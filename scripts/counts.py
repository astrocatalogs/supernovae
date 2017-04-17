
import gzip
import json
import os
from collections import OrderedDict

from tqdm import tqdm

from repos import repo_file_list

files = repo_file_list(bones=False)

spectracount = 0
photocount = 0
eventswithspectra = 0
eventswithphoto = 0

for fcnt, eventfile in enumerate(tqdm(sorted(files, key=lambda s: s.lower()))):
    # if fcnt > 100:
    #    break
    fileeventname = os.path.splitext(os.path.basename(eventfile))[
        0].replace('.json', '')

    if os.path.isfile(eventfile):
        if eventfile.split('.')[-1] == 'gz':
            with gzip.open(eventfile, 'rt') as f:
                filetext = f.read()
        else:
            with open(eventfile, 'r') as f:
                filetext = f.read()

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    namekey = list(item.keys())[0]
    item = item[namekey]

    if namekey != item['name']:
        tqdm.write(
            namekey + ' has different name from its key ' + item['name'])

    if 'spectra' in item:
        eventswithspectra += 1
        spectracount += len(item['spectra'])

    if 'photometry' in item:
        eventswithphoto += 1
        photocount += len(item['photometry'])

print('Event count: ' + str(len(files)))
print('Events with spectra: ' + str(eventswithspectra))
print('Events with photometry: ' + str(eventswithphoto))
print('Total spectra: ' + str(spectracount))
print('Total photometry: ' + str(photocount))
