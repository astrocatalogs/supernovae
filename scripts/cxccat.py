import gzip
import json
import math
import os
import requests

import numpy as np

from collections import OrderedDict
from copy import deepcopy

from astropy.io import fits
from astropy import units as un
from astropy.coordinates import SkyCoord as coord, match_coordinates_sky
from tqdm import tqdm

from astrocats.supernovae.scripts.repos import repo_file_list

from ...catalog.utils import get_entry_filename, is_number

def download_file(url, path, overwrite=False):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    local_path = os.path.join(path, local_filename)
    if os.path.isfile(local_path) and not overwrite:
        return local_path
    r = requests.get(url, stream=True)
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
                #f.flush() commented by recommendation from J.F.Sebastian
    return local_path

dupes = []

outdir = "astrocats/supernovae/output/"

files = repo_file_list(bones=False)

newcatalog = []

for fcnt, eventfile in enumerate(
        tqdm(sorted(files, key=lambda s: s.lower()))):
    if fcnt > 1000:
        break

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

path = download_file(
    'http://cxc.harvard.edu/csc2/preliminary/preliminary_detlist.fits',
    'astrocats/supernovae/output/cache')

cxctable = fits.getdata(path, 1)
cxccatalog = []
for ri, row in enumerate(tqdm(cxctable)):
    if ri > 1000:
        break
    name = row[0]
    if row[2] != 'TRUE' or row[34] != 'POINT' or row[5] == 'T':
        continue
    cxcdict = {
        'name': name,
        'alias': [name],
        'discyear': 2010.0,
        'ra': row[6],
        'dec': row[7],
        'raerr': row[8]*3600.,
        'decerr': row[9]*3600.
    }
    cxccatalog.append(cxcdict)

cxcc = coord([x['ra'] for x in newcatalog],
             [x['dec'] for x in newcatalog], unit=(un.deg, un.deg))

print('Finding coordinate overlap...')
aids = np.zeros(shape=(len(coo), 0))
adds = np.zeros(shape=(len(coo), 0))
for mi in range(2):
    print(mi)
    ids, distdegs, d3d = match_coordinates_sky(cxcc, coo)
    aids = np.concatenate((aids, np.reshape(ids, (len(ids), 1))), axis=1)
print(aids.shape)

for item1 in tqdm(cxccatalog):
    name1 = item1['name']

    discyear1 = None
    if 'discyear' in item1 and item1['discyear']:
        discyear1 = item1['discyear']

    cxcra = item1['ra']
    cxcdec = item1['dec']

    aliases1 = item1['alias']
    ra1 = item1['ra']
    dec1 = item1['dec']

    cxcc = coord(ra=cxcra, dec=cxcdec, unit=(un.deg, un.deg))
    ids, distdegs = coord.match_coordinates_sky(cxcc, coo, storekdtree='coo')

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

        discdiffyear = ''

        exactstr = 'a close'

        distdeg = distdegs[i2]
        if distdeg < 2.0 * (poserr1 + poserr2):
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
with open(outdir + 'cxcs.json', 'w') as f:
    f.write(jsonstring)
