"""Import tasks for the Catalina Real-Time Transient Survey."""
import os
import re

from astrocats.catalog.utils import is_number, pbar
from astrocats.catalog.photometry import PHOTOMETRY
from bs4 import BeautifulSoup

from decimal import Decimal

from ..supernova import SUPERNOVA


def do_crts(catalog):
    """Import data from the Catalina Real-Time Transient Survey."""
    crtsnameerrors = ['2011ax']
    task_str = catalog.get_current_task_str()
    folders = ['catalina', 'MLS', 'MLS', 'SSS']
    files = ['AllSN.html', 'AllSN.arch.html', 'CRTSII_SN.html', 'AllSN.html']
    for fi, fold in enumerate(pbar(folders, task_str)):
        html = catalog.load_url(
            'http://nesssi.cacr.caltech.edu/' + fold + '/' + files[fi],
            os.path.join(catalog.get_current_task_repo(), 'CRTS', fold + '-' +
                         files[fi]), archived_mode=('arch' in files[fi]))
        html = html.replace('<ahref=', '<a href=')
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
                elif tdi == (8 if files[fi] == 'CRTSII_SN.html' else 11):
                    lclink = td.find('a')['onclick']
                    lclink = lclink.split("'")[1]
                elif tdi == (10 if files[fi] == 'CRTSII_SN.html' else 13):
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
            name, source = catalog.new_entry(
                name, srcname='Catalina Sky Survey',
                bibcode='2009ApJ...696..870D',
                url='http://nesssi.cacr.caltech.edu/catalina/AllSN.html')
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            for alias in validaliases:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.ALIAS, alias, source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.RA, ra.strip(), source, u_value='floatdegrees')
            catalog.entries[name].add_quantity(
                SUPERNOVA.DEC, dec.strip(), source, u_value='floatdegrees')
            if SUPERNOVA.CLAIMED_TYPE not in catalog.entries[name]:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.CLAIMED_TYPE, 'Candidate', source)

            if hostmag:
                # 1.0 magnitude error based on Drake 2009 assertion that SN are
                # only considered
                #    real if they are 2 mags brighter than host.
                photodict = {
                    PHOTOMETRY.BAND: 'C',
                    PHOTOMETRY.MAGNITUDE: hostmag,
                    PHOTOMETRY.E_MAGNITUDE: '1.0',
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.HOST: True,
                    PHOTOMETRY.TELESCOPE: 'Catalina Schmidt',
                    PHOTOMETRY.UPPER_LIMIT: hostupper
                }
                catalog.entries[name].add_photometry(**photodict)

            fname2 = (catalog.get_current_task_repo() + '/' + fold + '/' +
                      lclink.split('.')[-2].rstrip('p').split('/')[-1] +
                      '.html')

            html2 = catalog.load_url(lclink, fname2)
            if not html2:
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
                mag = ''
                err = ''
                if 'javascript:showy' in line:
                    mag = re.search("showy\('(.*?)'\)", line).group(1)
                if 'javascript:showz' in line:
                    err = re.search("showz\('(.*?)'\)", line).group(1)
                if not is_number(mag) or (err and not is_number(err)):
                    continue
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.E_TIME: '0.125',  # 3 hr error
                    PHOTOMETRY.BAND: 'C',
                    PHOTOMETRY.MAGNITUDE: mag,
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.INCLUDES_HOST: True,
                    PHOTOMETRY.TELESCOPE: teles
                }
                if float(err) > 0.0:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = err
                if float(err) == 0.0:
                    photodict[PHOTOMETRY.UPPER_LIMIT] = True
                catalog.entries[name].add_photometry(**photodict)
            if catalog.args.update:
                catalog.journal_entries()

            if catalog.args.travis and tri > catalog.TRAVIS_QUERY_LIMIT:
                break

    catalog.journal_entries()
    return
