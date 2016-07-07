# -*- coding: utf-8 -*-
"""Imports for the WISeREP spectroscopic repository.
"""
import os
import re
import urllib
import warnings
from copy import deepcopy
from glob import glob
from html import unescape

from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from astrocats.catalog.utils import uniq_cdl

from astrocats.catalog.utils import is_number, pbar, pbar_strings, tprint


def do_wiserep_spectra(catalog):
    task_str = catalog.get_current_task_str()
    secondaryreference = 'WISeREP'
    secondaryrefurl = 'http://wiserep.weizmann.ac.il/'
    secondarybibcode = '2012PASP..124..668Y'
    wiserepcnt = 0

    # These are known to be in error on the WISeREP page, either fix or ignore
    # them.
    wiserepbibcorrectdict = {'2000AJ....120..367G]': '2000AJ....120..367G',
                             'Harutyunyan+et+al.+2008': '2008A&A...488..383H',
                             '0609268': '2007AJ....133...58K',
                             '2006ApJ...636...400Q': '2006ApJ...636..400Q',
                             '2011ApJ...741...76': '2011ApJ...741...76C',
                             '2016PASP...128...961': '2016PASP..128...961',
                             '2002AJ....1124..417H': '2002AJ....1124.417H',
                             '2013ApJ…774…58D': '2013ApJ...774...58D',
                             '2011Sci.333..856S': '2011Sci...333..856S',
                             '2014MNRAS.438,368': '2014MNRAS.438..368T',
                             '2012MNRAS.420.1135': '2012MNRAS.420.1135S',
                             '2012Sci..337..942D': '2012Sci...337..942D',
                             'stt1839': ''}

    oldname = ''
    file_names = next(os.walk(catalog.get_current_task_repo()))[1]
    for folder in pbar_strings(file_names, task_str):
        files = glob(catalog.get_current_task_repo() + '/' + folder + '/*')
        for fname in pbar(files, task_str):
            if '.html' in fname:
                lfiles = deepcopy(files)
                with open(fname, 'r') as f:
                    path = os.path.abspath(fname)
                    response = urllib.request.urlopen('file://' + path)
                    bs = BeautifulSoup(response, 'html5lib')
                    trs = bs.findAll('tr', {'valign': 'top'})
                    for tri, tr in enumerate(trs):
                        if 'Click to show/update object' in str(tr.contents):
                            claimedtype = ''
                            instrument = ''
                            epoch = ''
                            observer = ''
                            reducer = ''
                            specfile = ''
                            produceoutput = True
                            specpath = ''
                            tds = tr.findAll('td')
                            for tdi, td in enumerate(tds):
                                if not td.contents:
                                    continue
                                if tdi == 3:
                                    name = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                elif tdi == 5:
                                    claimedtype = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                    if claimedtype == 'SN':
                                        claimedtype = ''
                                        continue
                                    if claimedtype[:3] == 'SN ':
                                        claimedtype = claimedtype[
                                            3:].strip()
                                    claimedtype = claimedtype.replace(
                                        '-like', '').strip()
                                elif tdi == 9:
                                    instrument = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                elif tdi == 11:
                                    epoch = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                elif tdi == 13:
                                    observer = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                    if (observer == 'Unknown' or
                                            observer == 'Other'):
                                        observer = ''
                                elif tdi == 17:
                                    reducer = re.sub(
                                        '<[^<]+?>', '',
                                        str(td.contents[0])).strip()
                                    if (reducer == 'Unknown' or
                                            reducer == 'Other'):
                                        reducer = ''
                                elif tdi == 25:
                                    speclinks = td.findAll('a')
                                    try:
                                        for link in speclinks:
                                            if 'Ascii' in link['href']:
                                                specfile = link.contents[
                                                    0].strip()
                                                tfiles = deepcopy(lfiles)
                                                for fi, fname in \
                                                        enumerate(lfiles):
                                                    if specfile in fname:
                                                        specpath = fname
                                                        del tfiles[fi]
                                                        lfiles = deepcopy(
                                                            tfiles)
                                                        raise StopIteration
                                    except (KeyboardInterrupt, SystemExit):
                                        raise
                                    except StopIteration:
                                        pass
                                    # if not specpath:
                                        #    warnings.warn('Spectrum file
                                        #  not found, "' + specfile + '"')
                                else:
                                    continue
                        if ('Spec Type:</span>' in str(tr.contents) and
                                produceoutput):
                            produceoutput = False

                            trstr = str(tr)
                            result = re.search('redshift=(.*?)&amp;', trstr)
                            redshift = ''
                            if result:
                                redshift = result.group(1)
                                if (not is_number(redshift) or
                                        float(redshift) > 100.):
                                    redshift = ''

                            result = re.search('publish=(.*?)&amp;', trstr)
                            bibcode = ''
                            if result:
                                bibcode = unescape(urllib.parse.unquote(
                                    urllib.parse.unquote(
                                        result.group(1))).split('/')[-1])

                            if not bibcode:
                                biblink = tr.find(
                                    'a', {'title': 'Link to NASA ADS'})
                                if biblink:
                                    bibcode = biblink.contents[0]

                            if name.startswith('sn'):
                                name = 'SN' + name[2:]
                            if (name.startswith(('CSS', 'SSS', 'MLS')) and
                                    ':' not in name):
                                name = name.replace('-', ':', 1)
                            if name.startswith('MASTERJ'):
                                name = name.replace('MASTERJ', 'MASTER OT J')
                            if name.startswith('PSNJ'):
                                name = name.replace('PSNJ', 'PSN J')
                            name = catalog.get_preferred_name(name)
                            if oldname and name != oldname:
                                catalog.journal_entries()
                            oldname = name
                            name = catalog.add_entry(name)

                            # print(name + ' ' + claimedtype + ' ' + epoch +
                            # ' ' + observer + ' ' + reducer + ' ' + specfile +
                            # ' ' + bibcode + ' ' + redshift)

                            secondarysource = catalog.entries[name].add_source(
                                name=secondaryreference,
                                url=secondaryrefurl,
                                bibcode=secondarybibcode, secondary=True)
                            catalog.entries[name].add_quantity(
                                'alias', name, secondarysource)
                            if bibcode:
                                newbibcode = bibcode
                                if bibcode in wiserepbibcorrectdict:
                                    newbibcode = wiserepbibcorrectdict[bibcode]
                                if newbibcode:
                                    source = catalog.entries[name].add_source(
                                        bibcode=unescape(newbibcode))
                                else:
                                    source = catalog.entries[name].add_source(
                                        name=unescape(bibcode))
                                sources = uniq_cdl([source, secondarysource])
                            else:
                                sources = secondarysource

                            if claimedtype not in ['Other']:
                                catalog.entries[name].add_quantity(
                                    'claimedtype', claimedtype,
                                    secondarysource)
                            catalog.entries[name].add_quantity(
                                'redshift', redshift, secondarysource)

                            if not specpath:
                                continue

                            with open(specpath, 'r') as f:
                                data = [x.split() for x in f]

                                skipspec = False
                                newdata = []
                                oldval = ''
                                for row in data:
                                    if row and '#' not in row[0]:
                                        if (len(row) >= 2 and
                                                is_number(row[0]) and
                                                is_number(row[1]) and
                                                row[1] != oldval):
                                            newdata.append(row)
                                            oldval = row[1]

                                if skipspec or not newdata:
                                    warnings.warn(
                                        'Skipped adding spectrum file ' +
                                        specfile)
                                    continue

                                data = [list(i) for i in zip(*newdata)]
                                wavelengths = data[0]
                                fluxes = data[1]
                                errors = ''
                                if len(data) == 3:
                                    errors = data[1]
                                time = str(astrotime(epoch).mjd)

                                if max([float(x) for x in fluxes]) < 1.0e-5:
                                    fluxunit = 'erg/s/cm^2/Angstrom'
                                else:
                                    fluxunit = 'Uncalibrated'

                                catalog.entries[name].add_spectrum(
                                    'Angstrom', fluxunit,
                                    errors=errors,
                                    errorunit=fluxunit,
                                    wavelengths=wavelengths,
                                    fluxes=fluxes,
                                    u_time='MJD', time=time,
                                    instrument=instrument, source=sources,
                                    observer=observer, reducer=reducer,
                                    filename=specfile)
                                wiserepcnt = wiserepcnt + 1

                                if (catalog.args.travis and
                                        wiserepcnt %
                                        catalog.TRAVIS_QUERY_LIMIT == 0):
                                    break

                tprint('Unadded files: ' + str(len(lfiles) - 1) +
                       "/" + str(len(files) - 1))
                tprint('WISeREP spectrum count: ' + str(wiserepcnt))

    catalog.journal_entries()
    return
