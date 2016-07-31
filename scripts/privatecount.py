#!/usr/local/bin/python3.5
import json
import os
import re
from glob import glob

totcount = 0
totcountp14 = 0
evcount = 0
for folder in glob('../input/sne-external-WISEREP/*'):
    path = folder + '/README.json'
    name = folder.split('/')[-1]
    if os.path.isfile(path):
        with open(path, 'r') as f:
            dat = json.loads(f.read())
            if "Private Spectra" in dat and 'PTF' in name.upper():
                nums = re.findall(r'\d+', name)
                if nums:
                    year = int('20' + nums[0])
                else:
                    year = 0
                privcount = int(dat["Private Spectra"])
                if privcount > 0:
                    evcount += 1
                    totcount += privcount
                    if year < 2014:
                        totcountp14 += privcount
                    print(name)

print(evcount, totcount, totcountp14)
