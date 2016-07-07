#!/usr/local/bin/python3.5

import glob
import json
from collections import OrderedDict

outdir = "../"

with open('rep-folders.txt', 'r') as f:
    repfolders = f.read().splitlines()

files = []
for rep in repfolders:
    files += glob('../' + rep + "/*.json")

for fcnt, eventfile in enumerate(sorted(files, key=lambda s: s.lower())):
    with open(eventfile, 'r') as f:
        filetext = f.read()

    thisevent = json.loads(filetext, object_pairs_hook=OrderedDict)
    thisevent = thisevent[list(thisevent.keys())[0]]

    if ('sources' in thisevent and 'claimedtype' in thisevent and
            'spectra' not in thisevent):
        wiserepalias = ''
        for source in thisevent['sources']:
            if source['name'] == 'WISeREP':
                wiserepalias = source['alias']

        if not wiserepalias:
            continue

        for ct in thisevent['claimedtype']:
            if wiserepalias in ct['source'].split(','):
                print(thisevent['name'])
                break
