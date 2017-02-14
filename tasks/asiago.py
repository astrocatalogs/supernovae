"""Import tasks related to the Asiago supernova catalog and spectroscopic
follow-up programs.
"""
import calendar
import os
import re
import urllib

from astrocats.catalog.utils import is_number, pbar, uniq_cdl, utf8
# from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from ..supernova import SUPERNOVA
from ..utils import clean_snname


def do_asiago_photo(catalog):
    task_str = catalog.get_current_task_str()
    # response = (urllib.request
    # .urlopen('http://graspa.oapd.inaf.it/cgi-bin/sncat.php'))
    path = os.path.abspath(
        os.path.join(catalog.get_current_task_repo(), 'asiago-cat.php'))
    response = urllib.request.urlopen('file://' + path)
    html = response.read().decode('utf-8')
    html = html.replace('\r', "")

    soup = BeautifulSoup(html, 'html5lib')
    table = soup.find('table')

    records = []
    for r, row in enumerate(table.findAll('tr')):
        if r == 0:
            continue
        col = row.findAll('td')
        records.append([utf8(x.renderContents()) for x in col])

    for ri, record in enumerate(pbar(records, task_str)):
        if len(record) > 1 and record[1] != '':
            oldname = clean_snname("SN" + record[1]).strip('?')

            reference = 'Asiago Supernova Catalogue'
            refurl = 'http://graspa.oapd.inaf.it/cgi-bin/sncat.php'
            refbib = '1989A&AS...81..421B'

            name, source = catalog.new_entry(
                oldname,
                srcname=reference,
                url=refurl,
                bibcode=refbib,
                secondary=True)

            year = re.findall(r'\d+', oldname)[0]
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, year,
                                               source)

            hostname = record[2]
            hostra = record[3]
            hostdec = record[4]
            ra = record[5].strip(':')
            dec = record[6].strip(':')
            redvel = record[11].strip(':')
            discoverer = record[19]

            datestring = year

            monthday = record[18]
            if "*" in monthday:
                datekey = SUPERNOVA.DISCOVER_DATE
            else:
                datekey = SUPERNOVA.MAX_DATE

            if monthday.strip() != '':
                monthstr = ''.join(re.findall('[a-zA-Z]+', monthday))
                monthstr = str(list(calendar.month_abbr).index(monthstr))
                datestring = datestring + '/' + monthstr

                dayarr = re.findall(r'\d+', monthday)
                if dayarr:
                    daystr = dayarr[0]
                    datestring = datestring + '/' + daystr

            catalog.entries[name].add_quantity(datekey, datestring, source)

            velocity = ''
            redshift = ''
            if redvel != '':
                if round(float(redvel)) == float(redvel):
                    velocity = int(redvel)
                else:
                    redshift = float(redvel)
                redshift = str(redshift)
                velocity = str(velocity)

            claimedtype = record[17].replace(':', '').replace('*', '').strip()

            if (hostname != ''):
                catalog.entries[name].add_quantity(SUPERNOVA.HOST, hostname,
                                                   source)
            if (claimedtype != ''):
                catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                   claimedtype, source)
            if (redshift != ''):
                catalog.entries[name].add_quantity(
                    [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                    redshift,
                    source,
                    kind='host')
            if (velocity != ''):
                catalog.entries[name].add_quantity(
                    [SUPERNOVA.VELOCITY, SUPERNOVA.HOST_VELOCITY],
                    velocity,
                    source,
                    kind='host')
            if (hostra != ''):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.HOST_RA, hostra, source, u_value='nospace')
            if (hostdec != ''):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.HOST_DEC, hostdec, source, u_value='nospace')
            if (ra != ''):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.RA, ra, source, u_value='nospace')
            if (dec != ''):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.DEC, dec, source, u_value='nospace')
            if (discoverer != ''):
                catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER,
                                                   discoverer, source)
        if catalog.args.travis and ri >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return


def do_asiago_spectra(catalog):
    task_str = catalog.get_current_task_str()
    html = catalog.load_url(('http://sngroup.oapd.inaf.it./'
                             'cgi-bin/output_class.cgi?sn=1990'),
                            os.path.join(catalog.get_current_task_repo(),
                                         'Asiago/spectra.html'))
    if not html:
        return

    bs = BeautifulSoup(html, 'html5lib')
    trs = bs.findAll('tr')
    for tr in pbar(trs, task_str):
        tds = tr.findAll('td')
        name = ''
        host = ''
        # fitsurl = ''
        source = ''
        reference = ''
        for tdi, td in enumerate(tds):
            if tdi == 0:
                butt = td.find('button')
                if not butt:
                    break
                alias = butt.text.strip()
                alias = alias.replace('PSNJ', 'PSN J').replace('GAIA', 'Gaia')
            elif tdi == 1:
                name = (td.text.strip().replace('PSNJ', 'PSN J')
                        .replace('GAIA', 'Gaia'))
                if name.startswith('SN '):
                    name = 'SN' + name[3:]
                if not name:
                    name = alias
                if is_number(name[:4]):
                    name = 'SN' + name
                oldname = name
                name = catalog.add_entry(name)
                reference = 'Asiago Supernova Catalogue'
                refurl = 'http://graspa.oapd.inaf.it/cgi-bin/sncat.php'
                secondarysource = catalog.entries[name].add_source(
                    name=reference, url=refurl, secondary=True)
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname,
                                                   secondarysource)
                if alias != name:
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, alias,
                                                       secondarysource)
            elif tdi == 2:
                host = td.text.strip()
                if host == 'anonymous':
                    host = ''
            elif tdi == 3:
                discoverer = td.text.strip()
            elif tdi == 5:
                ra = td.text.strip()
            elif tdi == 6:
                dec = td.text.strip()
            elif tdi == 7:
                claimedtype = td.text.strip()
            elif tdi == 8:
                redshift = td.text.strip()
            # elif tdi == 9:
            #     epochstr = td.text.strip()
            #     if epochstr:
            #         mjd = (astrotime(epochstr[:4] + '-' + epochstr[4:6] +
            #                '-' +
            #                str(floor(float(epochstr[6:]))).zfill(2)).mjd +
            #                float(epochstr[6:]) - floor(float(epochstr[6:])))
            #     else:
            #         mjd = ''
            elif tdi == 10:
                refs = td.findAll('a')
                source = ''
                reference = ''
                refurl = ''
                for ref in refs:
                    if ref.text != 'REF':
                        reference = ref.text
                        refurl = ref['href']
                if reference:
                    source = catalog.entries[name].add_source(
                        name=reference, url=refurl)
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name,
                                                   secondarysource)
                sources = uniq_cdl(
                    list(filter(None, [source, secondarysource])))
            elif tdi == 12:
                pass
                # fitslink = td.find('a')
                # if fitslink:
                #     fitsurl = fitslink['href']
        if name:
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                               claimedtype, sources)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, sources)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec, sources)
            catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, redshift,
                                               sources)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER,
                                               discoverer, sources)
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, host, sources)

            # if fitsurl:
            #    response = urllib.request.urlopen(
            #        'http://sngroup.oapd.inaf.it./' + fitsurl)
            #    compressed = io.BytesIO(response.read())
            #    decompressed = gzip.GzipFile(fileobj=compressed)
            #    hdulist = fits.open(decompressed)
            #    scidata = hdulist[0].data
            #    print(hdulist[0].header)
            #
            #    print(scidata[3])
            #    sys.exit()

    catalog.journal_entries()
    return
