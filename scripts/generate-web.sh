#! /bin/bash
set -e

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

cd /var/www/html/sne/sne/scripts
./make-catalog.py &
./make-catalog.py -by &
./find-dupes.py &
./find-conflicts.py &
./make-biblio.py &
./make-errata.py &
./make-host-catalog.py &
./hammertime.py &
./make-histograms.py &
