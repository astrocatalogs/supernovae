"""Import tasks for the Gamma-ray Bursts Catalog.
"""
import csv
import os

from astrocats.catalog.utils import pbar


def do_grb(catalog):
    task_str = catalog.get_current_task_str()
    file_path = os.path.join(
        catalog.get_current_task_repo(), 'GRB-catalog/catalog.csv')
    csvtxt = catalog.load_cached_url(
        'http://grb.pa.msu.edu/grbcatalog/'
        'download_data?cut_0_min=10&cut_0=BAT%20T90'
        '&cut_0_max=100000&num_cuts=1&no_date_cut=True',
        file_path)
    if not csvtxt:
        return
    data = list(csv.reader(csvtxt.splitlines(), delimiter=',',
                           quotechar='"', skipinitialspace=True))
    for r, row in enumerate(pbar(data, task_str)):
        if r == 0:
            continue
        (name,
         source) = catalog.new_entry('GRB ' +
                                     row[0],
                                     srcname='Gamma-ray Bursts Catalog',
                                     url='http://grbcatalog.org')
        catalog.entries[name].add_quantity(
            'ra', row[2], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row[3], source, unit='floatdegrees')
        catalog.entries[name].add_quantity('redshift', row[8], source)

    catalog.journal_entries()
    return
