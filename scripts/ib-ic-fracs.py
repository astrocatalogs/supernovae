#!/usr/local/bin/python3.5

import gzip
import json
import os
from collections import OrderedDict

from tqdm import tqdm

from utils.repos import get_repo_output_file_list
from utils.tq_funcs import tprint


def get_event_filename(name):
    return(name.replace('/', '_'))

files = get_repo_output_file_list(bones=False)

spectracount = 0
photocount = 0
eventswithspectra = 0
eventswithphoto = 0

years = range(1950, 2020, 5)
ibs = [0 for x in years]
ics = [0 for x in years]

for fcnt, eventfile in enumerate(tqdm(sorted(files, key=lambda s: s.lower()))):
    # if fcnt > 1000:
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
    namekey = list(item.keys())[0]
    item = item[namekey]
    tprint(namekey)

    if 'claimedtype' in item and 'maxdate' in item:
        maxyear = int(item['maxdate'][0]['value'].split('/')[0])
        for yi, year in enumerate(years):
            if maxyear <= years[yi]:
                for ct in item['claimedtype']:
                    if ct['value'] == "Ic":
                        ics[yi] += 1
                    elif ct['value'] == "Ib":
                        ibs[yi] += 1
                break

print(list(years))
print(ics)
print(ibs)
print([float(x) / max(y, 1) for x, y in zip(ics, ibs)])
