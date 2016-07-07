"""Import tasks for the Catalina Real-Time Transient Survey.
"""
import os
import re
import urllib

from bs4 import BeautifulSoup

from astrocats.catalog.utils import is_number, pbar
from cdecimal import Decimal


def do_crts(catalog):
    crtsnameerrors = ['2011ax']
    task_str = catalog.get_current_task_str()
    folders = ['catalina', 'MLS', 'SSS']
    for fold in pbar(folders, task_str):
        html = catalog.load_cached_url(
            'http://nesssi.cacr.caltech.edu/' + fold + '/AllSN.html',
            os.path.join(catalog.get_current_task_repo(), 'CRTS', fold +
                         '.html'))
        if not html:
            continue
        bs = BeautifulSoup(html, 'html5lib')
        trs = bs.findAll('tr')
        for tri, tr in enumerate(pbar(trs, task_str)):
            tds = tr.findAll('td')
            if not tds:
                continue
            # refs = []
            aliases = []
            crtsname = ''
            ra = ''
            dec = ''
            lclink = ''
            # ttype = ''
            # ctype = ''
            for tdi, td in enumerate(tds):
                if tdi == 0:
                    crtsname = td.contents[0].text.strip()
                elif tdi == 1:
                    ra = td.contents[0]
                elif tdi == 2:
                    dec = td.contents[0]
                elif tdi == 11:
                    lclink = td.find('a')['onclick']
                    lclink = lclink.split("'")[1]
                elif tdi == 13:
                    aliases = re.sub('[()]', '', re.sub(
                        '<[^<]+?>', '', td.contents[-1].strip()))
                    aliases = [xx.strip('; ') for xx in list(
                        filter(None, aliases.split(' ')))]

            name = ''
            hostmag = ''
            hostupper = False
            validaliases = []
            for ai, alias in enumerate(aliases):
                if alias in ['SN', 'SDSS']:
                    continue
                if alias in crtsnameerrors:
                    continue
                if alias == 'mag':
                    if ai < len(aliases) - 1:
                        ind = ai + 1
                        if aliases[ai + 1] in ['SDSS']:
                            ind = ai + 2
                        elif aliases[ai + 1] in ['gal', 'obj', 'object',
                                                 'source']:
                            ind = ai - 1
                        if '>' in aliases[ind]:
                            hostupper = True
                        hostmag = aliases[ind].strip('>~').replace(
                            ',', '.').replace('m', '.')
                    continue
                if (is_number(alias[:4]) and alias[:2] == '20' and
                        len(alias) > 4):
                    name = 'SN' + alias
                if ((('asassn' in alias and len(alias) > 6) or
                     ('ptf' in alias and len(alias) > 3) or
                     ('ps1' in alias and len(alias) > 3) or
                     'snhunt' in alias or
                     ('mls' in alias and len(alias) > 3) or
                     'gaia' in alias or
                     ('lsq' in alias and len(alias) > 3))):
                    alias = alias.replace('SNHunt', 'SNhunt')
                    validaliases.append(alias)

            if not name:
                name = crtsname
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_source(
                name='Catalina Sky Survey', bibcode='2009ApJ...696..870D',
                url='http://nesssi.cacr.caltech.edu/catalina/AllSN.html')
            catalog.entries[name].add_quantity('alias', name, source)
            for alias in validaliases:
                catalog.entries[name].add_quantity('alias', alias, source)
            catalog.entries[name].add_quantity(
                'ra', ra, source, unit='floatdegrees')
            catalog.entries[name].add_quantity(
                'dec', dec, source, unit='floatdegrees')

            if hostmag:
                # 1.0 magnitude error based on Drake 2009 assertion that SN are
                # only considered
                #    real if they are 2 mags brighter than host.
                (catalog.entries[name]
                 .add_photometry(band='C', magnitude=hostmag,
                                 e_magnitude=1.0, source=source,
                                 host=True, telescope='Catalina Schmidt',
                                 upperlimit=hostupper))

            fname2 = (catalog.get_current_task_repo() + '/' + fold + '/' +
                      lclink.split('.')[-2].rstrip('p').split('/')[-1] +
                      '.html')
            if (catalog.current_task.load_archive(catalog.args) and
                    os.path.isfile(fname2)):
                with open(fname2, 'r') as ff:
                    html2 = ff.read()
            else:
                try:
                    with open(fname2, 'w') as ff:
                        response2 = urllib.request.urlopen(lclink)
                        html2 = response2.read().decode('utf-8')
                        ff.write(html2)
                except:
                    continue

            lines = html2.splitlines()
            teles = 'Catalina Schmidt'
            for line in lines:
                if 'javascript:showx' in line:
                    search = re.search("showx\('(.*?)'\)", line)
                    if not search:
                        continue
                    mjdstr = search.group(1).split('(')[0].strip()
                    if not is_number(mjdstr):
                        continue
                    mjd = str(Decimal(mjdstr) + Decimal(53249.0))
                else:
                    continue
                if 'javascript:showy' in line:
                    mag = re.search("showy\('(.*?)'\)", line).group(1)
                if 'javascript:showz' in line:
                    err = re.search("showz\('(.*?)'\)", line).group(1)
                if not is_number(mag) or (err and not is_number(err)):
                    continue
                e_mag = err if float(err) > 0.0 else ''
                upl = (float(err) == 0.0)
                (catalog.entries[name]
                 .add_photometry(time=mjd, band='C', magnitude=mag,
                                 source=source,
                                 includeshost=True, telescope=teles,
                                 e_magnitude=e_mag, upperlimit=upl))
            if catalog.args.update:
                catalog.journal_entries()

        if catalog.args.travis and tri > catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return
