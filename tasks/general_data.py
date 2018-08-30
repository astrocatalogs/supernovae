# -*- coding: utf-8 -*-
"""General data import tasks."""
import json
import os
from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal
from glob import glob

from astrocats.structures.struct import PHOTOMETRY
from astrocats.structures.struct import SPECTRUM
from astrocats import utils
from astropy.io import fits
from astropy.time import Time as astrotime

from ..supernova import SUPERNOVA, Supernova


def do_external_radio(catalog):
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.txt')
    for datafile in utils.pbar(glob(path_pattern), task_str, sort=True):
        oldname = os.path.basename(datafile).split('.')[0]
        name = catalog.add_entry(oldname)
        radiosourcedict = OrderedDict()
        with open(datafile, 'r') as ff:
            for li, line in enumerate(
                    [xx.strip() for xx in ff.read().splitlines()]):
                if line.startswith('(') and li <= len(radiosourcedict):
                    key = line.split()[0]
                    bibc = line.split()[-1]
                    radiosourcedict[key] = catalog.entries[name].add_source(bibcode=bibc)
                elif li in [xx + len(radiosourcedict) for xx in range(3)]:
                    continue
                else:
                    cols = list(filter(None, line.split()))
                    source = radiosourcedict[cols[6]]
                    photo = {
                        PHOTOMETRY.TIME: cols[0],
                        PHOTOMETRY.FREQUENCY: cols[2],
                        PHOTOMETRY.U_FREQUENCY: 'GHz',
                        PHOTOMETRY.FLUX_DENSITY: cols[3],
                        PHOTOMETRY.U_FLUX_DENSITY: 'µJy',
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.INSTRUMENT: cols[5],
                        PHOTOMETRY.SOURCE: source
                    }
                    if float(cols[4]) == 0.0:
                        eflux = None
                        upp = True
                    else:
                        eflux = cols[4]
                        upp = False

                    if eflux is not None:
                        photo[PHOTOMETRY.E_FLUX_DENSITY] = eflux

                    photo[PHOTOMETRY.UPPER_LIMIT] = upp

                    catalog.entries[name].add_photometry(**photo)
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname, source)

    catalog.journal_entries()
    return


def do_external_xray(catalog):
    """Import supernova X-ray data."""
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.txt')
    for datafile in utils.pbar(glob(path_pattern), task_str, sort=True):
        oldname = os.path.basename(datafile).split('.')[0]
        name = catalog.add_entry(oldname)
        with open(datafile, 'r') as ff:
            for li, line in enumerate(ff.read().splitlines()):
                if li == 0:
                    source = catalog.entries[name].add_source(
                        bibcode=line.split()[-1])
                elif li in [1, 2, 3]:
                    continue
                else:
                    cols = list(filter(None, line.split()))
                    photodict = {
                        PHOTOMETRY.TIME: cols[:2],
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.ENERGY: cols[2:4],
                        PHOTOMETRY.U_ENERGY: 'keV',
                        PHOTOMETRY.COUNT_RATE: cols[4],
                        PHOTOMETRY.FLUX: cols[6],
                        PHOTOMETRY.UNABSORBED_FLUX: cols[8],
                        PHOTOMETRY.U_FLUX: 'ergs/s/cm^2',
                        PHOTOMETRY.PHOTON_INDEX: cols[15],
                        PHOTOMETRY.INSTRUMENT: cols[17],
                        PHOTOMETRY.NHMW: cols[11],
                        PHOTOMETRY.UPPER_LIMIT: (float(cols[5]) < 0),
                        PHOTOMETRY.SOURCE: source
                    }
                    catalog.entries[name].add_photometry(**photodict)
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                                       oldname, source)

    catalog.journal_entries()
    return


