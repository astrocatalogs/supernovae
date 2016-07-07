"""Import tasks for the Palomar Transient Factory (PTF).
"""
import os

import requests
from bs4 import BeautifulSoup

from astrocats.catalog.utils import is_number, pbar


def do_ptf(catalog):
    # response =
    # urllib.request.urlopen('http://wiserep.weizmann.ac.il/objects/list')
    # bs = BeautifulSoup(response, 'html5lib')
    # select = bs.find('select', {'name': 'objid'})
    # options = select.findAll('option')
    # for option in options:
    #    print(option.text)
    #    name = option.text
    #    if ((name.startswith('PTF') and is_number(name[3:5])) or
    #        name.startswith('PTFS') or name.startswith('iPTF')):
    # name = catalog.add_entry(name)
    task_str = catalog.get_current_task_str()

    if catalog.current_task.load_archive(catalog.args):
        with open(os.path.join(catalog.get_current_task_repo(),
                               'PTF/update.html'), 'r') as f:
            html = f.read()
    else:
        session = requests.Session()
        response = session.get('http://wiserep.weizmann.ac.il/spectra/update')
        html = response.text
        with open(os.path.join(catalog.get_current_task_repo(),
                               'PTF/update.html'), 'w') as f:
            f.write(html)

    bs = BeautifulSoup(html, 'html5lib')
    select = bs.find('select', {'name': 'objid'})
    options = select.findAll('option')
    for option in pbar(options, task_str):
        name = option.text
        if (((name.startswith('PTF') and is_number(name[3:5])) or
             name.startswith('PTFS') or name.startswith('iPTF'))):
            if '(' in name:
                alias = name.split('(')[0].strip(' ')
                name = name.split('(')[-1].strip(') ').replace('sn', 'SN')
                name = catalog.add_entry(name)
                source = catalog.entries[name].add_source(
                    bibcode='2012PASP..124..668Y')
                catalog.entries[name].add_quantity('alias', alias, source)
            else:
                # name = catalog.add_entry(name)
                name, source = catalog.new_entry(name,
                                                 bibcode='2012PASP..124..668Y')

    with open(os.path.join(
            catalog.get_current_task_repo(), 'PTF/old-ptf-events.csv')) as f:
        for suffix in pbar(f.read().splitlines(), task_str):
            name = catalog.add_entry('PTF' + suffix)
    with open(os.path.join(
            catalog.get_current_task_repo(), 'PTF/perly-2016.csv')) as f:
        for row in pbar(f.read().splitlines(), task_str):
            cols = [x.strip() for x in row.split(',')]
            alias = ''
            if cols[8]:
                name = cols[8]
                alias = 'PTF' + cols[0]
            else:
                name = 'PTF' + cols[0]
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_source(
                bibcode='2016arXiv160408207P')
            catalog.entries[name].add_quantity('alias', name, source)
            if alias:
                catalog.entries[name].add_quantity('alias', alias, source)
            catalog.entries[name].add_quantity('ra', cols[1], source)
            catalog.entries[name].add_quantity('dec', cols[2], source)
            catalog.entries[name].add_quantity(
                'claimedtype', 'SLSN-' + cols[3], source)
            catalog.entries[name].add_quantity(
                'redshift', cols[4], source, kind='spectroscopic')
            maxdate = cols[6].replace('-', '/')
            upl = maxdate.startswith('<')
            catalog.entries[name].add_quantity(
                'maxdate', maxdate.lstrip('<'), source, upperlimit=upl)
            catalog.entries[name].add_quantity(
                'ebv', cols[7], source, kind='spectroscopic')
            name = catalog.add_entry('PTF' + suffix)

    catalog.journal_entries()
    return
