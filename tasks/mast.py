"""Import tasks related to MAST."""
import json
import os
import sys
import time
from collections import OrderedDict
from datetime import datetime
from decimal import Decimal

import numpy as np
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import pbar
from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from astropy.io import fits
from astropy.table import Table

from ..supernova import SUPERNOVA

try:  # Python 3.x
    from urllib.parse import quote as urlencode
    from urllib.request import urlretrieve
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode
    from urllib import urlretrieve

try:  # Python 3.x
    import http.client as httplib
except ImportError:  # Python 2.x
    import httplib


def mastQuery(request):
    """Perform a MAST query.

    Parameters
    ----------
    request (dictionary): The Mashup request json object

    Returns head,content where head is the response HTTP headers, and content
    is the returned data.

    """
    server = 'mast.stsci.edu'

    # Grab Python Version
    version = ".".join(map(str, sys.version_info[:3]))

    # Create Http Header Variables
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Accept": "text/plain",
               "User-agent": "python-requests/" + version}

    # Encoding the request as a json string
    requestString = json.dumps(request)
    requestString = urlencode(requestString)

    # opening the https connection
    conn = httplib.HTTPSConnection(server)

    # Making the query
    conn.request("POST", "/api/v0/invoke", "request=" + requestString, headers)

    # Getting the response
    resp = conn.getresponse()
    head = resp.getheaders()
    content = resp.read().decode('utf-8')

    # Close the https connection
    conn.close()

    return head, content


