#!/usr/local/bin/python3.5

import gzip
import json
import os
from collections import OrderedDict

import ads

from astrocats.catalog.utils import tq, tprint
from astrocats.supernovae.scripts.repos import repo_file_list

targets = OrderedDict()

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
    # if fcnt > 1500:
    #     break
    fileeventname = os.path.splitext(os.path.basename(eventfile))[0].replace(
        '.json', '')

    if eventfile.split('.')[-1] == 'gz':
        with gzip.open(eventfile, 'rt') as f:
            filetext = f.read()
    else:
        with open(eventfile, 'r') as f:
            filetext = f.read()

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    item = item[list(item.keys())[0]]

    if ('redshift' not in item and
            'claimedtype' not in item) or 'spectra' in item:
        continue

    try:
        q = ads.SearchQuery(q=(
            'full:"' + fileeventname + '"' + ' and property:refereed'))
        allpapers = list(q)
    except:
        continue

    if len(allpapers) > 0:
        print(q.response.get_ratelimits())

    for paper in allpapers:
        bc = paper.bibcode
        if bc not in targets:
            allauthors = []
            if allpapers and allpapers[0].author:
                allauthors = allpapers[0].author
            targets[bc] = OrderedDict(
                [('bibcode', bc), ('allauthors', allauthors), ('events', [])])
        targets[bc]['events'].append(fileeventname)

    if len(allpapers) > 0:
        tprint(fileeventname)

# Convert to array since that's what datatables expects
targets = list(targets.values())
jsonstring = json.dumps(
    targets, indent='\t', separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'targets.json', 'w') as f:
    f.write(jsonstring)
