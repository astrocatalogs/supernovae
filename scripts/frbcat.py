import gzip
import json
import math
import os
import urllib

import numpy as np

from collections import OrderedDict
from copy import deepcopy

from astropy.io.ascii import read
from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from tqdm import tqdm

from astrocats.supernovae.scripts.repos import repo_file_list

from ...catalog.utils import get_entry_filename, is_number

dupes = []

outdir = "astrocats/supernovae/output/"

utmost = "astrocats/supernovae/scripts/UTMOST-FRBs.dat"

files = repo_file_list(bones=False)

newcatalog = []

for fcnt, eventfile in enumerate(
        tqdm(sorted(files, key=lambda s: s.lower()))):
    #if fcnt > 1000:
    #   break

    if eventfile.split('.')[-1] == 'gz':
        with gzip.open(eventfile, 'rt') as f:
            filetext = f.read()
    else:
        with open(eventfile, 'r') as f:
            filetext = f.read()

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    item = item[list(item.keys())[0]]
    newitem = OrderedDict()

    if 'discoverdate' in item and item['discoverdate']:
        date = item['discoverdate'][0]['value'].replace('/', '-')
        negdate = date.startswith('-')
        datesplit = date.lstrip('-').split('-')
        if len(datesplit) >= 1:
            if '<' in datesplit[0]:
                print(item['name'])
                datesplit[0] = datesplit[0].strip('<')
            discyear = float(datesplit[0])
        if len(datesplit) >= 2:
            discyear += float(datesplit[1]) / 12.
        if len(datesplit) >= 3:
            discyear += float(datesplit[2]) / (12. * 30.)
        if negdate:
            discyear = -discyear
        newitem['discyear'] = discyear
    if 'claimedtype' in item:
        newitem['claimedtype'] = item['claimedtype'][0]['value']
    if 'host' in item:
        newitem['host'] = item['host']
    if 'ra' in item and 'dec' in item and item['ra'] and item['dec']:
        newitem['name'] = item['name']
        newitem['alias'] = [x['value'] for x in item.get('alias', [])]
        if not len(newitem['alias']):
            newitem['alias'] = [item['name']]
        newitem['ra'] = item['ra'][0]['value']
        if not is_number(newitem['ra'].split(':')[0]):
            continue
        newitem['dec'] = item['dec'][0]['value']
        if not is_number(newitem['dec'].split(':')[0]):
            continue
        newitem['raerr'] = float(item['ra'][0].get('e_value', 0))
        newitem['decerr'] = float(item['dec'][0].get('e_value', 0))
        # Temporary fix for David's typo
        if newitem['dec'].count('.') == 2:
            newitem['dec'] = newitem['dec'][:newitem['dec'].rfind('.')]
        if 'distinctfrom' in item:
            newitem['distinctfrom'] = [x['value']
                                       for x in item['distinctfrom']]
        newcatalog.append(newitem)

coo = coord([x['ra'] for x in newcatalog],
            [x['dec'] for x in newcatalog], unit=(un.hourangle, un.deg))

response = urllib.request.urlopen('http://www.astronomy.swin.edu.au/pulsar/frbcat/table.php?format=text&sep=comma')

frbtxt = response.read().decode('utf-8').splitlines()

with open(utmost, 'r') as f:
    utmosttable = f.read().splitlines()

frbcatalog = []
frbnames = []
utmostcoords = {}
for row in utmosttable:
    if row[0] == '#':
        frbname = row[1:].strip()
        utmostcoords[frbname] = []
    else:
        frbnames.append(frbname)
        ra, dec, prob = row.split()
        utmostcoords[frbname].append([float(ra), float(dec)])

for frb in utmostcoords:
    ras, decs = zip(*(utmostcoords[frbname]))

    frbc1 = coord(ra=ras[0], dec=decs[0], unit=(un.hourangle, un.deg))
    frbc2 = coord(ra=ras[-1], dec=decs[-1], unit=(un.hourangle, un.deg))
    frblength = frbc1.separation(frbc2).arcsecond

    nras = np.linspace(ras[0], ras[1], np.round(frblength/30.0))
    ndecs = np.interp(nras, ras, decs)

    ncoo = [nras, ndecs] 
    for ra, dec in zip(*ncoo):
        frbc = coord(ra=ra, dec=dec, unit=(un.hourangle, un.deg))
        radecstr = frbc.to_string('hmsdms').replace('h', ':').replace('m', ':').replace('s', '').replace('d', ':').replace('+', '')
        ra, dec = radecstr.split()
        datesplit = '20' + frb[-6:-4], frb[-4:-2], frb[-2:]
        if len(datesplit) >= 1:
            discyear = float(datesplit[0])
        if len(datesplit) >= 2:
            discyear += float(datesplit[1]) / 12.
        if len(datesplit) >= 3:
            discyear += float(datesplit[2]) / (12. * 30.)
        frbdict = {
            'name': frb,
            'alias': [frb],
            'discyear': discyear,
            'ra': ra,
            'dec': dec,
            'raerr': 30,
            'decerr': 30
        }
        frbcatalog.append(frbdict)

