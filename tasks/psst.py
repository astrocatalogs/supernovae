"""Import tasks for the Pan-STARRS Survey for Transients
"""
import csv
import os

from astropy.time import Time as astrotime

from astrocats.catalog.utils import make_date_string, pbar


def do_psst(catalog):
    task_str = catalog.get_current_task_str()
    # 2016arXiv160204156S
    file_path = os.path.join(
        catalog.get_current_task_repo(), '2016arXiv160204156S-tab1.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name,
             source) = catalog.new_entry(row[0],
                                         bibcode='2016arXiv160204156S')
            catalog.entries[name].add_quantity(
                'claimedtype', row[3].replace('SN', '').strip('() '), source)
            catalog.entries[name].add_quantity('redshift', row[5].strip(
                '() '), source, kind='spectroscopic')

    file_path = os.path.join(
        catalog.get_current_task_repo(), '2016arXiv160204156S-tab2.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name,
             source) = catalog.new_entry(row[0],
                                         bibcode='2016arXiv160204156S')
            catalog.entries[name].add_quantity('ra', row[1], source)
            catalog.entries[name].add_quantity('dec', row[2], source)
            mldt = astrotime(float(row[4]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.entries[name].add_quantity('discoverdate', discoverdate,
                                               source)

    catalog.journal_entries()

    # 1606.04795
    file_path = os.path.join(catalog.get_current_task_repo(), '1606.04795.tsv')
    with open(file_path, 'r') as f:
        data = list(csv.reader(f, delimiter='\t',
                               quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name,
             source) = catalog.new_entry(row[0],
                                         srcname='Smartt et al. 2016',
                                         url='http://arxiv.org/abs/1606.04795')
            catalog.entries[name].add_quantity('ra', row[1], source)
            catalog.entries[name].add_quantity('dec', row[2], source)
            mldt = astrotime(float(row[3]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.entries[name].add_quantity('discoverdate', discoverdate,
                                               source)
            catalog.entries[name].add_quantity('claimedtype', row[6], source)
            catalog.entries[name].add_quantity(
                'redshift', row[7], source, kind='spectroscopic')
            for alias in [x.strip() for x in row[8].split(',')]:
                catalog.entries[name].add_quantity('alias', alias, source)

    catalog.journal_entries()

    return
