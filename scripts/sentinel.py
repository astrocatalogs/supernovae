#!/usr/local/bin/python3.5

import gzip
import json
import os
from collections import OrderedDict
from tqdm import tqdm

import ads
from astropy.time import Time as astrotime

from astrocats.supernovae.scripts.repos import repo_file_list
from astrocats.catalog.utils import tq

biblio = OrderedDict()

outdir = 'astrocats/supernovae/output/'

path = 'astrocats/supernovae/output/cache/bibauthors.json'
if os.path.isfile(path):
    with open(path, 'r') as f:
        bibauthordict = json.loads(f.read(), object_pairs_hook=OrderedDict)
else:
    bibauthordict = OrderedDict()

files = repo_file_list(bones=False)

path = 'ads.key'
if os.path.isfile(path):
    with open(path, 'r') as f:
        ads.config.token = f.read().splitlines()[0]
else:
    raise IOError(
        "Cannot find ads.key, please generate one at "
        "https://ui.adsabs.harvard.edu/#user/settings/token and place it in "
        "this file.")

for fcnt, eventfile in enumerate(tq(sorted(files, key=lambda s: s.lower()))):
    # if fcnt > 100:
    #    break
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

    if 'PTF' not in [x['value'] for x in item['alias']]:
        continue
    print(fileeventname)

# Convert to array since that's what datatables expects
# biblio = list(biblio.values())
# jsonstring = json.dumps(biblio, indent='\t',
#                         separators=(',', ':'), ensure_ascii=False)
# with open(outdir + 'biblio.json', 'w') as f:
#     f.write(jsonstring)
