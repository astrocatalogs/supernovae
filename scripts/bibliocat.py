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

    if 'sources' in item:
        for source in item['sources']:
            if 'bibcode' in source:
                bc = source['bibcode']
                if bc not in biblio:
                    tqdm.write(bc)

                    authors = ''
                    if bc in bibauthordict:
                        authors = bibauthordict[bc]

                    allauthors = list(ads.SearchQuery(bibcode=bc))
                    if allauthors and allauthors[0].author:
                        allauthors = allauthors[0].author
                    else:
                        allauthors = []
                    biblio[bc] = OrderedDict([('authors', authors),
                                              ('allauthors', allauthors),
                                              ('bibcode', bc), ('events', []),
                                              ('eventdates', []),
                                              ('types', []), ('photocount', 0),
                                              ('spectracount', 0),
                                              ('metacount', 0)])

                biblio[bc]['events'].append(item['name'])

                if 'discoverdate' in item and item['discoverdate']:
                    datestr = item['discoverdate'][
                        0]['value'].replace('/', '-')
                    if datestr.count('-') == 1:
                        datestr += '-01'
                    elif datestr.count('-') == 0:
                        datestr += '-01-01'
                    try:
                        biblio[bc]['eventdates'].append(
                            astrotime(datestr, format='isot').unix)
                    except:
                        biblio[bc]['eventdates'].append(float("inf"))
                else:
                    biblio[bc]['eventdates'].append(float("inf"))

                if 'claimedtype' in item:
                    cts = []
                    for ct in item['claimedtype']:
                        cts.append(ct['value'].strip('?'))
                    biblio[bc]['types'] = list(
                        set(biblio[bc]['types']).union(cts))

                if 'photometry' in item:
                    bcalias = source['alias']
                    lc = 0
                    for photo in item['photometry']:
                        if bcalias in photo['source'].split(','):
                            lc += 1
                    biblio[bc]['photocount'] += lc
                    # if lc > 0:
                    #    tqdm.write(str(lc))

                if 'spectra' in item:
                    bcalias = source['alias']
                    lc = 0
                    for spectra in item['spectra']:
                        if bcalias in spectra['source'].split(','):
                            lc += 1
                    biblio[bc]['spectracount'] += lc
                    # if lc > 0:
                    #    tqdm.write(str(lc))

                for key in list(item.keys()):
                    bcalias = source['alias']
                    lc = 0
                    if key in ['name', 'sources', 'schema', 'photometry',
                               'spectra', 'errors']:
                        continue
                    for quantum in item[key]:
                        if bcalias in quantum['source'].split(','):
                            lc += 1
                    biblio[bc]['metacount'] += lc

for bc in biblio:
    biblio[bc]['events'] = [x for (y, x) in sorted(
        zip(biblio[bc]['eventdates'], biblio[bc]['events']))]
    del biblio[bc]['eventdates']

# Convert to array since that's what datatables expects
biblio = list(biblio.values())
jsonstring = json.dumps(biblio, indent='\t',
                        separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'biblio.json', 'w') as f:
    f.write(jsonstring)