frbtable = read(frbtxt, format='csv')
for row in frbtable:
    name = row[0]
    if name in frbnames:
        continue
    frbnames.append(name)
    datesplit = row[3].split(' ')[0].split('-')
    if len(datesplit) >= 1:
        discyear = float(datesplit[0])
    if len(datesplit) >= 2:
        discyear += float(datesplit[1]) / 12.
    if len(datesplit) >= 3:
        discyear += float(datesplit[2]) / (12. * 30.)
    frbdict = {
        'name': name,
        'alias': [name],
        'discyear': discyear,
        'ra': row[7],
        'dec': row[8],
        'raerr': 60*float(row[10])/2.355,
        'decerr': 60*float(row[10])/2.355
    }
    frbcatalog.append(frbdict)

for item1 in tqdm(frbcatalog):
    name1 = item1['name']

    discyear1 = None
    if 'discyear' in item1 and item1['discyear']:
        discyear1 = item1['discyear']

    frbra = item1['ra']
    frbdec = item1['dec']

    aliases1 = item1['alias']
    ra1 = item1['ra']
    dec1 = item1['dec']

    frbc = coord(ra=frbra, dec=frbdec, unit=(un.hourangle, un.deg))
    distdegs = coo.separation(frbc).arcsecond

    for i2, item2 in enumerate(newcatalog[:]):
        name2 = item2['name']
        if name1 == name2:
            newcatalog.remove(item2)
            continue

        aliases2 = item2['alias']

        discyear2 = None
        if 'discyear' in item2 and item2['discyear']:
            discyear2 = item2['discyear']

        ct2 = ''
        if 'claimedtype' in item2:
            ct2 = item2['claimedtype']
        ho2 = ''
        if 'host' in item2:
            ho2 = item2['host']
        ra2 = item2['ra']
        dec2 = item2['dec']
        poserr1 = math.hypot(item1['raerr'], item1['decerr'])
        poserr2 = math.hypot(item2['raerr'], item2['decerr'])

        if poserr2 > 3000:
            continue

        discdiffyear = ''

        exactstr = 'a close'

        distdeg = distdegs[i2]
        if distdeg < 4.0 * (poserr1 + poserr2):
            if discyear1 and discyear2:
                if discyear1 and discyear2:
                    discdiffyear = discyear1 - discyear2

                elif discdiffyear and abs(discdiffyear) <= 2.0:
                    tqdm.write(name1 + ' has ' + exactstr +
                               ' coordinate and discovery date match to ' +
                               name2 + " [" + str(distdeg) + ', ' +
                               str(discdiffyear) + ']')
                else:
                    tqdm.write(
                        name1 + ' has ' + exactstr +
                        ' coordinate, but significantly different ' +
                        'date, to ' + name2 + " [Deg. diff: " +
                        str(distdeg) +
                        ((', Disc. diff: ' + str(discdiffyear)) if
                         discdiffyear else '') + ']')
            else:
                tqdm.write(name1 + ' has ' + exactstr +
                           ' coordinate match to ' + name2 + " [" +
                           str(distdeg) + "]")
        else:
            continue

        edit = True if os.path.isfile(
            '../sne-internal/' + get_entry_filename(name1) +
            '.json') else False

        dupes.append(OrderedDict([('name1', name1),
                                  ('aliases1', aliases1),
                                  ('name2', name2),
                                  ('aliases2', aliases2), ('ra1', ra1),
                                  ('dec1', dec1),
                                  ('ra2', ra2), ('dec2', dec2),
                                  ('distdeg', str(distdeg/3600.)),
                                  ('discdiffyear', str(discdiffyear)),
                                  ('poserror', str(poserr1 + poserr2)),
                                  ('claimedtype', ct2),
                                  ('host', ho2),
                                  ('edit', edit)]))

# Convert to array since that's what datatables expects
jsonstring = json.dumps(
    dupes, indent='\t', separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'frbs.json', 'w') as f:
    f.write(jsonstring)
