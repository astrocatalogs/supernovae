
import gzip
import json
import os
import warnings
from collections import OrderedDict

from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from astroquery.simbad import Simbad
from tqdm import tqdm

from astrocats.supernovae.scripts.repos import repo_file_list

from ...catalog.utils import get_entry_filename

events = OrderedDict()

warnings.filterwarnings('ignore')

outdir = "astrocats/supernovae/output/"

files = repo_file_list(bones=False)

newcatalog = []

# Simbad.list_votable_fields()
# sys.exit()
for fcnt, eventfile in enumerate(tqdm(sorted(files, key=lambda s: s.lower()))):
    if fcnt > 2000:
        break
    fileeventname = os.path.splitext(os.path.basename(eventfile))[
        0].replace('.json', '')

    if eventfile.split('.')[-1] == 'gz':
        with gzip.open(eventfile, 'rt') as f:
            filetext = f.read()
    else:
        with open(eventfile, 'r') as f:
            filetext = f.read()

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    item = item[list(item.keys())[0]]
    newitem = OrderedDict()

    if ('redshift' in item and 'host' not in item and 'ra' in item and
            'dec' in item and item['ra'] and item['dec']):
        # if 'ra' in item and 'dec' in item and item['ra'] and item['dec']:
        newitem['name'] = item['name']
        newitem['alias'] = [x['value'] for x in item['alias']]
        newitem['ra'] = item['ra'][0]['value']
        newitem['dec'] = item['dec'][0]['value']
        if 'redshift' in item:
            newitem['redshift'] = item['redshift'][0]['value']
        # Temporary fix for David's typo
        if newitem['dec'].count('.') == 2:
            newitem['dec'] = newitem['dec'][:newitem['dec'].rfind('.')]
        newcatalog.append(newitem)

coo = coord([x['ra'] for x in newcatalog],
            [x['dec'] for x in newcatalog], unit=(un.hourangle, un.deg))

for ci, co in enumerate(tqdm(coo)):
    customSimbad = Simbad()
    customSimbad.add_votable_fields('otype', 'z_value')
    regstr = 'region(ICRS, ' + co.to_string('hmsdms') + ', 1m)'
    print(regstr)

    result_table = customSimbad.query_criteria(regstr, otype='Galaxy')
    if result_table:
        print(newcatalog[ci])
        if 'redshift' in newcatalog[ci]:
            print(newcatalog[ci]['redshift'])
        print(result_table)

# Convert to array since that's what datatables expects
dupes = list(dupes.values())
jsonstring = json.dumps(dupes, indent='\t', separators=(',', ':'),
                        ensure_ascii=False)
with open(outdir + 'hostcandidates.json', 'w') as f:
   f.write(jsonstring)
