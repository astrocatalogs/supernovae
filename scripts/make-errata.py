#!/usr/local/bin/python3.5

import json
import os
from collections import OrderedDict

from tqdm import tqdm

from events import *
from utils.repos import get_repo_output_file_list

errata = []

files = get_repo_output_file_list(bones=False)

for fcnt, eventfile in enumerate(tqdm(sorted(files, key=lambda s: s.lower()))):
    # if fcnt > 100:
    #    break
    fileeventname = os.path.splitext(os.path.basename(eventfile))[
        0].replace('.json', '')

    filetext = get_entry_text(eventfile)

    item = json.loads(filetext, object_pairs_hook=OrderedDict)
    item = item[list(item.keys())[0]]

    if 'errors' in item:
        for error in item['errors']:
            quantity = error['extra']
            likelyvalue = ''
            if quantity in list(item.keys()) and 'value' in item[quantity][0]:
                likelyvalue = item[quantity][0]['value']
            errata.append(OrderedDict([('name', item['name']),
                                       ('alias', item['alias']),
                                       ('ident', error['value']),
                                       ('kind', error['kind']),
                                       ('quantity', error['extra']),
                                       ('likelyvalue', likelyvalue)]))

jsonstring = json.dumps(errata, indent='\t',
                        separators=(',', ':'), ensure_ascii=False)
with open('../errata.json', 'w') as f:
    f.write(jsonstring)
