import gzip
import json
import os
import warnings
from collections import OrderedDict

from astropy import units as un
from astropy.coordinates import SkyCoord as coord
from tqdm import tqdm

from astrocats.catalog.utils import round_sig
from astrocats.supernovae.scripts.repos import repo_file_list

from ...catalog.utils import get_entry_filename

conflicts = []

outdir = "astrocats/supernovae/output/"

files = repo_file_list(bones=False)

for fcnt, eventfile in enumerate(tqdm(sorted(files, key=lambda s: s.lower()))):
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

    ras = []
    decs = []
    zs = []
    cts = []
    rasources = []
    decsources = []
    zsources = []
    ctsources = []
    for key in list(item.keys()):
        lc = 0
        if key in ['name', 'sources', 'photometry', 'spectra']:
            continue
        if len(item[key]) == 1:
            continue
        for quantum in item[key]:
            if key == 'ra':
                newsources = []
                for alias in quantum['source'].split(','):
                    for source in item['sources']:
                        if source['alias'] == alias:
                            newsources.append({'idtype': 'bibcode' if 'bibcode' in source else
                                'name' if 'name' in source else 'arxivid',
                                'id': source['bibcode'] if 'bibcode' in source else
                                source['name'] if 'name' in source else source['arxivid']})
                if newsources:
                    ras.append(quantum['value'])
                    rasources.append({'idtype': ','.join(
                        [x['idtype'] for x in newsources]), 'id': ','.join([x['id'] for x in newsources])})
            elif key == 'dec':
                newsources = []
                for alias in quantum['source'].split(','):
                    for source in item['sources']:
                        if source['alias'] == alias:
                            newsources.append({'idtype': 'bibcode' if 'bibcode' in source else
                                'name' if 'name' in source else 'arxivid',
                                'id': source['bibcode'] if 'bibcode' in source else
                                source['name'] if 'name' in source else source['arxivid']})
                if newsources:
                    decs.append(quantum['value'])
                    # Temporary fix for David's typo
                    if decs[-1].count('.') == 2:
                        decs[-1] = decs[-1][:decs[-1].rfind('.')]
                    decsources.append({'idtype': ','.join(
                        [x['idtype'] for x in newsources]), 'id': ','.join([x['id'] for x in newsources])})
            elif key == 'redshift':
                newsources = []
                for alias in quantum['source'].split(','):
                    for source in item['sources']:
                        if source['alias'] == alias:
                            newsources.append({'idtype': 'bibcode' if 'bibcode' in source else
                                'name' if 'name' in source else 'arxivid',
                                'id': source['bibcode'] if 'bibcode' in source else
                                source['name'] if 'name' in source else source['arxivid']})
                if newsources:
                    zs.append(float(quantum['value']))
                    zsources.append({'idtype': ','.join(
                        [x['idtype'] for x in newsources]), 'id': ','.join([x['id'] for x in newsources])})
            elif key == 'claimedtype':
                newsources = []
                for alias in quantum['source'].split(','):
                    for source in item['sources']:
                        if source['alias'] == alias:
                            newsources.append({'idtype': 'bibcode' if 'bibcode' in source else
                                'name' if 'name' in source else 'arxivid',
                                'id': source['bibcode'] if 'bibcode' in source else
                                source['name'] if 'name' in source else source['arxivid']})
                if newsources:
                    cts.append(quantum['value'])
                    ctsources.append({'idtype': ','.join(
                        [x['idtype'] for x in newsources]), 'id': ','.join([x['id'] for x in newsources])})

    edit = True if os.path.isfile(
        '../sne-internal/' + get_entry_filename(item['name']) + '.json') else False

    if ras and decs and item['name'] and item['name'] not in ['SN2002fz']:
        oralen = len(ras)
        odeclen = len(decs)
        if len(ras) > len(decs):
            decs = decs + [decs[0] for x in range(len(ras) - len(decs))]
        elif len(ras) < len(decs):
            ras = ras + [ras[0] for x in range(len(decs) - len(ras))]

        try:
            coo = coord(ras, decs, unit=(un.hourangle, un.deg))
        except:
            warnings.warn('Mangled coordinate, setting to 0')
            radegs = []
            decdegs = []
        else:
            radegs = coo.ra.deg[:oralen]
            decdegs = coo.dec.deg[:odeclen]

        ras = ras[:oralen]
        decs = decs[:odeclen]

        ialias = item.get('alias', item['name'])
        if len(ras) != len(radegs):
            tqdm.write('Mangled R.A. for ' + item['name'])
            conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                          ('quantity', 'ra'), ('difference', '?'), ('values', ras), ('sources', rasources)]))
        elif len(radegs) > 1:
            maxradiff = max([abs((radegs[i + 1] - radegs[i]) / radegs[i + 1])
                             for i in range(len(radegs) - 1)])
            if maxradiff > 0.001:
                tqdm.write(
                    'R.A. difference greater than 0.1% for ' + item['name'])
                conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                              ('quantity', 'ra'), ('difference', str(round_sig(maxradiff))), ('values', ras), ('sources', rasources)]))

        if len(decs) != len(decdegs):
            tqdm.write('Mangled Dec. for ' + item['name'])
            conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                          ('quantity', 'dec'), ('difference', '?'), ('values', decs), ('sources', decsources)]))
        elif len(decdegs) > 1:
            maxdecdiff = max([abs((decdegs[i + 1] - decdegs[i]) / decdegs[i + 1])
                              for i in range(len(decdegs) - 1)])
            if maxdecdiff > 0.001:
                tqdm.write(
                    'Dec. difference greater than 0.1% for ' + item['name'])
                conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                              ('quantity', 'dec'), ('difference', str(round_sig(maxdecdiff))), ('values', decs), ('sources', decsources)]))

    if zs:
        maxzdiff = max([abs((zs[i + 1] - zs[i]) / zs[i + 1])
                        for i in range(len(zs) - 1)])
        if maxzdiff > 0.05:
            tqdm.write(
                'Redshift difference greater than 5% for ' + item['name'])
            conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                          ('quantity', 'redshift'), ('difference', str(round_sig(maxzdiff))), ('values', zs), ('sources', zsources)]))

    if cts:
        typei = any(((x.startswith('I') and (len(x) == 1 or x[1] != 'I')) or
                     (x.startswith('SLSN-I') and (len(x) == 6 or x[6] != 'I'))) for x in cts)
        typeii = any((x.startswith(('II', 'SLSN-II')) or x == 'CC')
                     for x in cts)
        ntypei = any(x == 'nIa' for x in cts)
        if (typei and typeii) or (typei and ntypei):
            tqdm.write('Conflicting supernova typings for ' + item['name'])
            conflicts.append(OrderedDict([('name', item['name']), ('alias', ialias), ('edit', edit),
                                          ('quantity', 'claimedtype'), ('difference', ''), ('values', cts), ('sources', ctsources)]))

# Convert to array since that's what datatables expects
jsonstring = json.dumps(conflicts, indent='\t',
                        separators=(',', ':'), ensure_ascii=False)
with open(outdir + 'conflicts.json', 'w') as f:
    f.write(jsonstring)
