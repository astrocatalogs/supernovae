import gzip
import json
import math
import os
from collections import OrderedDict
from copy import deepcopy

from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from tqdm import tqdm

from astrocats.supernovae.scripts.repos import repo_file_list

from ...catalog.utils import get_entry_filename, is_number

dupes = []

outdir = "astrocats/supernovae/output/"

files = repo_file_list(bones=False)

newcatalog = []

for fcnt, eventfile in enumerate(
        tqdm(sorted(files, key=lambda s: s.lower()))):
    #if fcnt > 5000:
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

    if 'maxdate' in item and item['maxdate']:
        date = item['maxdate'][0]['value'].replace('/', '-')
        negdate = date.startswith('-')
        datesplit = date.lstrip('-').split('-')
        if len(datesplit) >= 1:
            if '<' in datesplit[0]:
                print(item['name'])
                datesplit[0] = datesplit[0].strip('<')
            maxyear = float(datesplit[0])
        if len(datesplit) >= 2:
            maxyear += float(datesplit[1]) / 12.
        if len(datesplit) >= 3:
            maxyear += float(datesplit[2]) / (12. * 30.)
        if negdate:
            maxyear = -maxyear
        newitem['maxyear'] = maxyear
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
    if 'ra' in item and 'dec' in item and item['ra'] and item['dec']:
        newitem['name'] = item['name']
        newitem['alias'] = [x['value'] for x in item.get('alias', [{'value': item['name']}])]
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
cooref = list(range(len(coo)))

newcatalog2 = deepcopy(newcatalog)

for i1, item1 in enumerate(tqdm(newcatalog)):
    name1 = item1['name']

    maxyear1 = None
    if 'maxyear' in item1 and item1['maxyear']:
        maxyear1 = item1['maxyear']
    discyear1 = None
    if 'discyear' in item1 and item1['discyear']:
        discyear1 = item1['discyear']

    distdegs = coo[i1+1:].separation(coo[i1]).arcsecond

    lcooref = deepcopy(cooref)

    for i2, item2 in enumerate(newcatalog2[i1+1:]):
        name2 = item2['name']

        aliases1 = item1['alias']
        aliases2 = item2['alias']

        distinctfrom1 = item1[
            'distinctfrom'] if 'distinctfrom' in item1 else []
        distinctfrom2 = item2[
            'distinctfrom'] if 'distinctfrom' in item2 else []

        if (len(set(aliases1).intersection(distinctfrom2))):
            tqdm.write('Found ' + name2 +
                       ' in distinct from list of ' + name1 + '.')
            continue
        if (len(set(aliases2).intersection(distinctfrom1))):
            tqdm.write('Found ' + name1 +
                       ' in distinct from list of ' + name2 + '.')
            continue

        maxyear2 = None
        if 'maxyear' in item2 and item2['maxyear']:
            maxyear2 = item2['maxyear']
        discyear2 = None
        if 'discyear' in item2 and item2['discyear']:
            discyear2 = item2['discyear']

        ra1 = item1['ra']
        ra2 = item2['ra']
        dec1 = item1['dec']
        dec2 = item2['dec']
        poserr1 = math.hypot(item1['raerr'], item1['decerr'])
        poserr2 = math.hypot(item2['raerr'], item2['decerr'])

        maxdiffyear = ''
        discdiffyear = ''

        distdeg = distdegs[i2]
        exactstr = ('exact' if distdeg == 0.0 else 'a close')

        if distdeg < (10. + (poserr1 + poserr2) / 3600.):
            if (maxyear1 and maxyear2) or (discyear1 and discyear2):
                if maxyear1 and maxyear2:
                    maxdiffyear = abs(maxyear1 - maxyear2)
                if discyear1 and discyear2:
                    discdiffyear = abs(discyear1 - discyear2)

                if maxdiffyear and maxdiffyear <= 2.0:
                    tqdm.write(name1 + ' has ' + exactstr +
                               ' coordinate and maximum date match to ' +
                               name2 + " [" + str(distdeg) + ', ' +
                               str(maxdiffyear) + ']')
                elif discdiffyear and discdiffyear <= 2.0:
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
                        ((', Max. diff: ' + str(maxdiffyear)) if
                         maxdiffyear else '') +
                        ((', Disc. diff: ' + str(discdiffyear)) if
                         discdiffyear else '') + ']')
                    continue
            else:
                tqdm.write(name1 + ' has ' + exactstr +
                           ' coordinate match to ' + name2 + " [" +
                           str(distdeg) + "]")
            if (not name1.startswith(('SN', 'AT')) and
                name2.startswith(('SN', 'AT')) or
                (discyear1 and discyear2 and discyear2 < discyear1 and
                 not name1.startswith(('SN', 'AT'))) or
                    (maxyear1 and maxyear2 and maxyear2 < maxyear1 and
                     not name1.startswith(('SN', 'AT')))):
                name1, name2 = name2, name1
                aliases1, aliases2 = aliases2, aliases1
                ra1, ra2 = ra2, ra1
                dec1, dec2 = dec2, dec1
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
                                  ('distdeg', str(distdeg)),
                                  ('maxdiffyear', str(maxdiffyear)),
                                  ('discdiffyear', str(discdiffyear)),
                                  ('edit', edit)]))

jsonstring = json.dumps(
    dupes, indent='\t', separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'dupes.json', 'w') as f:
    f.write(jsonstring)
