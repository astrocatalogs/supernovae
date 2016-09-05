"""Import tasks for the Supernova Hunt.
"""
import os
import re

from bs4 import BeautifulSoup

from astrocats.catalog.utils import pbar

from ..supernova import SUPERNOVA


def do_snhunt(catalog):
    task_str = catalog.get_current_task_str()
    snh_url = 'http://nesssi.cacr.caltech.edu/catalina/current.html'
    html = catalog.load_url(snh_url, os.path.join(
        catalog.get_current_task_repo(), 'SNhunt/current.html'))
    if not html:
        return
    text = html.splitlines()
    findtable = False
    for ri, row in enumerate(text):
        if 'Supernova Discoveries' in row:
            findtable = True
        if findtable and '<table' in row:
            tstart = ri + 1
        if findtable and '</table>' in row:
            tend = ri - 1
    tablestr = '<html><body><table>'
    for row in text[tstart:tend]:
        if row[:3] == 'tr>':
            tablestr = tablestr + '<tr>' + row[3:]
        else:
            tablestr = tablestr + row
    tablestr = tablestr + '</table></body></html>'
    bs = BeautifulSoup(tablestr, 'html5lib')
    trs = bs.find('table').findAll('tr')
    for tr in pbar(trs, task_str):
        cols = [str(xx.text) for xx in tr.findAll('td')]
        if not cols:
            continue
        name = re.sub(
            '<[^<]+?>', '',
            cols[4]).strip().replace(' ', '').replace('SNHunt', 'SNhunt')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            name='Supernova Hunt', url=snh_url)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        host = re.sub('<[^<]+?>', '', cols[1]).strip().replace('_', ' ')
        catalog.entries[name].add_quantity(SUPERNOVA.HOST, host, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, cols[2], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, cols[3], source, u_value='floatdegrees')
        dd = cols[0]
        discoverdate = dd[:4] + '/' + dd[4:6] + '/' + dd[6:8]
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           discoverdate, source)
        discoverers = cols[5].split('/')
        for discoverer in discoverers:
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER, 'CRTS',
                                               source)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER,
                                               discoverer, source)
        if catalog.args.update:
            catalog.journal_entries()

    catalog.journal_entries()
    return
