"""Import tasks related to the Asiago supernova catalog and spectroscopic
follow-up programs.
"""
import datetime
import os

# from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from astrocats.catalog.utils import pbar, utf8
from astrocats.supernovae.supernova import SUPERNOVA
from astrocats.supernovae.utils import name_clean


def do_swift(catalog):
    task_str = catalog.get_current_task_str()
    now = datetime.datetime.now()
    url = 'https://www.swift.psu.edu/secure/toop/summary.php'
    reference = 'Swift TOOs'
    years = range(2005, int(now.year) + 1)
    for year in years:
        print(year)
        archived = True if year < years[-1] - 1 else False
        html = catalog.load_url(
            url,
            os.path.join(catalog.get_current_task_repo(),
                         'Swift/' + str(year) + '.html'),
            post={'year': str(year)},
            archived_mode=archived,
            verify=False)
        if not html:
            continue

        soup = BeautifulSoup(html, 'html5lib')
        table = soup.findAll('table')[2]

        records = []
        for r, row in enumerate(table.findAll('tr')):
            if r == 0:
                continue
            col = row.findAll('td')
            records.append([utf8(x.renderContents()) for x in col])

        for record in pbar(records, task_str):
            if len(record) > 1 and record[0] != '':
                oldname = name_clean(record[0])
                radeg = record[1]
                decdeg = record[2]

                if not catalog.entry_exists(oldname):
                    continue
                if float(radeg) == 0.0 and float(decdeg) == 0.0:
                    continue

                name = catalog.add_entry(oldname)
                if (SUPERNOVA.RA in catalog.entries[name] and
                        SUPERNOVA.DEC in catalog.entries[name]):
                    catalog.journal_entries()
                    continue
                source = catalog.entries[name].add_source(
                    srcname=reference, url=url)

                catalog.entries[name].add_quantity(
                    SUPERNOVA.RA, radeg, u_value='floatdegrees', source=source)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.DEC,
                    decdeg,
                    u_value='floatdegrees',
                    source=source)
                catalog.journal_entries()
    catalog.journal_entries()

    return
