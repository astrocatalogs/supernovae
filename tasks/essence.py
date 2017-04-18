'''Import tasks for ESSENCE.
'''
import csv
import datetime
import os
from glob import glob

from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import is_number, pbar, pbar_strings
from astropy.time import Time as astrotime

from decimal import Decimal

from ..supernova import SUPERNOVA


def do_essence_photo(catalog):
    task_str = catalog.get_current_task_str()
    ess_path = os.path.join(catalog.get_current_task_repo(), 'ESSENCE',
                            'obj_table.dat')
    data = list(
        csv.reader(
            open(ess_path, 'r'),
            delimiter=' ',
            quotechar='"',
            skipinitialspace=True))
    for row in pbar(data[1:], task_str):
        etype = row[2]
        if etype.upper().replace('?', '') in catalog.nonsnetypes:
            continue
        ess_name = 'ESSENCE ' + row[0]
        name, source = catalog.new_entry(
            ess_name, bibcode='2016ApJS..224....3N')
        if row[1] != '---':
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, 'SN' + row[1],
                                               source)
        if etype != '---':
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, etype,
                                               source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[5], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[6], source)
        if is_number(row[11]):
            quantdict = {
                QUANTITY.VALUE: row[11],
                QUANTITY.SOURCE: source,
                QUANTITY.KIND: 'host'
            }
            if is_number(row[12]):
                quantdict[QUANTITY.E_VALUE] = row[12]
            catalog.entries[name].add_quantity(
                [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT], **quantdict)

    files = glob(
        os.path.join(catalog.get_current_task_repo(), 'ESSENCE',
                     '*clean*.dat'))

    for pfile in pbar(files, task_str):
        name = 'ESSENCE ' + pfile.split('/')[-1].split('.')[0]
        name, source = catalog.new_entry(name, bibcode='2016ApJS..224....3N')
        with open(pfile, 'r') as f:
            rows = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
        for ri, row in enumerate(rows):
            if ri == 1:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    row[5],
                    source,
                    kind=['spectroscopic', 'heliocentric'])
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    row[6],
                    source,
                    kind=['spectroscopic', 'cmb'])
                continue
            if row[0].startswith('#'):
                continue
            counts = row[3][:6]
            lerr = row[4][:6]
            uerr = row[5][:6]
            zp = 25.0
            photodict = {
                PHOTOMETRY.TIME: row[1],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: row[2][0],
                PHOTOMETRY.COUNT_RATE: counts,
                PHOTOMETRY.E_LOWER_COUNT_RATE: lerr,
                PHOTOMETRY.E_UPPER_COUNT_RATE: uerr,
                PHOTOMETRY.ZERO_POINT: str(zp),
                PHOTOMETRY.SOURCE: source,
                PHOTOMETRY.TELESCOPE: 'CTIO 4m',
                PHOTOMETRY.SYSTEM: 'Natural'
            }
            set_pd_mag_from_counts(
                photodict, counts, ec='', lec=lerr, uec=uerr, zp=zp)
            catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return


def do_essence_spectra(catalog):
    task_str = catalog.get_current_task_str()

    insdict = {
        "lris": "LRIS",
        "esi": "ESI",
        "deimos": "DEIMOS",
        "gmos": "GMOS",
        "fors1": "FORS1",
        "bluechannel": "Blue Channel",
        "ldss2": "LDSS-2",
        "ldss3": "LDSS-3",
        "imacs": "IMACS",
        "fast": "FAST"
    }

    teldict = {
        "lris": "Keck",
        "esi": "Keck",
        "deimos": "Keck",
        "gmos": "Gemini",
        "fors1": "VLT",
        "bluechannel": "MMT",
        "ldss2": "Magellan Clay & Baade",
        "ldss3": "Magellan Clay & Baade",
        "imacs": "Magellan Clay & Baade",
        "fast": "FLWO 1.5m"
    }

    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'ESSENCE', '*'))
    oldname = ''
    for fi, fname in enumerate(pbar_strings(file_names, task_str)):
        filename = os.path.basename(fname)
        fileparts = filename.split('_')
        name = 'ESSENCE ' + fileparts[0]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name

        if is_number(fileparts[1]):
            doffset = 1
        else:
            if fileparts[1] != 'comb':
                continue
            doffset = 2

        dstr = fileparts[doffset]
        mjd = str(
            astrotime(
                datetime.datetime(
                    year=int(dstr[:4]),
                    month=int(dstr[4:6]),
                    day=int(dstr[6:8])) + datetime.timedelta(days=float(dstr[
                        8:]))).mjd)

        instrument = fileparts[-1].split('.')[0]
        telescope = teldict.get(instrument, '')
        instrument = insdict.get(instrument, '')

        with open(fname, 'r') as f:
            data = csv.reader(f, delimiter=' ', skipinitialspace=True)
            data = [list(i) for i in zip(*data)]
            wavelengths = data[0]
            fluxes = [str(Decimal('1.0e-15') * Decimal(x)) for x in data[1]]

        name, source = catalog.new_entry(name, bibcode='2016ApJS..224....3N')

        specdict = {
            SPECTRUM.TIME: mjd,
            SPECTRUM.U_TIME: 'MJD',
            SPECTRUM.U_WAVELENGTHS: 'Angstrom',
            SPECTRUM.WAVELENGTHS: wavelengths,
            SPECTRUM.FLUXES: fluxes,
            SPECTRUM.U_FLUXES: 'erg/s/cm^2/Angstrom',
            SPECTRUM.FILENAME: filename,
            SPECTRUM.SOURCE: source
        }

        if instrument:
            specdict[SPECTRUM.INSTRUMENT] = instrument
        if telescope:
            specdict[SPECTRUM.TELESCOPE] = telescope

        catalog.entries[name].add_spectrum(**specdict)

        if catalog.args.travis and fi >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return
