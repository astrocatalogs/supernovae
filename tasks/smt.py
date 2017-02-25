"""Import tasks for the Supernova Hunt.
"""
import os

from astrocats.catalog.utils import pbar
from bs4 import BeautifulSoup

from ..supernova import SUPERNOVA


def do_smt(catalog):
    task_str = catalog.get_current_task_str()
    smt_url = 'http://www.mso.anu.edu.au/skymapper/smt/transients/tns/'
    html = catalog.load_url(smt_url,
                            os.path.join(catalog.get_current_task_repo(),
                                         'SMT', 'index.html'))
    if not html:
        return
    bs = BeautifulSoup(html, 'html5lib')
    trs = bs.find('table').findAll('tr')
    for tr in pbar(trs, task_str):
        cols = [str(xx.text) for xx in tr.findAll('td')]
        if not cols:
            continue
        name = 'AT' + cols[0]
        name, source = catalog.new_entry(name, srcname='SMT', url=smt_url)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, cols[1], source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, cols[2],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, cols[3], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, cols[4], source, u_value='floatdegrees')
        if catalog.args.update:
            catalog.journal_entries()

    catalog.journal_entries()
    return
