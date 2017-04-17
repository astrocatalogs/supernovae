"""Import tasks for the SIMBAD astrophysical database.
"""
import re

from astroquery.simbad import Simbad

from astrocats.catalog.utils import is_number, pbar, single_spaces, uniq_cdl
from ..supernova import SUPERNOVA
from ..utils import name_clean


def do_simbad(catalog):
    # Simbad.list_votable_fields()
    # Some coordinates that SIMBAD claims belong to the SNe actually belong to
    # the host.
    task_str = catalog.get_current_task_str()
    simbadmirrors = ['http://simbad.harvard.edu/simbad/sim-script',
                     'http://simbad.u-strasbg.fr/simbad/sim-script']
    simbadbadcoordbib = ['2013ApJ...770..107C']
    simbadbadtypebib = ['2014ApJ...796...87I', '2015MNRAS.448.1206M',
                        '2015ApJ...807L..18N']
    simbadbadnamebib = ['2004AJ....127.2809W', '2005MNRAS.364.1419Z',
                        '2015A&A...574A.112D', '2011MNRAS.417..916G',
                        '2002ApJ...566..880G']
    simbadbannedcats = ['[TBV2008]', 'OGLE-MBR']
    simbadbannednames = ['SN']
    customSimbad = Simbad()
    customSimbad.ROW_LIMIT = -1
    customSimbad.TIMEOUT = 120
    customSimbad.add_votable_fields('otype', 'sptype', 'sp_bibcode', 'id')
    table = []
    print(customSimbad.SIMBAD_URL)
    for mirror in simbadmirrors:
        customSimbad.SIMBAD_URL = mirror
        try:
            table = customSimbad.query_criteria('maintype=SN | maintype="SN?"')
        except Exception:
            continue
        else:
            if not table:
                continue
            break

    if not table:
        catalog.log.warning('SIMBAD unable to load, probably offline.')

    # 2000A&AS..143....9W
    for brow in pbar(table, task_str):
        row = {x: re.sub(r'b\'(.*)\'', r'\1',
                         str(brow[x])) for x in brow.colnames}
        # Skip items with no bibliographic info aside from SIMBAD, too
        # error-prone
        if row['OTYPE'] == 'Candidate_SN*' and not row['SP_TYPE']:
            continue
        if (not row['COO_BIBCODE'] and not row['SP_BIBCODE'] and
                not row['SP_BIBCODE_2']):
            continue
        if any([x in row['MAIN_ID'] for x in simbadbannedcats]):
            continue
        if row['COO_BIBCODE'] and row['COO_BIBCODE'] in simbadbadnamebib:
            continue
        name = single_spaces(re.sub(r'\[[^)]*\]', '', row['MAIN_ID']).strip())
        if name in simbadbannednames:
            continue
        if is_number(name.replace(' ', '')):
            continue
        name = catalog.add_entry(name)
        source = (catalog.entries[name]
                  .add_source(name='SIMBAD astronomical database',
                              bibcode="2000A&AS..143....9W",
                              url="http://simbad.u-strasbg.fr/",
                              secondary=True))
        aliases = row['ID'].split(',')
        for alias in aliases:
            if any([x in alias for x in simbadbannedcats]):
                continue
            ali = single_spaces(re.sub(r'\[[^)]*\]', '', alias).strip())
            if is_number(ali.replace(' ', '')):
                continue
            if ali in simbadbannednames:
                continue
            ali = name_clean(ali)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                               ali, source)
        if row['COO_BIBCODE'] and row['COO_BIBCODE'] not in simbadbadcoordbib:
            csources = ','.join(
                [source, catalog.entries[name].add_source(
                    bibcode=row['COO_BIBCODE'])])
            catalog.entries[name].add_quantity(SUPERNOVA.RA,
                                               row['RA'], csources)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC,
                                               row['DEC'], csources)
        if row['SP_BIBCODE'] and row['SP_BIBCODE'] not in simbadbadtypebib:
            ssources = uniq_cdl([source,
                                 catalog.entries[name]
                                 .add_source(bibcode=row['SP_BIBCODE'])] +
                                ([catalog.entries[name]
                                  .add_source(bibcode=row['SP_BIBCODE_2'])] if
                                 row['SP_BIBCODE_2'] else []))
            catalog.entries[name].add_quantity(
                SUPERNOVA.CLAIMED_TYPE,
                (row['SP_TYPE']
                 .replace('SN.', '')
                 .replace('SN', '')
                 .replace('(~)', '')
                 .strip(': ')), ssources)
    catalog.journal_entries()
    return
