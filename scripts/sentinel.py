
import gzip
import json
import os
from collections import OrderedDict

import ads

from astrocats.catalog.utils import tprint, tq
from astrocats.supernovae.scripts.repos import repo_file_list

sentinel = OrderedDict()

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
    # if fcnt > 10000:
    #    break
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

    # Check for likely existence of spectrum
    if 'spectra' in item:
        continue

    hasspecred = False
    if 'redshift' in item:
        redshiftkinds = [x['kind'] if 'kind' in x else ''
                         for x in item['redshift']]
        if any([any(
            [y == x for y in ['cmb', 'heliocentric', 'spectroscopic', '']])
                for x in redshiftkinds]):
            hasspecred = True

    hasspectype = False
    if 'claimedtype' in item:
        typekinds = ['candidate'
                     if x['value'] == 'Candidate' else (x['kind']
                                                        if 'kind' in x else '')
                     for x in item['claimedtype']]
        if any([any([y == x for y in ['spectroscopic', '']])
                for x in typekinds]):
            hasspectype = True

    if not hasspecred and not hasspectype:
        continue

    try:
        aliases = [
            x['value'] for x in item['alias']
            if (not any([y in x['value'] for y in ['GRB', 'SNR', 'SDSS-II']])
                and len(x['value']) >= 4)]
        if not aliases:
            continue
        # ADS treats queries with spaces differently, so must search for both
        # variations.
        for alias in aliases[:]:
            if alias.startswith('SN'):
                aliases.append('SN ' + alias[2:])
        qstr = 'full:("' + '" or "'.join(aliases) + '") '
        allpapers = ads.SearchQuery(
            q=(qstr +
               ' and property:refereed and ' +
               'full:("spectrum" or "spectra" or "spectroscopic" or ' +
               '"spectroscopy")'),
            fl=['id', 'bibcode', 'author'], max_pages=100)
    except:
        continue

    if not allpapers:
        continue

    try:
        for paper in allpapers:
            bc = paper.bibcode
            if bc not in sentinel:
                allauthors = paper.author
                sentinel[bc] = OrderedDict([('bibcode', bc), (
                    'allauthors', allauthors), ('events', [])])
            sentinel[bc]['events'].append(fileeventname)
        rate_limits = allpapers.response.get_ratelimits()
        if int(rate_limits['remaining']) <= 10:
            print('ADS API limit reached, terminating early.')
            break
        tprint(fileeventname + '\t(remaining API calls: ' + rate_limits[
            'remaining'] + ')')
    except:
        continue

# Convert to array since that's what datatables expects
sentinel = list(sentinel.values())
jsonstring = json.dumps(
    sentinel, indent='\t', separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'sentinel.json', 'w') as f:
    f.write(jsonstring)
