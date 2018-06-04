"""Imported tasks for the Carnegie Supernova Program."""
import csv
import os
from decimal import Decimal
from glob import glob

from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import is_number, jd_to_mjd, pbar, pbar_strings
from astropy.time import Time as astrotime

from ..supernova import SUPERNOVA
from ..utils import clean_snname


def do_csp_photo(catalog):
    """Import CSP photometry."""
    import re
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'CSP/*.dat'))
    task_str = catalog.get_current_task_str()
    for fname in pbar_strings(file_names, task_str):
        tsvin = csv.reader(open(fname, 'r'), delimiter='\t',
                           skipinitialspace=True)
        eventname = os.path.basename(os.path.splitext(fname)[0])
        eventparts = eventname.split('opt+')
        name = clean_snname(eventparts[0])
        name = catalog.add_entry(name)

        reference = 'Carnegie Supernova Project'
        refbib = '2010AJ....139..519C'
        refurl = 'http://csp.obs.carnegiescience.edu/data'
        source = catalog.entries[name].add_source(
            bibcode=refbib, name=reference, url=refurl)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

        year = re.findall(r'\d+', name)[0]
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE, year, source)

        for r, row in enumerate(tsvin):
            if len(row) > 0 and row[0][0] == "#":
                if r == 2:
                    redz = row[0].split(' ')[-1]
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.REDSHIFT, redz, source, kind='cmb')
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.RA, row[1].split(' ')[-1], source)
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.DEC, row[2].split(' ')[-1], source)
                if 'MJD' in ''.join(row):
                    cspbands = list(filter(None, [
                        x.strip()
                        for x in ''.join(row).split('MJD')[-1].split('+/-')]))
                continue
            for v, val in enumerate(row):
                if v == 0:
                    mjd = val
                elif v % 2 != 0:
                    if float(row[v]) < 90.0:
                        catalog.entries[name].add_photometry(
                            time=mjd, u_time='MJD', observatory='LCO',
                            band=cspbands[(v - 1) // 2],
                            system='CSP', magnitude=row[v],
                            e_magnitude=row[v + 1], source=source)

    catalog.journal_entries()
    return


def do_csp_spectra(catalog):
    """Import CSP spectra."""
    oldname = ''
    task_str = catalog.get_current_task_str()
    file_names = glob(os.path.join(catalog.get_current_task_repo(), 'CSP/*'))
    for fi, fname in enumerate(pbar_strings(file_names, task_str)):
        filename = os.path.basename(fname)
        sfile = filename.split('.')
        if sfile[1] == 'txt':
            continue
        sfile = sfile[0]
        fileparts = sfile.split('_')
        name = 'SN20' + fileparts[0][2:]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        telescope = fileparts[-2]
        instrument = fileparts[-1]
        source = catalog.entries[name].add_source(
            bibcode='2013ApJ...773...53F')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

        data = csv.reader(open(fname, 'r'), delimiter=' ',
                          skipinitialspace=True)
        specdata = []
        for r, row in enumerate(data):
            if row[0] == '#JDate_of_observation:':
                jd = row[1].strip()
                time = str(jd_to_mjd(Decimal(jd)))
            elif row[0] == '#Redshift:':
                catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT,
                                                   row[1].strip(),
                                                   source)
            if r < 7:
                continue
            specdata.append(list(filter(None, [x.strip(' ') for x in row])))
        specdata = [list(i) for i in zip(*specdata)]
        wavelengths = specdata[0]
        fluxes = specdata[1]

        catalog.entries[name].add_spectrum(
            u_wavelengths='Angstrom', u_fluxes='erg/s/cm^2/Angstrom',
            u_time='MJD',
            time=time, wavelengths=wavelengths, fluxes=fluxes,
            telescope=telescope, instrument=instrument,
            source=source, deredshifted=True, filename=filename)
        if catalog.args.travis and fi >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return


