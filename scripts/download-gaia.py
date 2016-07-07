#!/usr/local/bin/python3.5
import os
import urllib.error
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

# response = urllib2.urlopen('https://gaia.ac.uk/selected-gaia-science-alerts')
path = os.path.abspath('../sne-external/selected-gaia-science-alerts')
response = urllib.request.urlopen('file://' + path)
html = response.read()

soup = BeautifulSoup(html, "html5lib")
table = soup.findAll("table")[1]
for r, row in enumerate(table.findAll('tr')):
    if r == 0:
        continue

    col = row.findAll('td')
    classname = col[7].contents[0]

    if 'SN' not in classname:
        continue

    links = row.findAll('a')
    name = links[0].contents[0]

    if name == 'Gaia15aaaa':
        continue

    photlink = ('http://gsaweb.ast.cam.ac.uk/alerts/alert/' +
                name + '/lightcurve.csv/')
    photresp = urllib.request.urlopen(photlink)
    phottxt = photresp.read().decode('utf-8')

    with open('../sne-external/GAIA/GAIA-' + name + '.html', 'w') as f:
        f.write(phottxt)
