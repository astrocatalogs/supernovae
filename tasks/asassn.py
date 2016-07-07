"""Tasks related to the ASASSN survey.
"""
import os
from bs4 import BeautifulSoup

from astrocats.catalog.utils import pbar


def do_asassn(catalog):
    task_str = catalog.get_current_task_str()
    asn_url = 'http://www.astronomy.ohio-state.edu/~assassin/sn_list.html'
    html = catalog.load_cached_url(asn_url, os.path.join(
        catalog.get_current_task_repo(), 'ASASSN/sn_list.html'))
    if not html:
        return
    bs = BeautifulSoup(html, 'html5lib')
    trs = bs.find('table').findAll('tr')
    for tri, tr in enumerate(pbar(trs, task_str)):
        name = ''
        ra = ''
        dec = ''
        redshift = ''
        hostoff = ''
        claimedtype = ''
        host = ''
        atellink = ''
        typelink = ''
        if tri == 0:
            continue
        tds = tr.findAll('td')
        for tdi, td in enumerate(tds):
            if tdi == 1:
                name = catalog.add_entry(td.text.strip())
                atellink = td.find('a')
                if atellink:
                    atellink = atellink['href']
                else:
                    atellink = ''
            if tdi == 2:
                discdate = td.text.replace('-', '/')
            if tdi == 3:
                ra = td.text
            if tdi == 4:
                dec = td.text
            if tdi == 5:
                redshift = td.text
            if tdi == 8:
                hostoff = td.text
            if tdi == 9:
                claimedtype = td.text
                typelink = td.find('a')
                if typelink:
                    typelink = typelink['href']
                else:
                    typelink = ''
            if tdi == 12:
                host = td.text

        sources = [catalog.entries[name].add_source(
            url=asn_url, name='ASAS-SN Supernovae')]
        typesources = sources[:]
        if atellink:
            sources.append(
                (catalog.entries[name]
                 .add_source(name='ATel ' +
                             atellink.split('=')[-1], url=atellink)))
        if typelink:
            typesources.append(
                (catalog.entries[name]
                 .add_source(name='ATel ' +
                             typelink.split('=')[-1], url=typelink)))
        sources = ','.join(sources)
        typesources = ','.join(typesources)
        catalog.entries[name].add_quantity('alias', name, sources)
        catalog.entries[name].add_quantity('discoverdate', discdate, sources)
        catalog.entries[name].add_quantity('ra', ra, sources,
                                           unit='floatdegrees')
        catalog.entries[name].add_quantity('dec', dec, sources,
                                           unit='floatdegrees')
        catalog.entries[name].add_quantity('redshift', redshift, sources)
        catalog.entries[name].add_quantity(
            'hostoffsetang', hostoff, sources, unit='arcseconds')
        for ct in claimedtype.split('/'):
            if ct != 'Unk':
                catalog.entries[name].add_quantity('claimedtype', ct,
                                                   typesources)
        if host != 'Uncatalogued':
            catalog.entries[name].add_quantity('host', host, sources)
    catalog.journal_entries()
    return
