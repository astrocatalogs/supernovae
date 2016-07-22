#!/usr/local/bin/python3.5
import argparse
import csv
import filecmp
import gzip
import hashlib
import json
import operator
import os
import re
import shutil
import sys
import urllib.parse
import urllib.request
import warnings
from collections import OrderedDict
from copy import deepcopy
from glob import glob
from math import ceil, isnan, pi
from statistics import mean

import inflect
import numpy
import requests
from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from astropy.time import Time as astrotime
from bokeh.embed import file_html
from bokeh.layouts import row as bokehrow
from bokeh.layouts import column, layout
from bokeh.models import (ColumnDataSource, CustomJS, DatetimeAxis, HoverTool,
                          LinearAxis, Range1d, Slider)
from bokeh.models.widgets import Select
from bokeh.plotting import Figure, reset_output
from bokeh.resources import CDN
from bs4 import BeautifulSoup
from palettable import cubehelix

from astrocats.catalog.utils import (bandaliasf, bandcodes, bandcolorf,
                                     bandshortaliasf, bandwavef,
                                     bandwavelengths, get_sig_digits,
                                     is_number, pretty_num, radiocolorf,
                                     round_sig, tprint, tq, xraycolorf)
from astrocats.supernovae.scripts.events import (get_event_filename,
                                                 get_event_text)
from astrocats.supernovae.scripts.repos import get_rep_folder, repo_file_list
from cdecimal import Decimal

parser = argparse.ArgumentParser(
    description='Generate a catalog JSON file and plot HTML files from SNE data.')
parser.add_argument('--no-write-catalog', '-nwc', dest='writecatalog',
                    help='Don\'t write catalog file',          default=True, action='store_false')
parser.add_argument('--no-write-html', '-nwh',    dest='writehtml',
                    help='Don\'t write html plot files',       default=True, action='store_false')
parser.add_argument('--no-collect-hosts', '-nch', dest='collecthosts',
                    help='Don\'t collect host galaxy images',  default=True, action='store_false')
parser.add_argument('--force-html', '-fh',        dest='forcehtml',
                    help='Force write html plot files',        default=False, action='store_true')
parser.add_argument('--event-list', '-el',        dest='eventlist',
                    help='Process a list of events',           default=[], type=str, nargs='+')
parser.add_argument('--test', '-te',              dest='test',
                    help='Test this script',                   default=False, action='store_true')
parser.add_argument('--travis', '-tr',            dest='travis',
                    help='Set some options when using Travis', default=False, action='store_true')
parser.add_argument('--boneyard', '-by',          dest='boneyard',
                    help='Make "boneyard" catalog',            default=False, action='store_true')
parser.add_argument('--delete-orphans', '-do',    dest='deleteorphans',
                    help='Delete orphan JSON files',           default=False, action='store_true')
args = parser.parse_args()

infl = inflect.engine()
infl.defnoun("spectrum", "spectra")

outdir = "astrocats/supernovae/output/"
cachedir = "cache/"
jsondir = "json/"
htmldir = "html/"

travislimit = 100

radiosigma = 3.0

googlepingurl = "http://www.google.com/webmasters/tools/ping?sitemap=https%3A%2F%2Fsne.space%2Fsitemap.xml"

linkdir = "https://sne.space/sne/"

testsuffix = '.test' if args.test else ''

mycolors = cubehelix.perceptual_rainbow_16.hex_colors[:14]

columnkey = [
    "check",
    "name",
    "alias",
    "discoverdate",
    "maxdate",
    "maxappmag",
    "maxabsmag",
    "host",
    "ra",
    "dec",
    "hostra",
    "hostdec",
    "hostoffsetang",
    "hostoffsetdist",
    "instruments",
    "redshift",
    "velocity",
    "lumdist",
    "claimedtype",
    "ebv",
    "photolink",
    "spectralink",
    "radiolink",
    "xraylink",
    "references",
    "download",
    "responsive"
]

eventignorekey = [
    "download"
]

header = [
    "",
    "Name",
    "Aliases",
    "Disc. Date",
    "Max Date",
    r"<em>m</em><sub>max</sub>",
    r"<em>M</em><sub>max</sub>",
    "Host Name",
    "R.A.",
    "Dec.",
    "Host R.A.",
    "Host Dec.",
    "Host Offset (\")",
    "Host Offset (kpc)",
    "Instruments/Bands",
    r"<em>z</em>",
    r"<em>v</em><sub>&#9737;</sub> (km/s)",
    r"<em>d</em><sub>L</sub> (Mpc)",
    "Type",
    "E(B-V)",
    "Phot.",
    "Spec.",
    "Radio",
    "X-ray",
    "References",
    "Data",
    ""
]

eventpageheader = [
    "",
    "Name",
    "Aliases",
    "Discovery Date",
    "Maximum Date [band]",
    r"<em>m</em><sub>max</sub> [band]",
    r"<em>M</em><sub>max</sub> [band]",
    "Host Name",
    "R.A.",
    "Dec.",
    "Host R.A.",
    "Host Dec.",
    "Host Offset (\")",
    "Host Offset (kpc)",
    "Instruments/Bands",
    r"<em>z</em>",
    r"<em>v</em><sub>&#9737;</sub> (km/s)",
    r"<em>d</em><sub>L</sub> (Mpc)",
    "Claimed Type",
    "E(B-V)",
    "Photometry",
    "Spectra",
    "Radio",
    "X-ray",
    "References",
    "Download",
    ""
]

titles = [
    "",
    "Name (IAU name preferred)",
    "Aliases",
    "Discovey Date (year-month-day)",
    "Date of Maximum (year-month-day)",
    "Maximum apparent AB magnitude",
    "Maximum absolute AB magnitude",
    "Host Name",
    "Supernova J2000 Right Ascension (h:m:s)",
    "Supernova J2000 Declination (d:m:s)",
    "Host J2000 Right Ascension (h:m:s)",
    "Host J2000 Declination (d:m:s)",
    "Host Offset (Arcseconds)",
    "Host Offset (kpc)",
    "List of Instruments and Bands",
    "Redshift",
    "Heliocentric velocity (km/s)",
    "Luminosity distance (Mpc)",
    "Claimed Type",
    "Milky Way Reddening",
    "Photometry",
    "pectra",
    "Radio",
    "X-rays",
    "Bibcodes of references with most data on event",
    "Download and edit data",
    ""
]

photokeys = [
    'u_time',
    'time',
    'band',
    'instrument',
    'magnitude',
    'aberr',
    'upperlimit',
    'source'
]

sourcekeys = [
    'name',
    'alias',
    'secondary'
]

newfiletemplate = (
    '''{
\t"{0}":{
\t\t"name":"{0}",
\t\t"alias":[
\t\t\t"{0}"
\t\t]
\t}
}'''
)

with open('astrocats/supernovae/html/sitemap-template.xml', 'r') as f:
    sitemaptemplate = f.read()

if len(columnkey) != len(header):
    raise(ValueError('Header not same length as key list.'))
    sys.exit(0)

if len(columnkey) != len(eventpageheader):
    raise(ValueError('Event page header not same length as key list.'))
    sys.exit(0)

dataavaillink = "<a href='https://bitbucket.org/Guillochon/sne'>Y</a>"

header = OrderedDict(list(zip(columnkey, header)))
eventpageheader = OrderedDict(list(zip(columnkey, eventpageheader)))
titles = OrderedDict(list(zip(columnkey, titles)))

wavedict = dict(list(zip(bandcodes, bandwavelengths)))


def event_filename(name):
    return(name.replace('/', '_'))

# Replace bands with real colors, if possible.
# for b, code in enumerate(bandcodes):
#    if (code in bandwavelengths):
#        hexstr = irgb_string_from_xyz(xyz_from_wavelength(bandwavelengths[code]))
#        if (hexstr != "#000000"):
#            bandcolors[b] = hexstr

coldict = dict(list(zip(list(range(len(columnkey))), columnkey)))


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)


def utf8(x):
    return str(x, 'utf-8')


def label_format(label):
    newlabel = label.replace('Angstrom', 'Å')
    newlabel = newlabel.replace('^2', '²')
    return newlabel


def is_valid_link(url):
    response = requests.get(url)
    try:
        response.raise_for_status()
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        return False
    return True


def get_first_value(name, field):
    return catalog[name][field][0]['value'] if field in catalog[name] and catalog[name][field] else ''


def get_first_kind(name, field):
    return (catalog[name][field][0]['kind'] if field in catalog[name] and
            catalog[name][field] and 'kind' in catalog[name][field][0] else '')