def do_external_fits_spectra(catalog):
    fpath = catalog.get_current_task_repo()
    with open(os.path.join(fpath, 'meta.json'), 'r') as f:
        metadict = json.loads(f.read())

    fureps = {'erg/cm2/s/A': 'erg/s/cm^2/Angstrom'}
    # task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.fits')
    files = glob(path_pattern)
    for datafile in files:
        filename = datafile.split('/')[-1]
        if filename == 'meta.json':
            continue
        hdulist = fits.open(datafile)
        for oi, obj in enumerate(hdulist[0].header):
            if any(x in ['.', '/'] for x in obj):
                del hdulist[0].header[oi]
        hdulist[0].verify('silentfix')
        hdrkeys = list(hdulist[0].header.keys())
        # print(hdrkeys)
        name = None
        if filename in metadict:
            if 'name' in metadict[filename]:
                name = metadict[filename]['name']
        if name is None:
            name = hdulist[0].header['OBJECT']
        if 'bibcode' in metadict[filename]:
            name, source = catalog.new_entry(name, bibcode=metadict[filename]['bibcode'])
        elif 'donator' in metadict[filename]:
            name, source = catalog.new_entry(name, srcname=metadict[filename]['donator'])
        else:
            if 'OBSERVER' in hdrkeys:
                name, source = catalog.new_entry(name, srcname=hdulist[0].header['OBSERVER'])
            else:
                name = catalog.add_entry(name)
                source = catalog.entries[name].add_self_source()
        # for key in hdulist[0].header.keys():
        #     print(key, hdulist[0].header[key])
        if hdulist[0].header['SIMPLE']:
            if 'JD' in hdrkeys:
                mjd = str(utils.jd_to_mjd(Decimal(str(hdulist[0].header['JD']))))
            elif 'MJD' in hdrkeys:
                mjd = str(hdulist[0].header['MJD'])
            elif 'DATE-OBS' in hdrkeys:
                if 'T' in hdulist[0].header['DATE-OBS']:
                    dateobs = hdulist[0].header['DATE-OBS'].strip()
                elif 'UTC-OBS' in hdrkeys:
                    dateobs = (hdulist[0].header['DATE-OBS'].strip() + 'T' +
                               hdulist[0].header['UTC-OBS'].strip())
                mjd = str(astrotime(dateobs, format='isot').mjd)
            else:
                raise ValueError("Couldn't find JD/MJD for spectrum.")
            w0 = hdulist[0].header['CRVAL1']
            if hdulist[0].header['NAXIS'] == 1:
                wd = hdulist[0].header['CDELT1']
                fluxes = [str(x) for x in list(hdulist[0].data)]
                errors = False
            elif hdulist[0].header['NAXIS'] == 3:
                wd = hdulist[0].header['CD1_1']
                fluxes = [str(x) for x in list(hdulist[0].data)[0][0]]
                errors = [str(x) for x in list(hdulist[0].data)[3][0]]
            else:
                print('Warning: Skipping FITS spectrum `{}`.'.format(filename))
                continue
            waves = [str(w0 + wd * x) for x in range(0, len(fluxes))]
        else:
            raise ValueError('Non-simple FITS import not yet supported.')
        airmass = hdulist[0].header['AIRMASS']
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
            SPECTRUM.AIRMASS: airmass,
            SPECTRUM.FILENAME: filename,
            SPECTRUM.SOURCE: source
        }
        if 'TELESCOP' in hdrkeys:
            specdict[SPECTRUM.TELESCOPE] = hdulist[0].header['TELESCOP']
        if 'INSTRUME' in hdrkeys:
            specdict[SPECTRUM.INSTRUMENT] = hdulist[0].header['INSTRUME']
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


def do_internal(catalog):
    """Load events from files in the 'internal' repository, and save them."""
    log = catalog.log
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.json')
    files = glob(path_pattern)
    catalog.log.debug("found {} files matching '{}'".format(len(files), path_pattern))
    for datafile in utils.pbar(files, task_str, sort=True):
        new_entry = Supernova.init_from_file(catalog, path=datafile, clean=True, merge=True)

        name = new_entry[SUPERNOVA.NAME]
        old_name = None

        for alias in new_entry.get_aliases():
            old_name = catalog.get_name_for_entry_or_alias(alias)
            if old_name is not None:
                try:
                    if catalog.entries[old_name]._stub:
                        catalog.add_entry(old_name)
                except KeyError as err:
                    log.error("Failed in datafile '{}'".format(datafile))
                    log.error("`new_entry` = '{}'".format(new_entry))
                    log.error("`name` = '{}'".format(name))
                    log.error("`alias` = '{}'".format(alias))
                    log.error("`old_name` = '{}'".format(old_name))
                    try:
                        print(catalog.entries[alias])
                    except KeyError:
                        print("COULD NOT LOAD `entries[{}]`".format(alias))
                        try:
                            print(catalog.entries[name])
                        except KeyError:
                            print("COULD NOT LOAD `entries[{}]`".format(name))

                    raise

                break

        if old_name:
            old_entry = deepcopy(catalog.entries[old_name])
            catalog.copy_entry_to_entry(new_entry, old_entry)
            catalog.entries[old_name] = old_entry
        else:
            catalog.entries[name] = new_entry

        catalog.journal_entries()

    return
