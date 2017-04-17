'''Import tasks for the Supernova Legacy Survey.
'''
import csv
import os
from glob import glob

from astropy.time import Time as astrotime
from astroquery.vizier import Vizier

from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import (get_sig_digits, pbar, pbar_strings,
                                     pretty_num)

from ..supernova import SUPERNOVA


def do_snls_photo(catalog):
    task_str = catalog.get_current_task_str()
    snls_path = os.path.join(catalog.get_current_task_repo(), 'SNLS-ugriz.dat')
    data = list(
        csv.reader(
            open(snls_path, 'r'),
            delimiter=' ',
            quotechar='"',
            skipinitialspace=True))
    for row in pbar(data, task_str):
        counts = row[3]
        err = row[4]
        name = 'SNLS-' + row[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010A&A...523A...7G')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        # Conversion comes from SNLS-Readme
        # NOTE: Datafiles avail for download suggest diff zeropoints than 30,
        # but README states mags should be calculated assuming 30. Need to
        # inquire.
        zp = 30.0
        photodict = {
            PHOTOMETRY.TIME: row[2],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[1],
            PHOTOMETRY.COUNT_RATE: counts,
            PHOTOMETRY.E_COUNT_RATE: err,
            PHOTOMETRY.ZERO_POINT: str(zp),
            PHOTOMETRY.SOURCE: source,
            PHOTOMETRY.TELESCOPE: 'CFHT',
            PHOTOMETRY.INSTRUMENT: 'MegaCam',
            PHOTOMETRY.BAND_SET: 'MegaCam',
            PHOTOMETRY.SYSTEM: 'BD17'
        }
        set_pd_mag_from_counts(photodict, counts, ec=err, zp=zp)
        catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return


def do_snls_spectra(catalog):
    """
    """

    task_str = catalog.get_current_task_str()
    result = Vizier.get_catalogs('J/A+A/507/85/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    datedict = {}
    for row in table:
        datedict['SNLS-' + row['SN']] = str(astrotime(row['Date']).mjd)

    oldname = ''
    file_names = glob(os.path.join(catalog.get_current_task_repo(), 'SNLS/*'))
    for fi, fname in enumerate(pbar_strings(file_names, task_str)):
        filename = os.path.basename(fname)
        fileparts = filename.split('_')
        name = 'SNLS-' + fileparts[1]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2009A&A...507...85B')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + fileparts[1][:2], source)

        f = open(fname, 'r')
        data = csv.reader(f, delimiter=' ', skipinitialspace=True)
        specdata = []
        for r, row in enumerate(data):
            if row[0] == '@TELESCOPE':
                telescope = row[1].strip()
            elif row[0] == '@REDSHIFT':
                catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT,
                                                   row[1].strip(), source)
            if r < 14:
                continue
            specdata.append(list(filter(None, [x.strip(' \t') for x in row])))
        specdata = [list(i) for i in zip(*specdata)]
        wavelengths = specdata[1]

        fluxes = [
            pretty_num(
                float(x) * 1.e-16, sig=get_sig_digits(x)) for x in specdata[2]
        ]
        # FIX: this isnt being used
        errors = [
            pretty_num(
                float(x) * 1.e-16, sig=get_sig_digits(x)) for x in specdata[3]
        ]

        fluxunit = 'erg/s/cm^2/Angstrom'

        specdict = {
            SPECTRUM.WAVELENGTHS: wavelengths,
            SPECTRUM.FLUXES: fluxes,
            SPECTRUM.ERRORS: errors,
            SPECTRUM.U_WAVELENGTHS: 'Angstrom',
            SPECTRUM.U_FLUXES: fluxunit,
            SPECTRUM.U_ERRORS: fluxunit,
            SPECTRUM.TELESCOPE: telescope,
            SPECTRUM.FILENAME: filename,
            SPECTRUM.SOURCE: source
        }
        if name in datedict:
            specdict[SPECTRUM.TIME] = datedict[name]
            specdict[SPECTRUM.U_TIME] = 'MJD'
        catalog.entries[name].add_spectrum(**specdict)
        if catalog.args.travis and fi >= catalog.TRAVIS_QUERY_LIMIT:
            break
    catalog.journal_entries()
    return
