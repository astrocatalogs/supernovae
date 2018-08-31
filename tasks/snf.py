"""Import tasks for the Nearby Supernova Factory.
"""
import csv
import os
from glob import glob

from astrocats.utils import jd_to_mjd, pbar, pretty_num, uniq_cdl
from astropy.time import Time as astrotime

from decimal import Decimal

from astrocats.structures.struct import SPECTRUM
from ..supernova import SUPERNOVA


def do_snf_aliases(catalog):
    file_path = os.path.join(catalog.get_current_task_repo(), 'SNF/snf-aliases.csv')
    with open(file_path, 'r') as f:
        for row in [x.split(',') for x in f.read().splitlines()]:
            name, source = catalog.new_entry(
                row[0], bibcode=catalog.OSC_BIBCODE, name=catalog.OSC_NAME,
                url=catalog.OSC_URL, secondary=True)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)

    catalog.journal_entries()
    return


def do_snf_spectra(catalog):
    task_str = catalog.get_current_task_str()
    bibcodes = {'SN2005gj': '2006ApJ...650..510A',
                'SN2006D': '2007ApJ...654L..53T',
                'SN2007if': '2010ApJ...713.1073S',
                'SN2011fe': '2013A&A...554A..27P'}
    oldname = ''
    snfcnt = 0
    eventfolders = next(os.walk(os.path.join(catalog.get_current_task_repo(), 'SNFactory')))[1]
    for eventfolder in pbar(eventfolders, task_str):
        name = eventfolder
        # Use existing name if already added
        _name = catalog.get_name_for_entry_or_alias(name)
        if _name is not None:
            name = _name
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        sec_reference = 'Nearby Supernova Factory'
        sec_refurl = 'http://snfactory.lbl.gov/'
        sec_bibcode = '2002SPIE.4836...61A'
        sec_source = catalog.entries[name].add_source(
            name=sec_reference, url=sec_refurl, bibcode=sec_bibcode, secondary=True)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, sec_source)
        bibcode = bibcodes[name]
        source = catalog.entries[name].add_source(bibcode=bibcode)
        sources = uniq_cdl([source, sec_source])
        use_path = os.path.join(catalog.get_current_task_repo(), 'SNFactory', eventfolder, '*.dat')
        eventspectra = glob(use_path)
        for spectrum in pbar(eventspectra, task_str):
            filename = os.path.basename(spectrum)
            with open(spectrum) as spec_file:
                specdata = list(csv.reader(spec_file, delimiter=' ', skipinitialspace=True))
            specdata = list(filter(None, specdata))
            newspec = []
            time = None
            telescope = None
            instrument = None
            observer = None
            observatory = None
            if 'Keck_20060202_R' in spectrum:
                time = '53768.23469'
            elif 'Spectrum05_276' in spectrum:
                time = pretty_num(astrotime('2005-10-03').mjd, sig=5)
            elif 'Spectrum05_329' in spectrum:
                time = pretty_num(astrotime('2005-11-25').mjd, sig=5)
            elif 'Spectrum05_336' in spectrum:
                time = pretty_num(astrotime('2005-12-02').mjd, sig=5)
            for row in specdata:
                if row[0][0] == '#':
                    joinrow = (' '.join(row)).split('=')
                    if len(joinrow) < 2:
                        continue
                    field = joinrow[0].strip('# ')
                    value = joinrow[1].split('/')[0].strip('\' ')
                    if not time:
                        if field == 'JD':
                            time = str(jd_to_mjd(Decimal(value)))
                        elif field == 'MJD':
                            time = value
                        elif field == 'MJD-OBS':
                            time = value
                    if field == 'OBSERVER':
                        observer = value.capitalize()
                    if field == 'OBSERVAT':
                        observatory = value.capitalize()
                    if field == 'TELESCOP':
                        telescope = value.capitalize()
                    if field == 'INSTRUME':
                        instrument = value.capitalize()
                else:
                    newspec.append(row)
            if not time:
                raise ValueError('Time missing from spectrum.')
            specdata = newspec
            haserrors = len(specdata[0]) == 3 and specdata[0][2] and specdata[0][2] != 'NaN'
            specdata = [list(i) for i in zip(*specdata)]

            wavelengths = specdata[0]
            fluxes = specdata[1]
            errors = None
            if haserrors:
                errors = specdata[2]

            unit_err = 'Variance' if oldname == 'SN2011fe' else 'erg/s/cm^2/Angstrom'
            unit_flx = 'erg/s/cm^2/Angstrom'
            spec = {
                SPECTRUM.U_WAVELENGTHS: 'Angstrom',
                SPECTRUM.U_FLUXES: unit_flx,
                SPECTRUM.U_TIME: 'MJD',
                SPECTRUM.WAVELENGTHS: wavelengths,
                SPECTRUM.FLUXES: fluxes,
                SPECTRUM.U_ERRORS: unit_err,
                SPECTRUM.SOURCE: sources,
                SPECTRUM.FILENAME: filename
            }
            if errors is not None:
                spec[SPECTRUM.ERRORS] = errors
            if time is not None:
                spec[SPECTRUM.TIME] = time
            if observer is not None:
                spec[SPECTRUM.OBSERVER] = observer
            if observatory is not None:
                spec[SPECTRUM.OBSERVATORY] = observatory
            if telescope is not None:
                spec[SPECTRUM.TELESCOPE] = telescope
            if instrument is not None:
                spec[SPECTRUM.INSTRUMENT] = instrument
            catalog.entries[name].add_spectrum(**spec)

            snfcnt = snfcnt + 1
            if catalog.args.travis and snfcnt >= catalog.TRAVIS_QUERY_LIMIT:
                break

    catalog.journal_entries()
    return
