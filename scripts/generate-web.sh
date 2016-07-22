#! /bin/bash
set -e

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

cd /var/www/html/sne/astrocats
python3.5 -m astrocats.supernovae.scripts.webcat &
python3.5 -m astrocats.supernovae.scripts.dupecat &
python3.5 -m astrocats.supernovae.scripts.conflictcat &
python3.5 -m astrocats.supernovae.scripts.bibliocat &
python3.5 -m astrocats.supernovae.scripts.erratacat &
python3.5 -m astrocats.supernovae.scripts.hostcat &
python3.5 -m astrocats.supernovae.scripts.hammertime &
python3.5 -m astrocats.supernovae.scripts.histograms &