def do_csp_fits_spectra(catalog):
    from astropy.io import fits

    fpath = catalog.get_current_task_repo()

    fureps = {'erg/cm2/s/A': 'erg/s/cm^2/Angstrom'}
    task_str = catalog.get_current_task_str()
    dirs = [x[0] for x in os.walk(
        os.path.join(fpath, 'Gutierrez_et_al_2017'))]
    files = []
    for dir in dirs:
        files.extend(glob(os.path.join(dir, '*.fits')))
    for datafile in pbar(files, task_str):
        filename = datafile.split('/')[-1]
        hdulist = fits.open(datafile)
        for oi, obj in enumerate(hdulist[0].header):
            if any(x in ['.', '/'] for x in obj):
                del (hdulist[0].header[oi])
        try:
            hdulist[0].verify('silentfix')
        except Exception as e:
            print(e)
        hdrkeys = list(hdulist[0].header.keys())
        # print(hdrkeys)
        name = datafile.split('/')[-2]
        if name[2] == '9':
            name = 'SN19' + name[2:]
        elif name != 'SN210':
            name = 'SN20' + name[2:]
        name, source = catalog.new_entry(name, bibcode='2017ApJ...850...89G')
        # for key in hdulist[0].header.keys():
        #     print(key, hdulist[0].header[key])
        if hdulist[0].header['SIMPLE']:
            if 'JD' in hdrkeys:
                mjd = str(jd_to_mjd(Decimal(str(hdulist[0].header['JD']))))
            elif 'MJD' in hdrkeys:
                mjd = str(hdulist[0].header['MJD'])
            elif 'DATE-OBS' in hdrkeys or 'DATE' in hdrkeys:
                dkey = 'DATE-OBS' if 'DATE-OBS' in hdrkeys else 'DATE'
                dval = hdulist[0].header[dkey]
                if is_number(dval):
                    dkey = 'DATE' if dkey == 'DATE-OBS' else 'DATE-OBS'
                    dval = hdulist[0].header[dkey]
                if 'T' in dval:
                    dateobs = dval.strip()
                elif 'UTC-OBS' in hdrkeys:
                    dateobs = dval.strip(
                    ) + 'T' + hdulist[0].header['UTC-OBS'].strip()
                mjd = str(astrotime(dateobs, format='isot').mjd)
            else:
                raise ValueError("Couldn't find JD/MJD for spectrum.")
            # print(hdulist[0].header)
            if 'CRVAL1' in hdulist[0].header:
                w0 = hdulist[0].header['CRVAL1']
            elif hdulist[0].header['CTYPE1'] == 'MULTISPE':
                w0 = float(hdulist[0].header['WAT2_001'].split(
                    '"')[-1].split()[3])
            else:
                raise ValueError('Unsupported spectrum format.')
            if hdulist[0].header['NAXIS'] == 1:
                wd = hdulist[0].header['CDELT1']
                fluxes = [str(x) for x in list(hdulist[0].data)]
                errors = False
            elif hdulist[0].header['NAXIS'] == 3:
                wd = hdulist[0].header['CD1_1']
                fluxes = [str(x) for x in list(hdulist[0].data)[0][0]]
                errors = [str(x) for x in list(hdulist[0].data)[-1][0]]
            else:
                print('Warning: Skipping FITS spectrum `{}`.'.format(filename))
                continue
            waves = [str(w0 + wd * x) for x in range(0, len(fluxes))]
        else:
            raise ValueError('Non-simple FITS import not yet supported.')
        if 'BUNIT' in hdrkeys:
            fluxunit = hdulist[0].header['BUNIT']
            if fluxunit in fureps:
                fluxunit = fureps[fluxunit]
        else:
            if max([float(x) for x in fluxes]) < 1.0e-5:
                fluxunit = 'erg/s/cm^2/Angstrom'
            else:
                fluxunit = 'Uncalibrated'
        specdict = {
            SPECTRUM.U_WAVELENGTHS: 'Angstrom',
            SPECTRUM.WAVELENGTHS: waves,
            SPECTRUM.TIME: mjd,
            SPECTRUM.U_TIME: 'MJD',
            SPECTRUM.FLUXES: fluxes,
            SPECTRUM.U_FLUXES: fluxunit,
            SPECTRUM.FILENAME: filename,
            SPECTRUM.SOURCE: source
        }
        if 'TELESCOP' in hdrkeys:
            specdict[SPECTRUM.TELESCOPE] = hdulist[0].header['TELESCOP']
        if 'INSTRUME' in hdrkeys:
            specdict[SPECTRUM.INSTRUMENT] = hdulist[0].header['INSTRUME']
        if 'AIRMASS' in hdrkeys:
            specdict[SPECTRUM.AIRMASS] = hdulist[0].header['AIRMASS']
        if errors:
            specdict[SPECTRUM.ERRORS] = errors
            specdict[SPECTRUM.U_ERRORS] = fluxunit
        if 'SITENAME' in hdrkeys:
            specdict[SPECTRUM.OBSERVATORY] = hdulist[0].header['SITENAME']
        elif 'OBSERVAT' in hdrkeys:
            specdict[SPECTRUM.OBSERVATORY] = hdulist[0].header['OBSERVAT']
        if 'OBSERVER' in hdrkeys:
            specdict[SPECTRUM.OBSERVER] = hdulist[0].header['OBSERVER']
        catalog.entries[name].add_spectrum(**specdict)
        hdulist.close()
        catalog.journal_entries()
    return
