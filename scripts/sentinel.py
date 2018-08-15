
import gzip
import json
import os
from collections import OrderedDict

import ads

from astrocats.utils import tprint, tq, listify
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

specterms = [
    "spectrum", "spectra", "spectroscopic", "spectroscopy"]

photterms = [
    "photometry", "photometric", "light curve"]

for fcnt, eventfile in enumerate(tq(sorted(files, key=lambda s: s.lower()))):
    #if fcnt > 3000:
    #   break
    if not os.path.exists(eventfile):
        continue

    fileeventname = os.path.splitext(os.path.basename(eventfile))[0].replace(
        '.json', '').replace('.gz', '')

    if eventfile.split('.')[-1] == 'gz':
        with gzip.open(eventfile, 'rt') as f:
            filetext = f.read()
    else:
        with open(eventfile, 'r') as f:
            filetext = f.read()

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    item = item[list(item.keys())[0]]

    hasspecred = False
    hasspectype = False
    if 'spectra' not in item:
        if 'redshift' in item:
            redshiftkinds = [x for y in [listify(x.get('kind', '')) for x in item['redshift']] for x in y]
            if any([any(
                [y == x for y in ['cmb', 'heliocentric', 'spectroscopic', 'host', '']])
                    for x in redshiftkinds]):
                hasspecred = True

        if 'claimedtype' in item:
            typekinds = ['candidate'
                         if x['value'].lower() == 'candidate' else x.get('kind', '')
                         for x in item['claimedtype']]
            if any([any([y == x for y in ['spectroscopic', '']])
                    for x in typekinds]):
                hasspectype = True

    search_spectra = hasspecred or hasspectype
    search_photometry = len(item.get('photometry', [])) <= 3

    # Optionally ignore spectra
    # search_spectra = False

    if not search_photometry and not search_spectra:
        continue

    try:
        aliases = [
            x['value'] for x in item['alias']
            if (not any([y in x['value'] for y in ['GRB', 'SNR', 'SDSS-II']])
                and len(x['value']) >= 5)]
        if not aliases:
            continue
        # ADS treats queries with spaces differently, so must search for both
        # variations.
        for alias in aliases[:]:
            if alias.startswith('SN'):
                aliases.append('SN ' + alias[2:])
        qstr = 'full:(="' + '" or "'.join(aliases) + '") '
        qstr += 'and property:refereed and full:('
        terms = []
        if search_spectra:
            terms += specterms
        if search_photometry:
            terms += photterms
        qstr += '"' + '" or "'.join(terms) + '")'
        allpapers = ads.SearchQuery(
            q=qstr, fl=['id', 'bibstem', 'bibcode', 'author'], max_pages=100)
    except:
        print('ADS query failed for {}, skipping'.format(fileeventname))
        continue

    try:
        npapers = 0
        for paper in allpapers:
            if paper.bibstem in ['ATel', 'CBET', 'IAUC']:
                tprint('ignored bibstem')
                continue
            bc = paper.bibcode
            if bc not in sentinel:
                allauthors = paper.author
                sentinel[bc] = OrderedDict([('bibcode', bc), (
                    'allauthors', allauthors), ('events', [])])
            sentinel[bc]['events'].append(fileeventname)
            npapers += 1
        if not npapers:
            continue
        if int(rate_limits['remaining']) <= 10:
            print('ADS API limit reached, terminating early.')
            break

        rate_limits = allpapers.response.get_ratelimits()

        tprint('{:<30} (papers found: {}, remaining API calls: {})'.format(
            fileeventname, npapers, rate_limits['remaining']))
    except Exception as e:
        print(repr(e))
        print('Failed to parse ADS output for {}, skipping'.format(fileeventname))
        print(allpapers.response.get_ratelimits())
        continue

# Convert to array since that's what datatables expects
sentinel = list(sentinel.values())
jsonstring = json.dumps(
    sentinel, indent='\t', separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'sentinel.json', 'w') as f:
    f.write(jsonstring)
