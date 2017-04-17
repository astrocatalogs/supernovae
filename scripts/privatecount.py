import json
import os
import re
from tqdm import tqdm
from glob import glob

totcount = 0
totcountp14 = 0
evcount = 0
with open('../output/catalog.min.json', 'r') as f:
    filetext = f.read()
    meta = json.loads(filetext)

metaals = [[y['value'].upper() for y in x['alias']] for x in meta]

names = []

for folder in tqdm(glob('../input/sne-external-WISEREP/*')):
    path = folder + '/README.json'
    name = folder.split('/')[-1]
    if os.path.isfile(path):
        with open(path, 'r') as f:
            dat = json.loads(f.read())
            aliases = []
            for al in metaals:
                if name.upper() in al:
                    aliases = al
            if not aliases:
                continue
            if "Private Spectra" in dat and any([x for x in aliases]):
                nums = re.findall(r'\d+', name)
                if nums:
                    year = int('20' + nums[0])
                else:
                    year = 0
                privcount = int(dat["Private Spectra"])
                if privcount > 0:
                    evcount += 1
                    totcount += privcount
                    tqdm.write(name + ': ' + str(privcount))
                    if year < 2014:
                        totcountp14 += privcount
                        names.append(name)

print(evcount, totcount, totcountp14)
