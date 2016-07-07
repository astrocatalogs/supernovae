'''Import tasks for the Supernova Legacy Survey.
'''
import csv
import os
from glob import glob
from math import log10

from astropy.time import Time as astrotime
from astroquery.vizier import Vizier

from astrocats.catalog.utils import (get_sig_digits, pbar, pbar_strings,
                                     pretty_num)


def do_snls_photo(catalog):
    task_str = catalog.get_current_task_str()
    snls_path = os.path.join(catalog.get_current_task_repo(), 'SNLS-ugriz.dat')
    data = list(csv.reader(open(snls_path, 'r'), delimiter=' ',
                           quotechar='"', skipinitialspace=True))
    for row in pbar(data, task_str):
        flux = row[3]
        err = row[4]
        # Being extra strict here with the flux constraint, see note below.
        if float(flux) < 3.0 * float(err):
            continue
        name = 'SNLS-' + row[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010A&A...523A...7G')
        catalog.entries[name].add_quantity('alias', name, source)
        band = row[1]
        mjd = row[2]
        sig = get_sig_digits(flux.split('E')[0]) + 1
        # Conversion comes from SNLS-Readme
        # NOTE: Datafiles avail for download suggest diff zeropoints than 30,
        # need to inquire.
        magnitude = pretty_num(30.0 - 2.5 * log10(float(flux)), sig=sig)
        e_mag = pretty_num(
            2.5 * log10(1.0 + float(err) / float(flux)), sig=sig)
        # e_mag = pretty_num(2.5*(log10(float(flux) + float(err)) -
        # log10(float(flux))), sig=sig)
        catalog.entries[name].add_photometry(
            time=mjd, band=band, magnitude=magnitude, e_magnitude=e_mag,
            counts=flux, e_counts=err, source=source)

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
        catalog.entries[name].add_quantity('alias', name, source)

        catalog.entries[name].add_quantity(
            'discoverdate', '20' + fileparts[1][:2], source)

        f = open(fname, 'r')
        data = csv.reader(f, delimiter=' ', skipinitialspace=True)
        specdata = []
        for r, row in enumerate(data):
            if row[0] == '@TELESCOPE':
                telescope = row[1].strip()
            elif row[0] == '@REDSHIFT':
                catalog.entries[name].add_quantity(
                    'redshift', row[1].strip(), source)
            if r < 14:
                continue
            specdata.append(list(filter(None, [x.strip(' \t') for x in row])))
        specdata = [list(i) for i in zip(*specdata)]
        wavelengths = specdata[1]

        fluxes = [pretty_num(float(x) * 1.e-16, sig=get_sig_digits(x))
                  for x in specdata[2]]
        # FIX: this isnt being used
        # errors = [pretty_num(float(x)*1.e-16, sig=get_sig_digits(x)) for x in
        # specdata[3]]

        catalog.entries[name].add_spectrum(
            'Angstrom', 'erg/s/cm^2/Angstrom', wavelengths=wavelengths,
            fluxes=fluxes, u_time='MJD' if name in datedict else '',
            time=datedict[name] if name in datedict else '',
            telescope=telescope, source=source,
            filename=filename)
        if catalog.args.travis and fi >= catalog.TRAVIS_QUERY_LIMIT:
            break
    catalog.journal_entries()
    return
