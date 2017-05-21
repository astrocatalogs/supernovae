"""Import tasks for SNaX."""
import os

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import jd_to_mjd, make_date_string, pbar, uniq_cdl
from astropy.time import Time as astrotime

from decimal import Decimal

from ..supernova import SUPERNOVA


def do_snax(catalog):
    """Import from the SNaX X-ray database."""
    task_str = catalog.get_current_task_str()

    dlurl = 'http://kronos.uchicago.edu/snax/export.php?exportType=TSV&exportFields=standard&objid=&name=&typeid=&type=&galaxyid=&galaxy=&fluxMin=&fluxMax=&fluxEnergyLMin=&fluxEnergyLMax=&fluxEnergyHMin=&fluxEnergyHMax=&lumMin=&lumMax=&instrumentid=&instrument=&ageMin=&ageMax=&dateMin=&dateMax=&sortA=dateExploded'  # noqa: E501

    file_path = os.path.join(catalog.get_current_task_repo(), 'SNaX.TSV')

    tsv = catalog.load_url(dlurl, file_path)
    # csvtxt = catalog.load_url(
    #     'http://www.grbcatalog.org/'
    #     'download_data?cut_0_min=5&cut_0=BAT%20T90'
    #     '&cut_0_max=100000&num_cuts=1&no_date_cut=True',
    #     file_path)

    data = [x.split('\t') for x in tsv.split('\n')]

    for r, row in enumerate(pbar(data, task_str)):
        if r == 0 or not row[0]:
            continue
        (name, source) = catalog.new_entry(
            row[0], srcname='SNaX', url='http://kronos.uchicago.edu/snax/',
            secondary=True)
        sources = [source]
        expsrc = uniq_cdl(sources + [
            catalog.entries[name].add_source(bibcode=row[-6].strip())
        ])
        coosrc = uniq_cdl(sources + [
            catalog.entries[name].add_source(bibcode=row[-5].strip())
        ])
        dissrc = uniq_cdl(sources + [
            catalog.entries[name].add_source(bibcode=row[-4].strip())
        ])
        flxsrc = uniq_cdl(sources + [
            catalog.entries[name].add_source(bibcode=row[-3].strip()),
            catalog.entries[name].add_source(bibcode=row[-2].strip())
        ])

        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row[1],
                                           source)
        date = astrotime(float(row[2]), format='jd').datetime
        catalog.entries[name].add_quantity(
            SUPERNOVA.EXPLOSION_DATE,
            make_date_string(date.year, date.month, date.day), expsrc)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, ' '.join(row[3].split()[:3]), coosrc)
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, ' '.join(row[3].split()[:3]), coosrc)
        catalog.entries[name].add_quantity(SUPERNOVA.LUM_DIST, row[4], dissrc)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST, row[5], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row[6],
            source,
            e_value=row[7] if (row[7] and float(row[7]) != 0.0) else '')
        photodict = {
            PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[8])),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.ENERGY: row[15:17],
            PHOTOMETRY.U_ENERGY: 'keV',
            PHOTOMETRY.FLUX: str(Decimal('1.0e-13') * Decimal(row[11])),
            PHOTOMETRY.U_FLUX: 'ergs/s/cm^2',
            PHOTOMETRY.E_LOWER_FLUX:
            str(Decimal('1.0e-13') * Decimal(row[13])),
            PHOTOMETRY.E_UPPER_FLUX:
            str(Decimal('1.0e-13') * Decimal(row[14])),
            PHOTOMETRY.INSTRUMENT: row[9],
            PHOTOMETRY.SOURCE: flxsrc
        }
        if row[12] == '1':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return