def do_mast_spectra(catalog):
    """Import HST spectra from MAST."""
    task_str = catalog.get_current_task_str()
    masturl = 'https://mast.stsci.edu'
    mastref = 'MAST'
    fureps = {'erg/cm2/s/A': 'erg/s/cm^2/Angstrom'}

    histfile = os.path.join(
        catalog.get_current_task_repo(), 'MAST', 'history.json')

    if os.path.exists(histfile):
        histdict = json.load(open(histfile, 'r'))
    else:
        histdict = OrderedDict()

    # objectOfInterest = 'ASASSN-14li'
    #
    # resolverRequest = {'service': 'Mast.Name.Lookup',
    #                    'params': {'input': objectOfInterest,
    #                               'format': 'json'},
    #                    }
    #
    # headers, resolvedObjectString = mastQuery(resolverRequest)
    #
    # resolvedObject = json.loads(resolvedObjectString)
    #
    # pp.pprint(resolvedObject)

    # objRa = resolvedObject['resolvedCoordinate'][0]['ra']
    # objDec = resolvedObject['resolvedCoordinate'][0]['decl']

    objs = []
    for entry in catalog.entries:
        if SUPERNOVA.DISCOVER_DATE in catalog.entries[entry]:
            dd = catalog.entries[entry][
                SUPERNOVA.DISCOVER_DATE][0][QUANTITY.VALUE]
            try:
                dt = datetime.strptime(dd, '%Y/%m/%d')
                if dt < datetime(1997, 1, 1):
                    continue
            except Exception:
                pass
        if (SUPERNOVA.RA in catalog.entries[entry] and
                SUPERNOVA.DEC in catalog.entries[entry]):
            objs.append([
                entry,
                catalog.entries[entry][SUPERNOVA.RA][0][QUANTITY.VALUE],
                catalog.entries[entry][SUPERNOVA.DEC][0][QUANTITY.VALUE]])
    if not len(objs):
        return
    objs = np.array(objs).T

    coords = coord(objs[1], objs[2], unit=(un.hourangle, un.deg))

    for ci, co in enumerate(pbar(coords, desc=task_str)):
        entry = objs[0][ci]
        use_cache = False
        if entry in histdict:
            if dt < datetime(datetime.now().year - 5, 1, 1):
                use_cache = True
            if (dt >= datetime(datetime.now().year - 5, 1, 1) and
                    time.time() - histdict[entry][0] < 30. * 86400.):
                use_cache = True
        if use_cache:
            spectra = histdict[entry][1]
        else:
            objRa, objDec = tuple(co.to_string().split())
            mastRequest = {'service': 'Mast.Caom.Cone',
                           'params': {'ra': objRa,
                                      'dec': objDec,
                                      'radius': 0.008},
                           'format': 'json',
                           'pagesize': 1000,
                           'page': 1,
                           'removenullcolumns': True,
                           'removecache': True}

            try:
                headers, mastDataString = mastQuery(mastRequest)
            except Exception:
                print('`mastQuery` failed for `{}`, skipping.'.format(entry))
                continue

            mastData = json.loads(mastDataString)

            # print(mastData.keys())
            # print("Query status:", mastData['status'])

            mastDataTable = Table()

            if 'fields' not in mastData:
                print('`fields` not found for `{}`'.format(entry))
                continue

            for col, atype in [(
                    x['name'], x['type']) for x in mastData['fields']]:
                if atype == "string":
                    atype = "str"
                if atype == "boolean":
                    atype = "bool"
                mastDataTable[col] = np.array(
                    [x.get(col, None) for x in mastData['data']], dtype=atype)

            # print(mastDataTable.columns)

            spectra = [
                x for x in mastDataTable if
                x['dataproduct_type'] == 'spectrum' and x[
                    'obs_collection'] == 'HST']

            spectra = [{
                'target_classification': x['target_classification'],
                'obsid': x['obsid'],
                't_min': x['t_min'],
                't_max': x['t_max'],
                'instrument_name': x['instrument_name'],
                'proposal_pi': x['proposal_pi'],
            } for x in spectra]

        mjd = ''
        instrument = ''
        observer = ''
        for si in range(len(spectra)):
            spec = spectra[si]
            if all([x not in spec['target_classification'].upper()
                    for x in ['SUPERNOVA', 'UNIDENTIFIED']]):
                continue

            obsid = spec['obsid']
            mjd = str(Decimal('0.5') * (
                Decimal(str(spec['t_min'])) + Decimal(str(spec['t_max']))))
            instrument = spec['instrument_name']
            if ('STIS' not in instrument.upper() and
                    'COS' not in instrument.upper()):
                continue
            observer = spec['proposal_pi']

            if use_cache:
                scienceProducts = spec.get('sciProds', [])
            else:
                productRequest = {'service': 'Mast.Caom.Products',
                                  'params': {'obsid': obsid},
                                  'format': 'json',
                                  'pagesize': 100,
                                  'page': 1}

                try:
                    headers, obsProductsString = mastQuery(productRequest)
                except Exception:
                    print(
                        '`mastQuery` failed for `{}`, skipping.'.format(obsid))
                    continue

                obsProducts = json.loads(obsProductsString)

                if 'fields' not in obsProducts:
                    print('`fields` not found for `{}`'.format(obsid))
                    print(obsProducts)
                    continue

                sciProdArr = [x for x in obsProducts['data']
                              if x.get("productType", None) == 'SCIENCE']
                scienceProducts = OrderedDict()

                for col, atype in [
                        (x['name'], x['type']) for x in obsProducts['fields']]:
                    if atype == "string":
                        atype = "str"
                    if atype == "boolean":
                        atype = "bool"
                    if atype == "int":
                        # array may contain nan values, and they do not exist
                        # in numpy integer arrays.
                        atype = "float"
                    scienceProducts[col] = [
                        x.get(col, None) for x in sciProdArr]

                spectra[si]['sciProds'] = scienceProducts

            # print("Number of science products:", len(scienceProducts))
            # print(scienceProducts)

            search_str = '_x1d.fits'
            summed = False
            if any(['_x1dsum.fits' in x for x in scienceProducts[
                    'productFilename']]):
                search_str = '_x1dsum.fits'
                summed = True
            if any(['_sx1.fits' in x for x in scienceProducts[
                    'productFilename']]):
                search_str = '_sx1.fits'
                summed = True
            for ri in range(len(scienceProducts['productFilename'])):
                if search_str not in scienceProducts['productFilename'][ri]:
                    continue
                filename = str(obsid) + "_" + \
                    scienceProducts['productFilename'][ri]
                datafile = os.path.join(
                    catalog.get_current_task_repo(), 'MAST', filename)
                if not os.path.exists(datafile):
                    # link is url, so can just dl
                    if "http" in scienceProducts['dataURI'][ri]:
                        urlretrieve(scienceProducts['dataURI'][ri], datafile)
                    else:  # link is uri, need to go through direct dl request
                        server = 'mast.stsci.edu'
                        conn = httplib.HTTPSConnection(server)
                        conn.request(
                            "GET", "/api/v0/download/file/" +
                            scienceProducts['dataURI'][ri].lstrip('mast:'))
                        resp = conn.getresponse()
                        fileContent = resp.read()
                        with open(datafile, 'wb') as FLE:
                            FLE.write(fileContent)
                        conn.close()

                try:
                    hdulist = fits.open(datafile)
                except Exception:
                    print(
                        "Couldn't read `{}`, maybe private.".format(filename))
                    os.remove(datafile)
                    continue
                for oi, obj in enumerate(hdulist[0].header):
                    if any(x in ['.', '/'] for x in obj):
                        del (hdulist[0].header[oi])
                hdulist[0].verify('silentfix')
                hdrkeys = list(hdulist[0].header.keys())
                # print(hdrkeys)
                name = entry
                if not name:
                    name = hdulist[0].header['OBJECT']
                name, source = catalog.new_entry(
                    name, srcname=mastref, url=masturl, secondary=True)
                sources = [source]
                if 'OBSERVER' in hdrkeys:
                    sources.append(
                        catalog.entries[name].add_source(
                            name=hdulist[0].header['OBSERVER']))
                if observer:
                    source = catalog.entries[name].add_source(name=observer)
                    sources.append(source)
                source = ','.join(sources)

                if summed:
                    wcol = 3
                    fcol = 4
                else:
                    wcol = 2
                    fcol = 3
                try:
                    waves = [str(x) for x in list(hdulist[1].data)[0][wcol]]
                    fluxes = [str(x) for x in list(hdulist[1].data)[0][fcol]]
                except Exception:
                    print('Failed to find waves/fluxes for `{}`.'.format(filename))
                    continue

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
                    specdict[SPECTRUM.TELESCOPE] = hdulist[0].header[
                        'TELESCOP']
                if not instrument and 'INSTRUME' in hdrkeys:
                    instrument = hdulist[0].header['INSTRUME']
                if instrument:
                    specdict[SPECTRUM.INSTRUMENT] = instrument
                if 'SITENAME' in hdrkeys:
                    specdict[SPECTRUM.OBSERVATORY] = hdulist[0].header[
                        'SITENAME']
                elif 'OBSERVAT' in hdrkeys:
                    specdict[SPECTRUM.OBSERVATORY] = hdulist[0].header[
                        'OBSERVAT']
                if 'OBSERVER' in hdrkeys:
                    specdict[SPECTRUM.OBSERVER] = hdulist[0].header['OBSERVER']
                catalog.entries[name].add_spectrum(**specdict)
        if not use_cache and (ci % 100 == 0 or ci == len(coords) - 1):
            histdict[entry] = [time.time(), spectra]
            json.dump(histdict, open(histfile, 'w'),
                      indent='\t', separators=(',', ':'))
        catalog.journal_entries()

    return