def md5file(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

catalog = OrderedDict()
catalogcopy = OrderedDict()
snepages = [["# name", "aliases", "max apparent mag", "max mag date", "claimed type", "redshift", "redshift kind",
             "ra", "dec", "# of photometric obs.", "URL"]]
sourcedict = {}
nophoto = []
lcspye = []
lcspno = []
lconly = []
sponly = []
hasalc = []
hasasp = []
totalphoto = 0
totalspectra = 0

if os.path.isfile(outdir + cachedir + 'hostimgs.json'):
    with open(outdir + cachedir + 'hostimgs.json', 'r') as f:
        filetext = f.read()
    hostimgdict = json.loads(filetext)
else:
    hostimgdict = {}

files = repo_file_list(normal=(not args.boneyard), bones=args.boneyard)

if os.path.isfile(outdir + cachedir + 'md5s.json'):
    with open(outdir + cachedir + 'md5s.json', 'r') as f:
        filetext = f.read()
    md5dict = json.loads(filetext)
else:
    md5dict = {}

for fcnt, eventfile in enumerate(tq(sorted(files, key=lambda s: s.lower()))):
    fileeventname = os.path.splitext(os.path.basename(eventfile))[
        0].replace('.json', '')
    if args.eventlist and fileeventname not in args.eventlist:
        continue

    if args.travis and fcnt >= travislimit:
        break

    entry_changed = False
    checksum = md5file(eventfile)
    if eventfile not in md5dict or md5dict[eventfile] != checksum:
        entry_changed = True
        md5dict[eventfile] = checksum

    filetext = get_event_text(eventfile)

    catalog.update(json.loads(filetext, object_pairs_hook=OrderedDict))
    entry = next(reversed(catalog))

    eventname = entry

    if args.eventlist and eventname not in args.eventlist:
        continue

    tprint(eventfile + ' [' + checksum + ']')

    repfolder = get_rep_folder(catalog[entry])
    if os.path.isfile("astrocats/supernovae/input/sne-internal/" + fileeventname + ".json"):
        catalog[entry]['download'] = 'e'
    else:
        catalog[entry]['download'] = ''
    if 'discoverdate' in catalog[entry]:
        for d, date in enumerate(catalog[entry]['discoverdate']):
            catalog[entry]['discoverdate'][d]['value'] = catalog[
                entry]['discoverdate'][d]['value'].split('.')[0]
    if 'maxdate' in catalog[entry]:
        for d, date in enumerate(catalog[entry]['maxdate']):
            catalog[entry]['maxdate'][d]['value'] = catalog[
                entry]['maxdate'][d]['value'].split('.')[0]

    hostmag = ''
    hosterr = ''
    if 'photometry' in catalog[entry]:
        for photo in catalog[entry]['photometry']:
            if 'host' in photo and ('upperlimit' not in photo or not photo['upperlimit']):
                hostmag = float(photo['magnitude'])
                hosterr = float(photo['e_magnitude']
                                ) if 'e_magnitude' in photo else 0.0

        # Delete the host magnitudes so they are not plotted as points
        catalog[entry]['photometry'][:] = [x for x in catalog[entry]['photometry']
                                           if 'host' not in x]

    photoavail = 'photometry' in catalog[entry] and any(
        ['magnitude' in x for x in catalog[entry]['photometry']])
    radioavail = 'photometry' in catalog[entry] and any(
        ['fluxdensity' in x for x in catalog[entry]['photometry']])
    xrayavail = 'photometry' in catalog[entry] and any(
        ['counts' in x and 'magnitude' not in x for x in catalog[entry]['photometry']])
    spectraavail = 'spectra' in catalog[entry]

    # Must be two sigma above host magnitude, if host magnitude known, to add
    # to phot count.
    numphoto = len([x for x in catalog[entry]['photometry'] if 'upperlimit' not in x and 'magnitude' in x and
                    (not hostmag or not 'includeshost' in x or float(x['magnitude']) <= (hostmag - 2.0 * hosterr))]) if photoavail else 0
    numradio = len([x for x in catalog[entry]['photometry'] if 'upperlimit' not in x and 'fluxdensity' in x and
                    (not x['e_fluxdensity'] or float(x['fluxdensity']) > radiosigma * float(x['e_fluxdensity'])) and
                    (not hostmag or not 'includeshost' in x or float(x['magnitude']) <= (hostmag - 2.0 * hosterr))]) if photoavail else 0
    numxray = len([x for x in catalog[entry]['photometry'] if 'upperlimit' not in x and 'counts' in x and
                   (not hostmag or not 'includeshost' in x or float(x['magnitude']) <= (hostmag - 2.0 * hosterr))]) if photoavail else 0
    numspectra = len(catalog[entry]['spectra']) if spectraavail else 0

    redshiftfactor = (1.0 / (1.0 + float(catalog[entry]['redshift'][0]['value']))) if (
        'redshift' in catalog[entry]) else 1.0
    dayframe = 'Rest frame days' if 'redshift' in catalog[
        entry] else 'Observer frame days'

    mjdmax = ''
    if 'maxdate' in catalog[entry]:
        datestr = catalog[entry]['maxdate'][0]['value']
        datesplit = datestr.split('/')
        if len(datesplit) < 2:
            datestr += "/01"
        if len(datesplit) < 3:
            datestr += "/01"
        try:
            mjdmax = astrotime(datestr.replace('/', '-')).mjd
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass

    minphotoep = ''
    maxphotoep = ''
    if mjdmax:
        photoeps = [(Decimal(x['time']) - Decimal(mjdmax + 0.5)) * Decimal(redshiftfactor) for x in catalog[entry]['photometry']
                    if 'upperlimit' not in x and 'includeshost' not in x and 'magnitude' in x and 'time' in x] if photoavail else []
        if photoeps:
            minphotoep = pretty_num(float(min(photoeps)), sig=3)
            maxphotoep = pretty_num(float(max(photoeps)), sig=3)

    minspectraep = ''
    maxspectraep = ''
    if mjdmax:
        spectraeps = ([(Decimal(x['time']) - Decimal(mjdmax + 0.5)) * Decimal(redshiftfactor) for x in catalog[entry]['spectra'] if 'time' in x]
                      if spectraavail else [])
        if spectraeps:
            minspectraep = pretty_num(float(min(spectraeps)), sig=3)
            maxspectraep = pretty_num(float(max(spectraeps)), sig=3)

    catalog[entry]['numphoto'] = numphoto
    catalog[entry]['numradio'] = numradio
    catalog[entry]['numxray'] = numxray
    catalog[entry]['numspectra'] = numspectra

    distancemod = 0.0
    if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
        distancemod = float(get_first_value(entry, 'maxappmag')) - \
            float(get_first_value(entry, 'maxabsmag'))

    plotlink = "sne/" + fileeventname + "/"
    if photoavail:
        catalog[entry]['photolink'] = (str(numphoto) +
                                       ((',' + minphotoep + ',' + maxphotoep) if (minphotoep and maxphotoep and minphotoep != maxphotoep) else ''))
    if radioavail:
        catalog[entry]['radiolink'] = str(numradio)
    if xrayavail:
        catalog[entry]['xraylink'] = str(numxray)
    if spectraavail:
        catalog[entry]['spectralink'] = (str(numspectra) +
                                         ((',' + minspectraep + ',' + maxspectraep) if (minspectraep and maxspectraep and minspectraep != maxspectraep) else ''))

    prange = list(range(len(catalog[entry]['photometry']))
                  ) if 'photometry' in catalog[entry] else []

    instrulist = sorted([_f for _f in list({catalog[entry]['photometry'][x]['instrument']
                                            if 'instrument' in catalog[entry]['photometry'][x] else None for x in prange}) if _f])
    if len(instrulist) > 0:
        instruments = ''
        for i, instru in enumerate(instrulist):
            instruments += instru
            bandlist = sorted([_f for _f in list({bandshortaliasf(catalog[entry]['photometry'][x]['band'] if 'band' in catalog[entry]['photometry'][x] else '')
                                                  if 'instrument' in catalog[entry]['photometry'][x] and catalog[entry]['photometry'][x]['instrument'] == instru
                                                  else "" for x in prange}) if _f], key=lambda y: (bandwavef(y), y))
            if bandlist:
                instruments += ' (' + ", ".join(bandlist) + ')'
            if i < len(instrulist) - 1:
                instruments += ', '

        # Now add bands without attached instrument
        obandlist = sorted([_f for _f in list({bandshortaliasf(catalog[entry]['photometry'][x]['band'] if 'band' in catalog[entry]['photometry'][x] else '')
                                               if 'instrument' not in catalog[entry]['photometry'][x] else "" for x in prange}) if _f], key=lambda y: (bandwavef(y), y))
        if obandlist:
            instruments += ", " + ", ".join(obandlist)
        catalog[entry]['instruments'] = instruments
    else:
        bandlist = sorted([_f for _f in list({bandshortaliasf(catalog[entry]['photometry'][x]['band']
                                                              if 'band' in catalog[entry]['photometry'][x] else '') for x in prange}) if _f], key=lambda y: (bandwavef(y), y))
        if len(bandlist) > 0:
            catalog[entry]['instruments'] = ", ".join(bandlist)

    tools = "pan,wheel_zoom,box_zoom,save,crosshair,reset,resize"

    # Check file modification times before constructing .html files, which is
    # expensive
    dohtml = True
    if not args.forcehtml:
        if os.path.isfile(outdir + htmldir + fileeventname + ".html"):
            if not entry_changed:
                dohtml = False

    # Copy JSON files up a directory if they've changed
    if dohtml:
        shutil.copy2(eventfile, outdir + jsondir + os.path.basename(eventfile))

    if (photoavail or radioavail or xrayavail) and dohtml and args.writehtml:
        phototime = [(mean([float(y) for y in x['time']]) if isinstance(x['time'], list) else float(x['time']))
                     for x in catalog[entry]['photometry'] if any([y in x for y in ['fluxdensity', 'magnitude', 'flux']])]
        phototimelowererrs = [float(x['e_lower_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if any([y in x for y in ['fluxdensity', 'magnitude', 'flux']])]
        phototimeuppererrs = [float(x['e_upper_time']) if ('e_lower_time' in x and 'e_upper_time' in x) in x
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if any([y in x for y in ['fluxdensity', 'magnitude', 'flux']])]

        x_buffer = 0.1 * (max(phototime) - min(phototime)
                          ) if len(phototime) > 1 else 1.0

        min_x_range = -0.5 * x_buffer + \
            min([x - y for x, y in list(zip(phototime, phototimeuppererrs))])
        max_x_range = 2.0 * x_buffer + \
            max([x + y for x, y in list(zip(phototime, phototimelowererrs))])

    if photoavail and dohtml and args.writehtml:
        phototime = [float(x['time']) for x in catalog[entry][
            'photometry'] if 'magnitude' in x]
        phototimelowererrs = [float(x['e_lower_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'magnitude' in x]
        phototimeuppererrs = [float(x['e_upper_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photoAB = [float(x['magnitude']) for x in catalog[entry][
            'photometry'] if 'magnitude' in x]
        photoABlowererrs = [float(x['e_lower_magnitude']) if ('e_lower_magnitude' in x)
                            else (float(x['e_magnitude']) if 'e_magnitude' in x else 0.) for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photoABuppererrs = [float(x['e_upper_magnitude']) if ('e_upper_magnitude' in x)
                            else (float(x['e_magnitude']) if 'e_magnitude' in x else 0.) for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photoband = [(x['band'] if 'band' in x else '')
                     for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photoinstru = [(x['instrument'] if 'instrument' in x else '')
                       for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photosource = [', '.join(str(j) for j in sorted(int(i) for i in x['source'].split(',')))
                       for x in catalog[entry]['photometry'] if 'magnitude' in x]
        phototype = [(x['upperlimit'] if 'upperlimit' in x else False)
                     for x in catalog[entry]['photometry'] if 'magnitude' in x]
        photocorr = [('k' if 'kcorrected' in x else 'raw')
                     for x in catalog[entry]['photometry'] if 'magnitude' in x]

        photoutime = catalog[entry]['photometry'][0][
            'u_time'] if 'u_time' in catalog[entry]['photometry'][0] else 'MJD'
        hastimeerrs = (len(list(filter(None, phototimelowererrs)))
                       and len(list(filter(None, phototimeuppererrs))))
        hasABerrs = (len(list(filter(None, photoABlowererrs)))
                     and len(list(filter(None, photoABuppererrs))))
        tt = [
            ("Source ID(s)", "@src"),
            ("Epoch (" + photoutime + ")",
             "@x{1.11}" + ("<sub>-@xle{1}</sub><sup>+@xue{1}</sup>" if hastimeerrs else ""))
        ]
        tt += [("Apparent Magnitude", "@y{1.111}" + (
            "<sub>-@lerr{1.11}</sub><sup>+@uerr{1.11}</sup>" if hasABerrs else ""))]
        if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
            tt += [("Absolute Magnitude", "@yabs{1.111}" + (
                "<sub>-@lerr{1.11}</sub><sup>+@uerr{1.11}</sup>" if hasABerrs else ""))]
        if len(list(filter(None, photoband))):
            tt += [("Band", "@desc")]
        if len(list(filter(None, photoinstru))):
            tt += [("Instrument", "@instr")]
        hover = HoverTool(tooltips=tt)

        min_y_range = 0.5 + max([(x + y) if not z else x for x, y,
                                 z in list(zip(photoAB, photoABuppererrs, phototype))])
        max_y_range = -0.5 + min([(x - y) if not z else x for x,
                                  y, z in list(zip(photoAB, photoABlowererrs, phototype))])

        p1 = Figure(title='Photometry for ' + eventname, active_drag='box_zoom',
                    # sizing_mode = "scale_width",
                    y_axis_label='Apparent Magnitude', tools=tools, plot_width=485, plot_height=485,
                    x_range=(min_x_range, max_x_range), y_range=(min_y_range, max_y_range), toolbar_location='above', toolbar_sticky=False)
        p1.xaxis.axis_label_text_font = 'futura'
        p1.yaxis.axis_label_text_font = 'futura'
        p1.xaxis.major_label_text_font = 'futura'
        p1.yaxis.major_label_text_font = 'futura'
        p1.xaxis.axis_label_text_font_size = '11pt'
        p1.yaxis.axis_label_text_font_size = '11pt'
        p1.xaxis.major_label_text_font_size = '8pt'
        p1.yaxis.major_label_text_font_size = '8pt'
        p1.title.align = 'center'
        p1.title.text_font_size = '16pt'
        p1.title.text_font = 'futura'

        min_x_date = astrotime(min_x_range, format='mjd').datetime
        max_x_date = astrotime(max_x_range, format='mjd').datetime

        p1.extra_x_ranges = {"gregorian date": Range1d(
            start=min_x_date, end=max_x_date)}
        p1.add_layout(DatetimeAxis(major_label_text_font_size='8pt', axis_label='Time (' + photoutime + '/Gregorian)',
                                   major_label_text_font='futura', axis_label_text_font='futura', major_tick_in=0,
                                   x_range_name="gregorian date", axis_label_text_font_size='11pt'), 'below')

        if mjdmax:
            min_xm_range = (min_x_range - mjdmax) * redshiftfactor
            max_xm_range = (max_x_range - mjdmax) * redshiftfactor
            p1.extra_x_ranges["time since max"] = Range1d(
                start=min_xm_range, end=max_xm_range)
            p1.add_layout(LinearAxis(axis_label="Time since max (" + dayframe + ")", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     x_range_name="time since max", axis_label_text_font_size='11pt'), 'above')

        if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
            min_y_absmag = min_y_range - distancemod
            max_y_absmag = max_y_range - distancemod
            p1.extra_y_ranges = {"abs mag": Range1d(
                start=min_y_absmag, end=max_y_absmag)}
            p1.add_layout(LinearAxis(axis_label="Absolute Magnitude", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     y_range_name="abs mag", axis_label_text_font_size='11pt'), 'right')
        p1.add_tools(hover)

        xs = []
        ys = []
        err_xs = []
        err_ys = []

        for x, y, xlowerr, xupperr, ylowerr, yupperr in list(zip(phototime, photoAB, phototimelowererrs,
                                                                 phototimeuppererrs, photoABlowererrs, photoABuppererrs)):
            xs.append(x)
            ys.append(y)
            err_xs.append((x - xlowerr, x + xupperr))
            err_ys.append((y - ylowerr, y + yupperr))

        bandset = set(photoband)
        bandset = [i for (j, i) in sorted(
            list(zip(list(map(bandaliasf, bandset)), bandset)))]

        sources = []
        corrects = ['raw', 'k']
        glyphs = [[] for x in range(len(corrects))]
        for ci, corr in enumerate(corrects):
            for band in bandset:
                bandname = bandaliasf(band)
                indb = [i for i, j in enumerate(photoband) if j == band]
                indt = [i for i, j in enumerate(phototype) if not j]
                indnex = [i for i, j in enumerate(
                    phototimelowererrs) if j == 0.]
                indyex = [i for i, j in enumerate(
                    phototimelowererrs) if j > 0.]
                indney = [i for i, j in enumerate(photoABuppererrs) if j == 0.]
                indyey = [i for i, j in enumerate(photoABuppererrs) if j > 0.]
                indc = [i for i, j in enumerate(photocorr) if j == corr]
                indne = set(indb).intersection(indt).intersection(
                    indc).intersection(indney).intersection(indnex)
                indye = set(indb).intersection(indt).intersection(
                    indc).intersection(set(indyey).union(indyex))

                noerrorlegend = bandname if len(indne) == 0 else ''

                data = dict(
                    x=[phototime[i] for i in indne],
                    y=[photoAB[i] for i in indne],
                    lerr=[photoABlowererrs[i] for i in indne],
                    uerr=[photoABuppererrs[i] for i in indne],
                    desc=[photoband[i] for i in indne],
                    instr=[photoinstru[i] for i in indne],
                    src=[photosource[i] for i in indne]
                )
                if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
                    data['yabs'] = [photoAB[i] - distancemod for i in indne]
                if hastimeerrs:
                    data['xle'] = [phototimelowererrs[i] for i in indne]
                    data['xue'] = [phototimeuppererrs[i] for i in indne]

                sources.append(ColumnDataSource(data))
                glyphs[ci].append(p1.circle('x', 'y', source=sources[-1], color=bandcolorf(
                    band), fill_color="white", legend=noerrorlegend, size=4).glyph)

                data = dict(
                    x=[phototime[i] for i in indye],
                    y=[photoAB[i] for i in indye],
                    lerr=[photoABlowererrs[i] for i in indye],
                    uerr=[photoABuppererrs[i] for i in indye],
                    desc=[photoband[i] for i in indye],
                    instr=[photoinstru[i] for i in indye],
                    src=[photosource[i] for i in indye]
                )
                if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
                    data['yabs'] = [photoAB[i] - distancemod for i in indye]
                if hastimeerrs:
                    data['xle'] = [phototimelowererrs[i] for i in indye]
                    data['xue'] = [phototimeuppererrs[i] for i in indye]

                sources.append(ColumnDataSource(data))
                glyphs[ci].append(p1.multi_line([err_xs[x] for x in indye], [
                                  [ys[x], ys[x]] for x in indye], color=bandcolorf(band)).glyph)
                glyphs[ci].append(p1.multi_line([[xs[x], xs[x]] for x in indye], [
                                  err_ys[x] for x in indye], color=bandcolorf(band)).glyph)
                glyphs[ci].append(p1.circle('x', 'y', source=sources[-1],
                                            color=bandcolorf(band), legend=bandname, size=4).glyph)

                upplimlegend = bandname if len(
                    indye) == 0 and len(indne) == 0 else ''

                indt = [i for i, j in enumerate(phototype) if j]
                ind = set(indb).intersection(indt)
                data = dict(
                    x=[phototime[i] for i in ind],
                    y=[photoAB[i] for i in ind],
                    lerr=[photoABlowererrs[i] for i in ind],
                    uerr=[photoABuppererrs[i] for i in ind],
                    desc=[photoband[i] for i in ind],
                    instr=[photoinstru[i] for i in ind],
                    src=[photosource[i] for i in ind]
                )
                if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
                    data['yabs'] = [photoAB[i] - distancemod for i in ind]
                if hastimeerrs:
                    data['xle'] = [phototimelowererrs[i] for i in ind]
                    data['xue'] = [phototimeuppererrs[i] for i in ind]

                sources.append(ColumnDataSource(data))
                # Currently Bokeh doesn't support tooltips for
                # inverted_triangle, so hide an invisible circle behind for the
                # tooltip
                glyphs[ci].append(
                    p1.circle('x', 'y', source=sources[-1], alpha=0.0, size=7).glyph)
                glyphs[ci].append(p1.inverted_triangle('x', 'y', source=sources[-1],
                                                       color=bandcolorf(band), legend=upplimlegend, size=7).glyph)

                for gi, gly in enumerate(glyphs[ci]):
                    if corr != 'raw':
                        glyphs[ci][gi].visible = False

        p1.legend.label_text_font = 'futura'
        p1.legend.label_text_font_size = '8pt'
        p1.legend.label_width = 20
        p1.legend.label_height = 14
        p1.legend.glyph_height = 14

        if any([x != 'raw' for x in photocorr]):
            photodicts = {}
            for ci, corr in enumerate(corrects):
                for gi, gly in enumerate(glyphs[ci]):
                    photodicts[corr + str(gi)] = gly
            sdicts = dict(zip(['s' + str(x)
                               for x in range(len(sources))], sources))
            photodicts.update(sdicts)
            photocallback = CustomJS(args=photodicts, code="""
                var show = 'all';
                if (cb_obj.get('value') == 'Raw') {
                    show = 'raw';
                } else if (cb_obj.get('value') == 'K-Corrected') {
                    show = 'k';
                }
                var viz = (show == 'all') ? true : false;
                var corrects = ["raw", "k"];
                for (c = 0; c < """ + str(len(corrects)) + """; c++) {
                    for (g = 0; g < """ + str(len(glyphs[0])) + """; g++) {
                        if (show == 'all' || corrects[c] != show) {
                            eval(corrects[c] + g).attributes.visible = viz;
                        } else if (show != 'all' || corrects[c] == show) {
                            eval(corrects[c] + g).attributes.visible = !viz;
                        }
                    }
                }
                for (s = 0; s < """ + str(len(sources)) + """; s++) {
                    eval('s'+s).trigger('change');
                }
            """)
            photochecks = Select(title="Photometry to show:",
                                 value="Raw", options=["Raw", "K-Corrected", "All"], callback=photocallback)
        else:
            photochecks = ''

    if spectraavail and dohtml and args.writehtml:
        spectrumwave = []
        spectrumflux = []
        spectrumerrs = []
        spectrummjdmax = []
        hasepoch = True
        if 'redshift' in catalog[entry]:
            z = float(catalog[entry]['redshift'][0]['value'])
        catalog[entry]['spectra'] = list(
            filter(None, [x if 'data' in x else None for x in catalog[entry]['spectra']]))
        for spectrum in catalog[entry]['spectra']:
            spectrumdata = deepcopy(spectrum['data'])
            oldlen = len(spectrumdata)
            specslice = ceil(float(len(spectrumdata)) / 10000)
            spectrumdata = spectrumdata[::specslice]
            spectrumdata = [x for x in spectrumdata if is_number(
                x[1]) and not isnan(float(x[1]))]
            specrange = range(len(spectrumdata))

            if 'deredshifted' in spectrum and spectrum['deredshifted'] and 'redshift' in catalog[entry]:
                spectrumwave.append(
                    [float(spectrumdata[x][0]) * (1.0 + z) for x in specrange])
            else:
                spectrumwave.append([float(spectrumdata[x][0])
                                     for x in specrange])

            spectrumflux.append([float(spectrumdata[x][1]) for x in specrange])
            if 'errorunit' in spectrum:
                spectrumerrs.append([float(spectrumdata[x][2])
                                     for x in specrange])
                spectrumerrs[-1] = [x if is_number(x) and not isnan(
                    float(x)) else 0. for x in spectrumerrs[-1]]

            if 'u_time' not in spectrum or 'time' not in spectrum:
                hasepoch = False

            if 'u_time' in spectrum and 'time' in spectrum and spectrum['u_time'] == 'MJD' and 'redshift' in catalog[entry] and mjdmax:
                specmjd = (float(spectrum['time']) - mjdmax) * redshiftfactor
                spectrummjdmax.append(specmjd)

        nspec = len(catalog[entry]['spectra'])

        prunedwave = []
        prunedflux = []
        for i in reversed(range(nspec)):
            ri = nspec - i - 1
            prunedwave.append([])
            prunedflux.append([])
            for wi, wave in enumerate(spectrumwave[i]):
                exclude = False
                if 'exclude' in catalog[entry]['spectra'][i]:
                    for exclusion in catalog[entry]['spectra'][i]['exclude']:
                        if 'below' in exclusion:
                            if wave <= float(exclusion['below']):
                                exclude = True
                        elif 'above' in exclusion:
                            if wave >= float(exclusion['above']):
                                exclude = True
                if not exclude:
                    prunedwave[ri].append(wave)
                    prunedflux[ri].append(spectrumflux[i][wi])

        prunedwave = list(reversed(prunedwave))
        prunedflux = list(reversed(prunedflux))

        prunedscaled = deepcopy(prunedflux)
        for f, flux in enumerate(prunedscaled):
            std = numpy.std(flux)
            prunedscaled[f] = [x / std for x in flux]

        y_height = 0.
        y_offsets = [0. for x in range(nspec)]
        for i in reversed(range(nspec)):
            y_offsets[i] = y_height
            if (i - 1 >= 0 and 'time' in catalog[entry]['spectra'][i] and 'time' in catalog[entry]['spectra'][i - 1]
                    and catalog[entry]['spectra'][i]['time'] == catalog[entry]['spectra'][i - 1]['time']):
                ydiff = 0
            else:
                ydiff = 0.8 * (max(prunedscaled[i]) - min(prunedscaled[i]))
            prunedscaled[i] = [j + y_height for j in prunedscaled[i]]
            y_height += ydiff

        maxsw = max(list(map(max, prunedwave)))
        minsw = min(list(map(min, prunedwave)))
        maxfl = max(list(map(max, prunedscaled)))
        minfl = min(list(map(min, prunedscaled)))
        maxfldiff = max(map(operator.sub, list(
            map(max, prunedscaled)), list(map(min, prunedscaled))))
        x_buffer = 0.0  # 0.1*(maxsw - minsw)
        x_range = [-x_buffer + minsw, x_buffer + maxsw]
        y_buffer = 0.1 * maxfldiff
        y_range = [-y_buffer + minfl, y_buffer + maxfl]

        for f, flux in enumerate(prunedscaled):
            prunedscaled[f] = [x - y_offsets[f] for x in flux]

        tt2 = [("Source ID(s)", "@src")]
        if 'redshift' in catalog[entry]:
            tt2 += [("λ (rest)", "@xrest{1.1} Å")]
        tt2 += [
            ("λ (obs)", "@x{1.1} Å"),
            ("Flux", "@yorig"),
            ("Flux unit", "@fluxunit")
        ]

        if hasepoch:
            tt2 += [("Epoch (" + spectrum['u_time'] + ")", "@epoch{1.11}")]

        if mjdmax:
            tt2 += [("Rest days to max", "@mjdmax{1.11}")]

        hover = HoverTool(tooltips=tt2)

        p2 = Figure(title='Spectra for ' + eventname, x_axis_label=label_format('Observed Wavelength (Å)'), active_drag='box_zoom',
                    y_axis_label=label_format('Flux (scaled)' + (' + offset'
                                                                 if (nspec > 1) else '')), x_range=x_range, tools=tools,  # sizing_mode = "scale_width",
                    plot_width=485, plot_height=485, y_range=y_range, toolbar_location='above', toolbar_sticky=False)
        p2.xaxis.axis_label_text_font = 'futura'
        p2.yaxis.axis_label_text_font = 'futura'
        p2.xaxis.major_label_text_font = 'futura'
        p2.yaxis.major_label_text_font = 'futura'
        p2.xaxis.axis_label_text_font_size = '11pt'
        p2.yaxis.axis_label_text_font_size = '11pt'
        p2.xaxis.major_label_text_font_size = '8pt'
        p2.yaxis.major_label_text_font_size = '8pt'
        p2.title.align = 'center'
        p2.title.text_font_size = '16pt'
        p2.title.text_font = 'futura'
        p2.add_tools(hover)

        sources = []
        for i in range(len(prunedwave)):
            sl = len(prunedscaled[i])
            fluxunit = catalog[entry]['spectra'][i][
                'u_fluxes'] if 'u_fluxes' in catalog[entry][
                    'spectra'][i] else ''

            data = dict(
                x0=prunedwave[i],
                y0=prunedscaled[i],
                yorig=spectrumflux[i],
                fluxunit=[label_format(fluxunit)] * sl,
                x=prunedwave[i],
                y=[y_offsets[i] + j for j in prunedscaled[i]],
                src=[catalog[entry]['spectra'][i]['source']] * sl
            )
            if 'redshift' in catalog[entry]:
                data['xrest'] = [x / (1.0 + z) for x in prunedwave[i]]
            if hasepoch:
                data['epoch'] = [catalog[entry]['spectra'][i]['time']
                                 for j in prunedscaled[i]]
                if mjdmax and spectrummjdmax:
                    data['mjdmax'] = [spectrummjdmax[i]
                                      for j in prunedscaled[i]]
            sources.append(ColumnDataSource(data))
            p2.line('x', 'y', source=sources[i], color=mycolors[
                    i % len(mycolors)], line_width=2, line_join='round')

        if 'redshift' in catalog[entry]:
            minredw = minsw / (1.0 + z)
            maxredw = maxsw / (1.0 + z)
            p2.extra_x_ranges = {"other wavelength": Range1d(
                start=minredw, end=maxredw)}
            p2.add_layout(LinearAxis(axis_label="Restframe Wavelength (Å)",
                                     x_range_name="other wavelength", axis_label_text_font_size='11pt',
                                     axis_label_text_font='futura',
                                     major_label_text_font_size='8pt', major_label_text_font='futura'), 'above')

        sdicts = dict(zip(['s' + str(x)
                           for x in range(len(sources))], sources))
        callback = CustomJS(args=sdicts, code="""
            var yoffs = [""" + ','.join([str(x) for x in y_offsets]) + """];
            for (s = 0; s < """ + str(len(sources)) + """; s++) {
                var data = eval('s'+s).get('data');
                var redshift = """ + str(z if 'redshift' in catalog[entry] else 0.) + """;
                if (!('binsize' in data)) {
                    data['binsize'] = 1.0
                }
                if (!('spacing' in data)) {
                    data['spacing'] = 1.0
                }
                if (cb_obj.get('title') == 'Spacing') {
                    data['spacing'] = cb_obj.get('value');
                } else {
                    data['binsize'] = cb_obj.get('value');
                }
                var f = data['binsize']
                var space = data['spacing']
                var x0 = data['x0'];
                var y0 = data['y0'];
                var dx0 = x0[1] - x0[0];
                var yoff = space*yoffs[s];
                data['x'] = [x0[0] - 0.5*Math.max(0., f - dx0)];
                data['xrest'] = [(x0[0] - 0.5*Math.max(0., f - dx0))/(1.0 + redshift)];
                data['y'] = [y0[0] + yoff];
                var xaccum = 0.;
                var yaccum = 0.;
                for (i = 0; i < x0.length; i++) {
                    var dx;
                    if (i == 0) {
                        dx = x0[i+1] - x0[i];
                    } else {
                        dx = x0[i] - x0[i-1];
                    }
                    xaccum += dx;
                    yaccum += y0[i]*dx;
                    if (xaccum >= f) {
                        data['x'].push(data['x'][data['x'].length-1] + xaccum);
                        data['xrest'].push(data['x'][data['x'].length-1]/(1.0 + redshift));
                        data['y'].push(yaccum/xaccum + yoff);
                        xaccum = 0.;
                        yaccum = 0.;
                    }
                }
                eval('s'+s).trigger('change');
            }
        """)

        binslider = Slider(start=0, end=20, value=1, step=0.5, width=230, title=label_format(
            "Bin size (Angstrom)"), callback=callback)
        spacingslider = Slider(start=0, end=2, value=1, step=0.02,
                               width=230, title=label_format("Spacing"), callback=callback)

    if radioavail and dohtml and args.writehtml:
        phototime = [float(x['time']) for x in catalog[entry][
            'photometry'] if 'fluxdensity' in x]
        phototimelowererrs = [float(x['e_lower_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        phototimeuppererrs = [float(x['e_upper_time']) if ('e_lower_time' in x and 'e_upper_time' in x) in x
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photofd = [float(x['fluxdensity']) if (float(x['fluxdensity']) > radiosigma * float(x['e_fluxdensity'])) else
                   round_sig(radiosigma * float(x['e_fluxdensity']), sig=get_sig_digits(x['e_fluxdensity'])) for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photofderrs = [(float(x['e_fluxdensity']) if 'e_fluxdensity' in x else 0.)
                       for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photoufd = [(x['u_fluxdensity'] if 'fluxdensity' in x else '')
                    for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photofreq = [(x['frequency'] if 'fluxdensity' in x else '')
                     for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photoufreq = [(x['u_frequency'] if 'fluxdensity' in x else '')
                      for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photoinstru = [(x['instrument'] if 'instrument' in x else '')
                       for x in catalog[entry]['photometry'] if 'fluxdensity' in x]
        photosource = [', '.join(str(j) for j in sorted(int(i) for i in catalog[entry]['photometry'][x]['source'].split(',')))
                       for x, y in enumerate(catalog[entry]['photometry']) if 'fluxdensity' in y]
        phototype = [(True if 'upperlimit' in x or radiosigma * float(x['e_fluxdensity']) >= float(x['fluxdensity']) else False)
                     for x in catalog[entry]['photometry'] if 'fluxdensity' in x]

        photoutime = catalog[entry]['photometry'][0][
            'u_time'] if 'u_time' in catalog[entry]['photometry'][0] else 'MJD'
        if distancemod:
            dist = (10.0**(1.0 + 0.2 * distancemod) * un.pc).cgs.value
            areacorr = 4.0 * pi * dist**2.0 * ((1.0e-6 * un.jansky).cgs.value)

        x_buffer = 0.1 * (max(phototime) - min(phototime)
                          ) if len(phototime) > 1 else 1.0

        hastimeerrs = (len(list(filter(None, phototimelowererrs)))
                       and len(list(filter(None, phototimeuppererrs))))
        hasfderrs = len(list(filter(None, photofderrs)))
        tt = [
            ("Source ID(s)", "@src"),
            ("Epoch (" + photoutime + ")",
             "@x{1.11}" + ("<sub>-@xle{1}</sub><sup>+@xue{1}</sup>" if hastimeerrs else ""))
        ]
        tt += [("Flux Density (" + photoufd[0] + ")",
                "@y{1.11}" + ("&nbsp;±&nbsp;@err{1.11}" if hasfderrs else ""))]
        if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
            tt += [("Iso. Lum. (ergs s⁻¹)", "@yabs" +
                    ("&nbsp;±&nbsp;@abserr" if hasfderrs else ""))]
        if len(list(filter(None, photofreq))):
            tt += [("Frequency (" + photoufreq[0] + ")", "@desc")]
        if len(list(filter(None, photoinstru))):
            tt += [("Instrument", "@instr")]
        hover = HoverTool(tooltips=tt)

        if photoavail:
            x_range = p1.x_range
        else:
            x_range = (min_x_range, max_x_range)
        min_y_range = min([x - y for x, y in list(zip(photofd, photofderrs))])
        max_y_range = max([x + y for x, y in list(zip(photofd, photofderrs))])
        [min_y_range, max_y_range] = [min_y_range - 0.1 *
                                      (max_y_range - min_y_range), max_y_range + 0.1 * (max_y_range - min_y_range)]

        p3 = Figure(title='Radio Observations of ' + eventname, active_drag='box_zoom',
                    # sizing_mode = "scale_width",
                    y_axis_label='Flux Density (µJy)', tools=tools, plot_width=485, plot_height=485,
                    x_range=x_range, y_range=(min_y_range, max_y_range), toolbar_location='above', toolbar_sticky=False)
        p3.xaxis.axis_label_text_font = 'futura'
        p3.yaxis.axis_label_text_font = 'futura'
        p3.xaxis.major_label_text_font = 'futura'
        p3.yaxis.major_label_text_font = 'futura'
        p3.xaxis.axis_label_text_font_size = '11pt'
        p3.yaxis.axis_label_text_font_size = '11pt'
        p3.xaxis.major_label_text_font_size = '8pt'
        p3.yaxis.major_label_text_font_size = '8pt'
        p3.title.align = 'center'
        p3.title.text_font_size = '16pt'
        p3.title.text_font = 'futura'

        min_x_date = astrotime(min_x_range, format='mjd').datetime
        max_x_date = astrotime(max_x_range, format='mjd').datetime

        p3.extra_x_ranges = {"gregorian date": Range1d(
            start=min_x_date, end=max_x_date)}
        p3.add_layout(DatetimeAxis(major_label_text_font_size='8pt', axis_label='Time (' + photoutime + '/Gregorian)',
                                   major_label_text_font='futura', axis_label_text_font='futura', major_tick_in=0,
                                   x_range_name="gregorian date", axis_label_text_font_size='11pt'), 'below')

        if mjdmax:
            min_xm_range = (min_x_range - mjdmax) * redshiftfactor
            max_xm_range = (max_x_range - mjdmax) * redshiftfactor
            p3.extra_x_ranges["time since max"] = Range1d(
                start=min_xm_range, end=max_xm_range)
            p3.add_layout(LinearAxis(axis_label="Time since max (" + dayframe + ")", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     x_range_name="time since max", axis_label_text_font_size='11pt'), 'above')

        if distancemod:
            min_y_absmag = min([(x - y) * (areacorr * float(z) * ((1.0 * un.GHz).cgs.value))
                                for x, y, z in list(zip(photofd, photofderrs, photofreq))])
            max_y_absmag = max([(x + y) * (areacorr * float(z) * ((1.0 * un.GHz).cgs.value))
                                for x, y, z in list(zip(photofd, photofderrs, photofreq))])
            [min_y_absmag, max_y_absmag] = [min_y_absmag - 0.1 *
                                            (max_y_absmag - min_y_absmag), max_y_absmag + 0.1 * (max_y_absmag - min_y_absmag)]
            p3.extra_y_ranges = {"abs mag": Range1d(
                start=min_y_absmag, end=max_y_absmag)}
            p3.add_layout(LinearAxis(axis_label="Isotropic Luminosity at ν (ergs s⁻¹)", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     y_range_name="abs mag", axis_label_text_font_size='11pt'), 'right')
            p3.yaxis[1].formatter.precision = 1
        p3.add_tools(hover)

        xs = []
        ys = []
        err_xs = []
        err_ys = []

        for x, y, xlowerr, xupperr, yerr in list(zip(phototime, photofd, phototimelowererrs, phototimeuppererrs, photofderrs)):
            xs.append(x)
            ys.append(y)
            err_xs.append((x - xlowerr, x + xupperr))
            err_ys.append((y - yerr, y + yerr))

        freqset = set(photofreq)
        frequnit = photoufreq[0] if photoufreq else ''

        for freq in freqset:
            indb = [i for i, j in enumerate(photofreq) if j == freq]
            indt = [i for i, j in enumerate(phototype) if not j]
            # Should always have upper error if have lower error.
            indnex = [i for i, j in enumerate(phototimelowererrs) if j == 0.]
            indyex = [i for i, j in enumerate(phototimelowererrs) if j > 0.]
            indney = [i for i, j in enumerate(photofderrs) if j == 0.]
            indyey = [i for i, j in enumerate(photofderrs) if j > 0.]
            indne = set(indb).intersection(indt).intersection(
                indney).intersection(indnex)
            indye = set(indb).intersection(
                indt).intersection(set(indyey).union(indyex))

            freqlabel = str(freq) + " " + frequnit

            noerrorlegend = freqlabel if len(
                indye) == 0 and len(indne) > 0 else ''

            data = dict(
                x=[phototime[i] for i in indne],
                y=[photofd[i] for i in indne],
                err=[photofderrs[i] for i in indne],
                desc=[photofreq[i] for i in indne],
                instr=[photoinstru[i] for i in indne],
                src=[photosource[i] for i in indne]
            )
            if distancemod:
                data['yabs'] = [str(round_sig(photofd[
                                    i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in indne]
                data['abserr'] = [str(round_sig(photofderrs[
                                      i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in indne]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in indne]
                data['xue'] = [phototimeuppererrs[i] for i in indne]

            source = ColumnDataSource(data)
            p3.circle('x', 'y', source=source, color=radiocolorf(
                freq), fill_color="white", legend=noerrorlegend, size=4)

            yeserrorlegend = freqlabel if len(indye) > 0 else ''

            data = dict(
                x=[phototime[i] for i in indye],
                y=[photofd[i] for i in indye],
                err=[photofderrs[i] for i in indye],
                desc=[photofreq[i] for i in indye],
                instr=[photoinstru[i] for i in indye],
                src=[photosource[i] for i in indye]
            )
            if distancemod:
                data['yabs'] = [str(round_sig(photofd[
                                    i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in indye]
                data['abserr'] = [str(round_sig(photofderrs[
                                      i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in indye]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in indye]
                data['xue'] = [phototimeuppererrs[i] for i in indye]

            source = ColumnDataSource(data)
            p3.multi_line([err_xs[x] for x in indye], [[ys[x], ys[x]]
                                                       for x in indye], color=radiocolorf(freq))
            p3.multi_line([[xs[x], xs[x]] for x in indye], [err_ys[x]
                                                            for x in indye], color=radiocolorf(freq))
            p3.circle('x', 'y', source=source, color=radiocolorf(
                freq), legend=yeserrorlegend, size=4)

            upplimlegend = freqlabel if len(
                indye) == 0 and len(indne) == 0 else ''

            indt = [i for i, j in enumerate(phototype) if j]
            ind = set(indb).intersection(indt)
            data = dict(
                x=[phototime[i] for i in ind],
                y=[photofd[i] for i in ind],
                err=[photofderrs[i] for i in ind],
                desc=[photofreq[i] for i in ind],
                instr=[photoinstru[i] for i in ind],
                src=[photosource[i] for i in ind]
            )
            if distancemod:
                data['yabs'] = [str(round_sig(photofd[
                                    i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in ind]
                data['abserr'] = [str(round_sig(photofderrs[
                                      i] * (areacorr * float(freq) * ((1.0 * un.GHz).cgs.value)), sig=3)) for i in ind]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in ind]
                data['xue'] = [phototimeuppererrs[i] for i in ind]

            source = ColumnDataSource(data)
            # Currently Bokeh doesn't support tooltips for inverted_triangle,
            # so hide an invisible circle behind for the tooltip
            p3.circle('x', 'y', source=source, alpha=0.0, size=7)
            p3.inverted_triangle('x', 'y', source=source,
                                 color=radiocolorf(freq), legend=upplimlegend, size=7)

        p3.legend.label_text_font = 'futura'
        p3.legend.label_text_font_size = '8pt'
        p3.legend.label_width = 20
        p3.legend.label_height = 14
        p3.legend.glyph_height = 14

    if xrayavail and dohtml and args.writehtml:
        phototime = [(mean([float(y) for y in x['time']]) if isinstance(x['time'], list) else float(x['time']))
                     for x in catalog[entry]['photometry'] if 'flux' in x]
        phototimelowererrs = [float(x['e_lower_time']) if ('e_lower_time' in x and 'e_upper_time' in x)
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'flux' in x]
        phototimeuppererrs = [float(x['e_upper_time']) if ('e_lower_time' in x and 'e_upper_time' in x) in x
                              else (float(x['e_time']) if 'e_time' in x else 0.) for x in catalog[entry]['photometry'] if 'flux' in x]
        photofl = [float(x['flux']) if ('e_flux' not in x or float(x['flux']) > radiosigma * float(x['e_flux'])) else
                   round_sig(radiosigma * float(x['e_flux']), sig=get_sig_digits(x['e_flux'])) for x in catalog[entry]['photometry'] if 'flux' in x]
        photoflerrs = [(float(x['e_flux']) if 'e_flux' in x else 0.)
                       for x in catalog[entry]['photometry'] if 'flux' in x]
        photoufl = [(x['u_flux'] if 'flux' in x else '')
                    for x in catalog[entry]['photometry'] if 'flux' in x]
        photoener = [((' - '.join([y.rstrip('.') for y in x['energy']]) if isinstance(x['energy'], list) else x['energy']) if 'flux' in x else '')
                     for x in catalog[entry]['photometry'] if 'flux' in x]
        photouener = [(x['u_energy'] if 'flux' in x else '')
                      for x in catalog[entry]['photometry'] if 'flux' in x]
        photoinstru = [(x['instrument'] if 'instrument' in x else '')
                       for x in catalog[entry]['photometry'] if 'flux' in x]
        photosource = [', '.join(str(j) for j in sorted(int(i) for i in catalog[entry]['photometry'][x]['source'].split(',')))
                       for x, y in enumerate(catalog[entry]['photometry']) if 'flux' in y]
        phototype = [(True if 'upperlimit' in x or radiosigma * float(x['e_flux']) >= float(x['flux']) else False)
                     for x in catalog[entry]['photometry'] if 'flux' in x]

        photoutime = catalog[entry]['photometry'][0][
            'u_time'] if 'u_time' in catalog[entry]['photometry'][0] else 'MJD'
        if distancemod:
            dist = (10.0**(1.0 + 0.2 * distancemod) * un.pc).cgs.value
            areacorr = 4.0 * pi * dist**2.0

        x_buffer = 0.1 * (max(phototime) - min(phototime)
                          ) if len(phototime) > 1 else 1.0

        hastimeerrs = (len(list(filter(None, phototimelowererrs)))
                       and len(list(filter(None, phototimeuppererrs))))
        hasflerrs = len(list(filter(None, photoflerrs)))
        tt = [
            ("Source ID(s)", "@src"),
            ("Epoch (" + photoutime + ")",
             "@x{1.11}" + ("<sub>-@xle{1}</sub><sup>+@xue{1}</sup>" if hastimeerrs else ""))
        ]
        tt += [("Flux (" + photoufl[0].replace("ergs/s/cm^2", "ergs s⁻¹ cm⁻²") + ")",
                "@y" + ("&nbsp;±&nbsp;@err" if hasflerrs else ""))]
        if 'maxabsmag' in catalog[entry] and 'maxappmag' in catalog[entry]:
            tt += [("Iso. Lum. (ergs s⁻¹)", "@yabs" +
                    ("&nbsp;±&nbsp;@abserr" if hasflerrs else ""))]
        if len(list(filter(None, photoener))):
            tt += [("Frequency (" + photouener[0] + ")", "@desc")]
        if len(list(filter(None, photoinstru))):
            tt += [("Instrument", "@instr")]
        hover = HoverTool(tooltips=tt)

        if photoavail:
            x_range = p1.x_range
        else:
            x_range = (min_x_range, max_x_range)
        min_y_range = min([x - y for x, y in list(zip(photofl, photoflerrs))])
        max_y_range = max([x + y for x, y in list(zip(photofl, photoflerrs))])
        [min_y_range, max_y_range] = [min_y_range - 0.1 *
                                      (max_y_range - min_y_range), max_y_range + 0.1 * (max_y_range - min_y_range)]

        p4 = Figure(title='X-ray Observations of ' + eventname, active_drag='box_zoom',
                    # sizing_mode = "scale_width",
                    y_axis_label='Flux (ergs s⁻¹ cm⁻²)', tools=tools, plot_width=485, plot_height=485,
                    x_range=x_range, y_range=(min_y_range, max_y_range), toolbar_location='above', toolbar_sticky=False)
        p4.xaxis.axis_label_text_font = 'futura'
        p4.yaxis.axis_label_text_font = 'futura'
        p4.xaxis.major_label_text_font = 'futura'
        p4.yaxis.major_label_text_font = 'futura'
        p4.xaxis.axis_label_text_font_size = '11pt'
        p4.yaxis.axis_label_text_font_size = '11pt'
        p4.xaxis.major_label_text_font_size = '8pt'
        p4.yaxis.major_label_text_font_size = '8pt'
        p4.yaxis[0].formatter.precision = 1
        p4.title.align = 'center'
        p4.title.text_font_size = '16pt'
        p4.title.text_font = 'futura'

        min_x_date = astrotime(min_x_range, format='mjd').datetime
        max_x_date = astrotime(max_x_range, format='mjd').datetime

        p4.extra_x_ranges = {"gregorian date": Range1d(
            start=min_x_date, end=max_x_date)}
        p4.add_layout(DatetimeAxis(major_label_text_font_size='8pt', axis_label='Time (' + photoutime + '/Gregorian)',
                                   major_label_text_font='futura', axis_label_text_font='futura', major_tick_in=0,
                                   x_range_name="gregorian date", axis_label_text_font_size='11pt'), 'below')

        if mjdmax:
            min_xm_range = (min_x_range - mjdmax) * redshiftfactor
            max_xm_range = (max_x_range - mjdmax) * redshiftfactor
            p4.extra_x_ranges["time since max"] = Range1d(
                start=min_xm_range, end=max_xm_range)
            p4.add_layout(LinearAxis(axis_label="Time since max (" + dayframe + ")", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     x_range_name="time since max", axis_label_text_font_size='11pt'), 'above')

        if distancemod:
            min_y_absmag = min(
                [(x - y) * areacorr for x, y in list(zip(photofl, photoflerrs))])
            max_y_absmag = max(
                [(x + y) * areacorr for x, y in list(zip(photofl, photoflerrs))])
            [min_y_absmag, max_y_absmag] = [min_y_absmag - 0.1 *
                                            (max_y_absmag - min_y_absmag), max_y_absmag + 0.1 * (max_y_absmag - min_y_absmag)]
            p4.extra_y_ranges = {"abs mag": Range1d(
                start=min_y_absmag, end=max_y_absmag)}
            p4.add_layout(LinearAxis(axis_label="Luminosity in band (ergs s⁻¹)", major_label_text_font_size='8pt',
                                     major_label_text_font='futura', axis_label_text_font='futura',
                                     y_range_name="abs mag", axis_label_text_font_size='11pt'), 'right')
            p4.yaxis[1].formatter.precision = 1
        p4.add_tools(hover)

        xs = []
        ys = []
        err_xs = []
        err_ys = []

        for x, y, xlowerr, xupperr, yerr in list(zip(phototime, photofl, phototimelowererrs, phototimeuppererrs, photoflerrs)):
            xs.append(x)
            ys.append(y)
            err_xs.append((x - xlowerr, x + xupperr))
            err_ys.append((y - yerr, y + yerr))

        enerset = set(photoener)
        enerunit = photouener[0] if photouener else ''

        for ener in enerset:
            indb = [i for i, j in enumerate(photoener) if j == ener]
            indt = [i for i, j in enumerate(phototype) if not j]
            # Should always have upper error if have lower error.
            indnex = [i for i, j in enumerate(phototimelowererrs) if j == 0.]
            indyex = [i for i, j in enumerate(phototimelowererrs) if j > 0.]
            indney = [i for i, j in enumerate(photoflerrs) if j == 0.]
            indyey = [i for i, j in enumerate(photoflerrs) if j > 0.]
            indne = set(indb).intersection(indt).intersection(
                indney).intersection(indnex)
            indye = set(indb).intersection(
                indt).intersection(set(indyey).union(indyex))

            enerlabel = str(ener) + " " + enerunit

            noerrorlegend = enerlabel if len(
                indye) == 0 and len(indne) > 0 else ''

            data = dict(
                x=[phototime[i] for i in indne],
                y=[photofl[i] for i in indne],
                err=[photoflerrs[i] for i in indne],
                desc=[photoener[i] for i in indne],
                instr=[photoinstru[i] for i in indne],
                src=[photosource[i] for i in indne]
            )
            if distancemod:
                data['yabs'] = [
                    str(round_sig(photofl[i] * areacorr, sig=3)) for i in indne]
                data['abserr'] = [
                    str(round_sig(photoflerrs[i] * areacorr, sig=3)) for i in indne]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in indne]
                data['xue'] = [phototimeuppererrs[i] for i in indne]

            source = ColumnDataSource(data)
            p4.circle('x', 'y', source=source, color=xraycolorf(ener),
                      fill_color="white", legend=noerrorlegend, size=4)

            yeserrorlegend = enerlabel if len(indye) > 0 else ''

            data = dict(
                x=[phototime[i] for i in indye],
                y=[photofl[i] for i in indye],
                err=[photoflerrs[i] for i in indye],
                desc=[photoener[i] for i in indye],
                instr=[photoinstru[i] for i in indye],
                src=[photosource[i] for i in indye]
            )
            if distancemod:
                data['yabs'] = [
                    str(round_sig(photofl[i] * areacorr, sig=3)) for i in indye]
                data['abserr'] = [
                    str(round_sig(photoflerrs[i] * areacorr, sig=3)) for i in indye]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in indye]
                data['xue'] = [phototimeuppererrs[i] for i in indye]

            source = ColumnDataSource(data)
            p4.multi_line([err_xs[x] for x in indye], [[ys[x], ys[x]]
                                                       for x in indye], color=xraycolorf(ener))
            p4.multi_line([[xs[x], xs[x]] for x in indye], [err_ys[x]
                                                            for x in indye], color=xraycolorf(ener))
            p4.circle('x', 'y', source=source, color=xraycolorf(
                ener), legend=yeserrorlegend, size=4)

            upplimlegend = enerlabel if len(
                indye) == 0 and len(indne) == 0 else ''

            indt = [i for i, j in enumerate(phototype) if j]
            ind = set(indb).intersection(indt)
            data = dict(
                x=[phototime[i] for i in ind],
                y=[photofl[i] for i in ind],
                err=[photoflerrs[i] for i in ind],
                desc=[photoener[i] for i in ind],
                instr=[photoinstru[i] for i in ind],
                src=[photosource[i] for i in ind]
            )
            if distancemod:
                data['yabs'] = [
                    str(round_sig(photofl[i] * areacorr, sig=3)) for i in ind]
                data['abserr'] = [
                    str(round_sig(photoflerrs[i] * areacorr, sig=3)) for i in ind]
            if hastimeerrs:
                data['xle'] = [phototimelowererrs[i] for i in ind]
                data['xue'] = [phototimeuppererrs[i] for i in ind]

            source = ColumnDataSource(data)
            # Currently Bokeh doesn't support tooltips for inverted_triangle,
            # so hide an invisible circle behind for the tooltip
            p4.circle('x', 'y', source=source, alpha=0.0, size=7)
            p4.inverted_triangle('x', 'y', source=source,
                                 color=xraycolorf(ener), legend=upplimlegend, size=7)

        p4.legend.label_text_font = 'futura'
        p4.legend.label_text_font_size = '8pt'
        p4.legend.label_width = 20
        p4.legend.label_height = 14
        p4.legend.glyph_height = 14

    hasimage = False
    skyhtml = ''
    if 'ra' in catalog[entry] and 'dec' in catalog[entry] and args.collecthosts:
        snra = catalog[entry]['ra'][0]['value']
        sndec = catalog[entry]['dec'][0]['value']
        try:
            c = coord(ra=snra, dec=sndec, unit=(un.hourangle, un.deg))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            warnings.warn('Malformed angle for event ' + entry + '.')
        else:
            # if 'lumdist' in catalog[entry] and float(catalog[entry]['lumdist'][0]['value']) > 0.:
            #    if 'host' in catalog[entry] and catalog[entry]['host'][0]['value'] == 'Milky Way':
            #        sdssimagescale = max(0.05,0.4125/float(catalog[entry]['lumdist'][0]['value']))
            #    else:
            #    sdssimagescale = max(0.5,20.6265/float(catalog[entry]['lumdist'][0]['value']))
            # else:
            #    if 'host' in catalog[entry] and catalog[entry]['host'][0]['value'] == 'Milky Way':
            #        sdssimagescale = 0.006
            #    else:
            #    sdssimagescale = 0.5
            #dssimagescale = 0.13889*sdssimagescale
            # At the moment, no way to check if host is in SDSS footprint
            # without comparing to empty image, which is only possible at fixed
            # angular resolution.
            sdssimagescale = 0.3
            dssimagescale = 0.13889 * sdssimagescale

            imgsrc = ''
            hasimage = True
            if eventname in hostimgdict:
                imgsrc = hostimgdict[eventname]
            else:
                try:
                    response = urllib.request.urlopen('http://skyservice.pha.jhu.edu/DR12/ImgCutout/getjpeg.aspx?ra='
                                                      + str(c.ra.deg) + '&dec=' + str(c.dec.deg) + '&scale=' + str(sdssimagescale) + '&width=500&height=500&opt=G', timeout=60)
                    resptxt = response.read()
                except (KeyboardInterrupt, SystemExit):
                    raise
                except:
                    hasimage = False
                else:
                    with open(outdir + htmldir + fileeventname + '-host.jpg', 'wb') as f:
                        f.write(resptxt)
                    imgsrc = 'SDSS'

                if hasimage and filecmp.cmp(outdir + htmldir + fileeventname + '-host.jpg', 'astrocats/supernovae/input/missing.jpg'):
                    hasimage = False

                if not hasimage:
                    hasimage = True
                    url = ("http://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Position=" + str(urllib.parse.quote_plus(snra + " " + sndec)) +
                           "&coordinates=J2000&coordinates=&projection=Tan&pixels=500&size=" + str(dssimagescale) + "&float=on&scaling=Log&resolver=SIMBAD-NED" +
                           "&Sampler=_skip_&Deedger=_skip_&rotation=&Smooth=&lut=colortables%2Fb-w-linear.bin&PlotColor=&grid=_skip_&gridlabels=1" +
                           "&catalogurl=&CatalogIDs=on&RGB=1&survey=DSS2+IR&survey=DSS2+Red&survey=DSS2+Blue&IOSmooth=&contour=&contourSmooth=&ebins=null")

                    try:
                        response = urllib.request.urlopen(url, timeout=60)
                        bandsoup = BeautifulSoup(response, "html5lib")
                    except (KeyboardInterrupt, SystemExit):
                        raise
                    except:
                        hasimage = False
                    else:
                        images = bandsoup.findAll('img')
                        imgname = ''
                        for image in images:
                            if "Quicklook RGB image" in image.get('alt', ''):
                                imgname = image.get('src', '').split('/')[-1]

                        if imgname:
                            try:
                                response = urllib.request.urlopen(
                                    'http://skyview.gsfc.nasa.gov/tempspace/fits/' + imgname)
                            except (KeyboardInterrupt, SystemExit):
                                raise
                            except:
                                hasimage = False
                            else:
                                with open(outdir + htmldir + fileeventname + '-host.jpg', 'wb') as f:
                                    f.write(response.read())
                                imgsrc = 'DSS'
                        else:
                            hasimage = False

        if hasimage:
            if imgsrc == 'SDSS':
                hostimgdict[eventname] = 'SDSS'
                skyhtml = ('<a href="http://skyserver.sdss.org/DR12/en/tools/chart/navi.aspx?opt=G&ra='
                           + str(c.ra.deg) + '&dec=' + str(c.dec.deg) + '&scale=0.15"><img src="' + fileeventname + '-host.jpg" width=250></a>')
            elif imgsrc == 'DSS':
                hostimgdict[eventname] = 'DSS'
                url = ("http://skyview.gsfc.nasa.gov/current/cgi/runquery.pl?Position=" + str(urllib.parse.quote_plus(snra + " " + sndec)) +
                       "&coordinates=J2000&coordinates=&projection=Tan&pixels=500&size=" + str(dssimagescale) + "float=on&scaling=Log&resolver=SIMBAD-NED" +
                       "&Sampler=_skip_&Deedger=_skip_&rotation=&Smooth=&lut=colortables%2Fb-w-linear.bin&PlotColor=&grid=_skip_&gridlabels=1" +
                       "&catalogurl=&CatalogIDs=on&RGB=1&survey=DSS2+IR&survey=DSS2+Red&survey=DSS2+Blue&IOSmooth=&contour=&contourSmooth=&ebins=null")
                skyhtml = ('<a href="' + url + '"><img src="' +
                           fileeventname + '-host.jpg" width=250></a>')
        else:
            hostimgdict[eventname] = 'None'

    if dohtml and args.writehtml:
        # if (photoavail and spectraavail) and dohtml and args.writehtml:
        plots = []
        if photoavail:
            if photochecks:
                p1box = column(p1, photochecks)
            else:
                p1box = p1
            plots += [p1box]
        if spectraavail:
            plots += [column(p2, bokehrow(binslider, spacingslider))]
        if radioavail:
            plots += [p3]
        if xrayavail:
            plots += [p4]

        p = layout([plots[i:i + 2] for i in range(0, len(plots), 2)],
                   ncols=2, toolbar_location=None)

        html = '<html><head><title>' + eventname + '</title>'
        if photoavail or spectraavail or radioavail or xrayavail:
            html = file_html(p, CDN, eventname)
            # html = html + '''<link href="https://cdn.pydata.org/bokeh/release/bokeh-0.11.0.min.css" rel="stylesheet" type="text/css">
            #    <script src="https://cdn.pydata.org/bokeh/release/bokeh-0.11.0.min.js"></script>''' + script + '</head><body>'
        else:
            html = '<html><title></title><body></body></html>'

        # if photoavail and spectraavail:
        #    html = html + div['p1'] + div['p2']# + div['binslider'] + div['spacingslider']
        # elif photoavail:
        #    html = html + div['p1']
        # elif spectraavail:
        #    html = html + div['p2'] + div['binslider'] + div['spacingslider']

        #html = html + '</body></html>'

        html = html.replace('<body>',
                            '''<body class='event-body'><div style="padding-bottom:8px;"><strong>Disclaimer:</strong> All data collected by the OSC was originally generated by others, if you intend to use this data in a publication, we ask that you please cite the linked sources and/or contact the sources of the data directly. Data sources are revealed by hovering over the data with your cursor.</div>''')
        html = re.sub(r'(\<\/title\>)', r'''\1\n
            <base target="_parent" />\n
            <link rel="stylesheet" href="https://sne.space/astrocats/astrocats/supernovae/html/event.css" type="text/css">\n
            <script type="text/javascript" src="https://sne.space/astrocats/astrocats/supernovae/scripts/marks.js" type="text/css"></script>\n
            <script type="text/javascript">\n
                if(top==self)\n
                this.location="''' + eventname + '''"\n
            </script>'''
                      , html)

        repfolder = get_rep_folder(catalog[entry])
        html = re.sub(r'(\<\/body\>)', '<div class="event-download">' + r'<a href="' +
                      linkdir + fileeventname + r'.json" download>' + r'Download all data for ' + eventname +
                      r'</a></div>\n\1', html)
        issueargs = '?title=' + ('[' + eventname + '] <Descriptive issue title>').encode('ascii', 'xmlcharrefreplace').decode("utf-8") + '&body=' + \
            ('Please describe the issue with ' + eventname + '\'s data here, be as descriptive as possible! ' +
             'If you believe the issue appears in other events as well, please identify which other events the issue possibly extends to.').encode('ascii', 'xmlcharrefreplace').decode("utf-8")
        html = re.sub(r'(\<\/body\>)', '<div class="event-issue">' + r'<a href="https://github.com/astrocatalogs/supernovae/issues/new' +
                      issueargs + r'" target="_blank">' + r'Report an issue with ' + eventname +
                      r'</a></div>\n\1', html)

        newhtml = r'<div class="event-tab-div"><h3 class="event-tab-title">Event metadata</h3><table class="event-table"><tr><th width=100px class="event-cell">Quantity</th><th class="event-cell">Value<sup>Sources</sup> [Kind]</th></tr>\n'
        for key in columnkey:
            if key in catalog[entry] and key not in eventignorekey and len(catalog[entry][key]) > 0:
                keyhtml = ''
                if isinstance(catalog[entry][key], str):
                    if key in ['photolink', 'spectralink', 'radiolink', 'xraylink']:
                        keysplit = catalog[entry][key].split(',')
                        if keysplit:
                            num = int(keysplit[0])
                            keyhtml = keyhtml + keysplit[0] + ' ' + (infl.plural(
                                'spectrum', num) if key == 'spectralink' else infl.plural('detection', num))
                            if len(keysplit) == 3:
                                keyhtml = keyhtml + \
                                    '<br>[' + keysplit[1] + ' – ' + \
                                    keysplit[2] + ' days from max]'
                    else:
                        subentry = re.sub('<[^<]+?>', '', catalog[entry][key])
                        keyhtml = keyhtml + subentry
                else:
                    for r, row in enumerate(catalog[entry][key]):
                        if 'value' in row and 'source' in row:
                            sources = [str(x) for x in sorted([x.strip() for x in row['source'].split(
                                ',')], key=lambda x: float(x) if is_number(x) else float("inf"))]
                            sourcehtml = ''
                            sourcecsv = ','.join(sources)
                            for s, source in enumerate(sources):
                                sourcehtml = sourcehtml + \
                                    (', ' if s > 0 else '') + r'<a href="#source' + \
                                    source + r'">' + source + r'</a>'
                            keyhtml = keyhtml + (r'<br>' if r > 0 else '')
                            keyhtml = keyhtml + "<div class='singletooltip'>"
                            if 'derived' in row and row['derived']:
                                keyhtml = keyhtml + '<span class="derived">'
                            keyhtml = keyhtml + row['value']
                            if ((key == 'maxdate' or key == 'maxabsmag' or key == 'maxappmag') and 'maxband' in catalog[entry]
                                    and catalog[entry]['maxband']):
                                keyhtml = keyhtml + \
                                    r' [' + catalog[entry]['maxband'][0]['value'] + ']'
                            if 'e_value' in row:
                                keyhtml = keyhtml + r' ± ' + row['e_value']
                            if 'derived' in row and row['derived']:
                                keyhtml = keyhtml + '</span>'

                            # Mark erroneous button
                            sourceids = []
                            idtypes = []
                            for alias in row['source'].split(','):
                                for source in catalog[entry]['sources']:
                                    if source['alias'] == alias:
                                        if 'bibcode' in source:
                                            sourceids.append(source['bibcode'])
                                            idtypes.append('bibcode')
                                        else:
                                            sourceids.append(source['name'])
                                            idtypes.append('name')
                            if not sourceids or not idtypes:
                                raise(ValueError(
                                    'Unable to find associated source by alias!'))
                            edit = "true" if os.path.isfile(
                                'astrocats/supernovae/input/sne-internal/' + get_event_filename(entry) + '.json') else "false"
                            keyhtml = (keyhtml + "<span class='singletooltiptext'><button class='singlemarkerror' type='button' onclick='markError(\"" +
                                       entry + "\", \"" + key + "\", \"" + ','.join(idtypes) +
                                       "\", \"" + ','.join(sourceids) + "\", \"" + edit + "\")'>Flag as erroneous</button></span>")
                            keyhtml = keyhtml + r'</div><sup>' + sourcehtml + r'</sup>'
                        elif isinstance(row, str):
                            keyhtml = keyhtml + \
                                (r'<br>' if r > 0 else '') + row.strip()

                if keyhtml:
                    newhtml = (newhtml + r'<tr><td class="event-cell">' + eventpageheader[key] +
                               r'</td><td width=250px class="event-cell">' + keyhtml)

                newhtml = newhtml + r'</td></tr>\n'
        newhtml = newhtml + r'</table><em>Values that are colored <span class="derived">purple</span> were computed by the OSC using values provided by the specified sources.</em></div>\n\1'
        html = re.sub(r'(\<\/body\>)', newhtml, html)

        if 'sources' in catalog[entry] and len(catalog[entry]['sources']):
            newhtml = r'<div class="event-tab-div"><h3 class="event-tab-title">Sources of data</h3><table class="event-table"><tr><th width=30px class="event-cell">ID</th><th class="event-cell">Source Info</th></tr><tr><th colspan="2" class="event-cell">Primary Sources</th></tr>\n'
            first_secondary = False
            for source in catalog[entry]['sources']:
                biburl = ''
                if 'bibcode' in source:
                    biburl = 'http://adsabs.harvard.edu/abs/' + \
                        source['bibcode']

                refurl = ''
                if 'url' in source:
                    refurl = source['url']

                sourcename = source[
                    'name'] if 'name' in source else source['bibcode']
                if not first_secondary and source.get('secondary', False):
                    first_secondary = True
                    newhtml += r'<tr><th colspan="2" class="event-cell">Secondary Sources</th></tr>\n'
                newhtml = (newhtml + r'<tr><td class="event-cell" id="source' + source['alias'] + '">' + source['alias'] +
                           r'</td><td width=250px class="event-cell">' +
                           ((((r'<a href="' + refurl + '">') if refurl else '') + sourcename.encode('ascii', 'xmlcharrefreplace').decode("utf-8") +
                             ((r'</a>\n') if refurl else '') + r'<br>') if 'bibcode' not in source or sourcename != source['bibcode'] else '') +
                           ((source['reference'] + r'<br>') if 'reference' in source else '') +
                           ((r'\n[' + (('<a href="' + biburl + '">') if 'reference' in source else '') + source['bibcode'] +
                             (r'</a>' if 'reference' in source else '') + ']') if 'bibcode' in source else '') +
                           r'</td></tr>\n')
            newhtml = newhtml + r'</table><em>Sources are presented in order of importation, not in order of importance.</em></div>\n'

            if hasimage:
                newhtml = newhtml + \
                    '<div class="event-host-div"><h3 class="event-host-title">Host Image</h3>' + skyhtml
                newhtml = newhtml + \
                    r'</table><em>Host images are taken from SDSS if available; if not, DSS is used.</em></div>\n'

        newhtml = newhtml + r'\n\1'

        html = re.sub(r'(\<\/body\>)', newhtml, html)

        with gzip.open(outdir + htmldir + fileeventname + ".html.gz", 'wt') as fff:
            touch(outdir + htmldir + fileeventname + ".html")
            fff.write(html)

    # Necessary to clear Bokeh state
    reset_output()

    # if spectraavail and dohtml:
    #    sys.exit()

    # if fcnt > 100:
    #    sys.exit()

    # Save this stuff because next line will delete it.
    if args.writecatalog:
        # Construct array for Bishop's webpage
        # Things David wants in this file: names (aliases), max mag, max mag
        # date (gregorian), type, redshift (helio), redshift (host), r.a.,
        # dec., # obs., link
        snepages.append([entry, ",".join([x['value'] for x in catalog[entry]['alias']]), get_first_value(entry, 'maxappmag'), get_first_value(entry, 'maxdate'),
                         get_first_value(entry, 'claimedtype'), get_first_value(
                             entry, 'redshift'), get_first_kind(entry, 'redshift'),
                         get_first_value(entry, 'ra'), get_first_value(entry, 'dec'), catalog[entry]['numphoto'], 'https://sne.space/' + plotlink])

        if 'sources' in catalog[entry]:
            lsourcedict = {}
            for sourcerow in catalog[entry]['sources']:
                if 'name' not in sourcerow:
                    continue
                strippedname = re.sub(
                    '<[^<]+?>', '', sourcerow['name'].encode('ascii', 'xmlcharrefreplace').decode("utf-8"))
                alias = sourcerow['alias']
                if 'bibcode' in sourcerow and 'secondary' not in sourcerow:
                    lsourcedict[alias] = {
                        'bibcode': sourcerow['bibcode'], 'count': 0}
                if strippedname in sourcedict:
                    sourcedict[strippedname] += 1
                else:
                    sourcedict[strippedname] = 1

            for key in catalog[entry].keys():
                if isinstance(catalog[entry][key], list):
                    for row in catalog[entry][key]:
                        if 'source' in row:
                            for lsource in lsourcedict:
                                if lsource in row['source'].split(','):
                                    if key == 'spectra':
                                        lsourcedict[lsource]['count'] += 10
                                    else:
                                        lsourcedict[lsource]['count'] += 1

            ssources = sorted(list(lsourcedict.values()),
                              key=lambda x: x['count'], reverse=True)
            if ssources:
                seemorelink = ''
                catalog[entry]['references'] = ','.join(
                    [y['bibcode'] for y in ssources[:5]])

        lcspye.append(catalog[entry]['numphoto'] >=
                      5 and catalog[entry]['numspectra'] > 0)
        lconly.append(catalog[entry]['numphoto'] >=
                      5 and catalog[entry]['numspectra'] == 0)
        sponly.append(catalog[entry]['numphoto'] <
                      5 and catalog[entry]['numspectra'] > 0)
        lcspno.append(catalog[entry]['numphoto'] <
                      5 and catalog[entry]['numspectra'] == 0)

        hasalc.append(catalog[entry]['numphoto'] >= 5)
        hasasp.append(catalog[entry]['numspectra'] > 0)

        totalphoto += catalog[entry]['numphoto']
        totalspectra += catalog[entry]['numspectra']

        # Delete unneeded data from catalog, add blank entries when data
        # missing.
        catalogcopy[entry] = OrderedDict()
        for col in columnkey:
            if col in catalog[entry]:
                catalogcopy[entry][col] = deepcopy(catalog[entry][col])
            else:
                catalogcopy[entry][col] = None

    del catalog[entry]

    if args.test and spectraavail and photoavail:
        break

# Write it all out at the end
if args.writecatalog and not args.eventlist:
    catalog = deepcopy(catalogcopy)

    # Write the MD5 checksums
    jsonstring = json.dumps(md5dict, indent='\t', separators=(',', ':'))
    with open(outdir + cachedir + 'md5s.json' + testsuffix, 'w') as f:
        f.write(jsonstring)

    # Write the host image info
    if args.collecthosts:
        jsonstring = json.dumps(
            hostimgdict, indent='\t', separators=(',', ':'))
        with open(outdir + cachedir + 'hostimgs.json' + testsuffix, 'w') as f:
            f.write(jsonstring)

    if not args.boneyard:
        # Things David wants in this file: names (aliases), max mag, max mag
        # date (gregorian), type, redshift, r.a., dec., # obs., link
        with open(outdir + htmldir + 'snepages.csv' + testsuffix, 'w') as f:
            csvout = csv.writer(f, quotechar='"', quoting=csv.QUOTE_ALL)
            for row in snepages:
                csvout.writerow(row)

        # Make a few small files for generating charts
        with open(outdir + htmldir + 'sources.csv' + testsuffix, 'w') as f:
            sortedsources = sorted(
                list(sourcedict.items()), key=operator.itemgetter(1), reverse=True)
            csvout = csv.writer(f)
            csvout.writerow(['Source', 'Number'])
            for source in sortedsources:
                csvout.writerow(source)

        with open(outdir + htmldir + 'pie.csv' + testsuffix, 'w') as f:
            csvout = csv.writer(f)
            csvout.writerow(['Category', 'Number'])
            csvout.writerow(['Has light curve and spectra', sum(lcspye)])
            csvout.writerow(['Has light curve only', sum(lconly)])
            csvout.writerow(['Has spectra only', sum(sponly)])
            csvout.writerow(['No light curve or spectra', sum(lcspno)])

        with open(outdir + htmldir + 'info-snippets/hasphoto.html' + testsuffix, 'w') as f:
            f.write("{:,}".format(sum(hasalc)))
        with open(outdir + htmldir + 'info-snippets/hasspectra.html' + testsuffix, 'w') as f:
            f.write("{:,}".format(sum(hasasp)))
        with open(outdir + htmldir + 'info-snippets/snecount.html' + testsuffix, 'w') as f:
            f.write("{:,}".format(len(catalog)))
        with open(outdir + htmldir + 'info-snippets/photocount.html' + testsuffix, 'w') as f:
            f.write("{:,}".format(totalphoto))
        with open(outdir + htmldir + 'info-snippets/spectracount.html' + testsuffix, 'w') as f:
            f.write("{:,}".format(totalspectra))

        ctypedict = dict()
        for entry in catalog:
            cleanedtype = ''
            if 'claimedtype' in catalog[entry] and catalog[entry]['claimedtype']:
                maxsources = 0
                for ct in catalog[entry]['claimedtype']:
                    sourcecount = len(ct['source'].split(','))
                    if sourcecount > maxsources:
                        maxsources = sourcecount
                        cleanedtype = ct['value'].strip('?* ')
            if not cleanedtype:
                cleanedtype = 'Unknown'
            if cleanedtype in ctypedict:
                ctypedict[cleanedtype] += 1
            else:
                ctypedict[cleanedtype] = 1
        sortedctypes = sorted(list(ctypedict.items()),
                              key=operator.itemgetter(1), reverse=True)
        with open(outdir + htmldir + 'types.csv' + testsuffix, 'w') as f:
            csvout = csv.writer(f)
            csvout.writerow(['Type', 'Number'])
            for ctype in sortedctypes:
                csvout.writerow(ctype)

        with open(outdir + htmldir + 'sitemap.xml', 'w') as f:
            sitemapxml = sitemaptemplate
            sitemaplocs = ''
            for key in catalog.keys():
                sitemaplocs = sitemaplocs + "  <url>\n    <loc>https://sne.space/sne/" + \
                    key + "</loc>\n  </url>\n"
            sitemapxml = sitemapxml.replace('{0}', sitemaplocs)
            f.write(sitemapxml)

        # Ping Google to let them know sitemap has been updated
        response = urllib.request.urlopen(googlepingurl)

    # Prune extraneous fields not required for main catalog file
    catalogcopy = OrderedDict()
    for entry in catalog:
        catalogcopy[entry] = OrderedDict()
        for col in catalog[entry]:
            catalogcopy[entry][col] = deepcopy(catalog[entry][col])
            if catalogcopy[entry][col]:
                for row in catalogcopy[entry][col]:
                    if 'source' in row:
                        del row['source']
                    if 'u_value' in row:
                        del row['u_value']
    catalog = deepcopy(catalogcopy)

    # Convert to array since that's what datatables expects
    catalog = list(catalog.values())

    if args.boneyard:
        catprefix = 'bones'
    else:
        catprefix = 'catalog'

    jsonstring = json.dumps(catalog, separators=(',', ':'))
    with open(outdir + catprefix + '.min.json' + testsuffix, 'w') as f:
        f.write(jsonstring)

    jsonstring = json.dumps(catalog, indent='\t', separators=(',', ':'))
    with open(outdir + catprefix + '.json' + testsuffix, 'w') as f:
        f.write(jsonstring)

    with open(outdir + htmldir + 'table-templates/' + catprefix + '.html' + testsuffix, 'w') as f:
        f.write('<table id="example" class="display" cellspacing="0" width="100%">\n')
        f.write('\t<thead>\n')
        f.write('\t\t<tr>\n')
        for h in header:
            f.write('\t\t\t<th class="' + h + '" title="' +
                    titles[h] + '">' + header[h] + '</th>\n')
        f.write('\t\t</tr>\n')
        f.write('\t</thead>\n')
        f.write('\t<tfoot>\n')
        f.write('\t\t<tr>\n')
        for h in header:
            f.write('\t\t\t<th class="' + h + '" title="' +
                    titles[h] + '">' + header[h] + '</th>\n')
        f.write('\t\t</tr>\n')
        f.write('\t</tfoot>\n')
        f.write('</table>\n')

    with open(outdir + catprefix + '.min.json', 'rb') as f_in, gzip.open(outdir + catprefix + '.min.json.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    if not args.boneyard:
        names = OrderedDict()
        for ev in catalog:
            names[ev['name']] = [x['value'] for x in ev['alias']]
        jsonstring = json.dumps(names, separators=(',', ':'))
        with open(outdir + 'names.min.json' + testsuffix, 'w') as f:
            f.write(jsonstring)

    if args.deleteorphans and not args.boneyard:

        safefiles = [os.path.basename(x) for x in files]
        safefiles += ['catalog.json', 'catalog.min.json', 'bones.json', 'bones.min.json', 'names.min.json', 'md5s.json', 'hostimgs.json', 'iaucs.json', 'errata.json',
                      'bibauthors.json', 'extinctions.json', 'dupes.json', 'biblio.json', 'atels.json', 'cbets.json', 'conflicts.json', 'hosts.json', 'hosts.min.json']

        for myfile in glob(outdir + jsondir + '*.json'):
            if not os.path.basename(myfile) in safefiles:
                print('Deleting orphan ' + myfile)
                # os.remove(myfile)
