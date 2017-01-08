# -*- coding: utf-8 -*-
"""General data import tasks.
"""
import os
from collections import OrderedDict
from glob import glob

from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import jd_to_mjd, pbar_strings
from astropy.io import fits
from astropy.time import Time as astrotime

from cdecimal import Decimal

from ..supernova import SUPERNOVA, Supernova


def do_external_radio(catalog):
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.txt')
    for datafile in pbar_strings(glob(path_pattern), task_str):
        oldname = os.path.basename(datafile).split('.')[0]
        name = catalog.add_entry(oldname)
        radiosourcedict = OrderedDict()
        with open(datafile, 'r') as ff:
            for li, line in enumerate(
                [xx.strip() for xx in ff.read().splitlines()]):
                if line.startswith('(') and li <= len(radiosourcedict):
                    key = line.split()[0]
                    bibc = line.split()[-1]
                    radiosourcedict[key] = catalog.entries[name].add_source(
                        bibcode=bibc)
                elif li in [xx + len(radiosourcedict) for xx in range(3)]:
                    continue
                else:
                    cols = list(filter(None, line.split()))
                    source = radiosourcedict[cols[6]]
                    if float(cols[4]) == 0.0:
                        eflux = ''
                        upp = True
                    else:
                        eflux = cols[4]
                        upp = False
                    catalog.entries[name].add_photometry(
                        time=cols[0],
                        frequency=cols[2],
                        u_frequency='GHz',
                        fluxdensity=cols[3],
                        e_fluxdensity=eflux,
                        u_fluxdensity='µJy',
                        upperlimit=upp,
                        u_time='MJD',
                        instrument=cols[5],
                        source=source)
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                                       oldname, source)

    catalog.journal_entries()
    return


def do_external_xray(catalog):
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.txt')
    for datafile in pbar_strings(glob(path_pattern), task_str):
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
                    catalog.entries[name].add_photometry(
                        time=cols[:2],
                        u_time='MJD',
                        energy=cols[2:4],
                        u_energy='keV',
                        counts=cols[4],
                        flux=cols[6],
                        unabsorbedflux=cols[8],
                        u_flux='ergs/ss/cm^2',
                        photonindex=cols[15],
                        instrument=cols[17],
                        nhmw=cols[11],
                        upperlimit=(float(cols[5]) < 0),
                        source=source)
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                                       oldname, source)

    catalog.journal_entries()
    return


def do_external_fits_spectra(catalog):
    fureps = {'erg/cm2/s/A': 'erg/s/cm^2/Angstrom'}
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.fits')
    files = glob(path_pattern)
    for datafile in files:
        hdulist = fits.open(datafile)
        filename = datafile.split('/')[-1]
        for oi, obj in enumerate(hdulist[0].header):
            if '.' in obj:
                del (hdulist[0].header[oi])
        hdulist[0].verify('silentfix')
        hdrkeys = list(hdulist[0].header.keys())
        # print(hdrkeys)
        name = hdulist[0].header['OBJECT']
        if 'OBSERVER' in hdrkeys:
            name, source = catalog.new_entry(
                name, srcname=hdulist[0].header['OBSERVER'])
        else:
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_self_source()
        # for key in hdulist[0].header.keys():
        #     print(key, hdulist[0].header[key])
        if hdulist[0].header['SIMPLE']:
            fluxes = [str(x) for x in list(hdulist[0].data)]
            if 'JD' in hdrkeys:
                mjd = str(jd_to_mjd(Decimal(str(hdulist[0].header['JD']))))
            elif 'MJD' in hdrkeys:
                mjd = str(hdulist[0].header['MJD'])
            elif 'DATE-OBS' in hdrkeys:
                if 'T' in hdulist[0].header['DATE-OBS']:
                    dateobs = hdulist[0].header['DATE-OBS'].strip()
                elif 'UTC-OBS' in hdrkeys:
                    dateobs = hdulist[0].header['DATE-OBS'].strip(
                    ) + 'T' + hdulist[0].header['UTC-OBS'].strip()
                mjd = str(astrotime(dateobs, format='isot').mjd)
            else:
                raise ValueError("Couldn't find JD/MJD for spectrum.")
            w0 = hdulist[0].header['CRVAL1']
            if 'CDELT1' in hdrkeys:
                wd = hdulist[0].header['CDELT1']
            else:
                print('Warning: Skipping FITS spectrum `{}`.'.format(filename))
                continue
            waves = [str(w0 + wd * x) for x in range(0, len(fluxes))]
        else:
            raise ValueError('Non-simple FITS import not yet supported.')
        tel = hdulist[0].header['TELESCOP']
        inst = hdulist[0].header['INSTRUME']
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
            SPECTRUM.TELESCOPE: tel,
            SPECTRUM.INSTRUMENT: inst,
            SPECTRUM.AIRMASS: airmass,
            SPECTRUM.FILENAME: filename,
            SPECTRUM.SOURCE: source
        }
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
    """Load events from files in the 'internal' repository, and save them.
    """
    task_str = catalog.get_current_task_str()
    path_pattern = os.path.join(catalog.get_current_task_repo(), '*.json')
    files = glob(path_pattern)
    catalog.log.debug("found {} files matching '{}'".format(
        len(files), path_pattern))
    for datafile in pbar_strings(files, task_str):
        new_event = Supernova.init_from_file(
            catalog, path=datafile, clean=True)
        catalog.entries.update({new_event[SUPERNOVA.NAME]: new_event})

    return
