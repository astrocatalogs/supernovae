"""Import tasks related to the Hubble pointings page.
"""
import json
import os

from astrocats.catalog.entry import ENTRY
from astrocats.catalog.utils import is_number, pbar
from astrocats.supernovae.utils import name_clean


def do_hst(catalog):
    task_str = catalog.get_current_task_str()
    url = 'http://archive.stsci.edu/hst/search.php'
    reference = 'Hubble Pointings'
    jtxt = catalog.load_url(
        url,
        os.path.join(catalog.get_current_task_repo(), 'HST.json'),
        post={
            'sci_target_descrip': '*supernova*',
            'outputformat': 'JSON_file',
            'action': 'Search',
            'max_records': '50000',
            'max_rpp': '50000'
        },
        verify=False)

    rows = json.loads(jtxt)

    allowed_prefixes = ('PS1', 'DES', 'GAIA', 'ASASSN', 'AT', 'IPTF', 'LSQ',
                        'PTF')
    loopcnt = 0
    for row in pbar(rows, task_str):
        oldname = name_clean(row['Target Name'])
        if not oldname.upper().startswith(allowed_prefixes):
            continue
        if oldname.startswith('PS1-') and not is_number(oldname[4]):
            continue
        name, source = catalog.new_entry(oldname, srcname=reference, url=url)
        if (ENTRY.RA in catalog.entries[name] and
                ENTRY.DEC in catalog.entries[name]):
            continue

        catalog.entries[name].add_quantity(
            ENTRY.RA, row['RA (J2000)'], source=source)
        catalog.entries[name].add_quantity(
            ENTRY.DEC, row['Dec (J2000)'], source=source)
        catalog.journal_entries()
        loopcnt = loopcnt + 1
        if (catalog.args.travis and loopcnt % catalog.TRAVIS_QUERY_LIMIT == 0):
            break
    catalog.journal_entries()

    return
