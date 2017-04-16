#! /bin/bash
set -e

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

cd /var/www/html/sne/astrocats
python -m astrocats.scripts.webcat -c sne &
pids[0]=$!
python -m astrocats.scripts.webcat -c sne -by &
pids[1]=$!
python -m astrocats.supernovae.scripts.dupecat &
pids[2]=$!
python -m astrocats.supernovae.scripts.conflictcat &
pids[3]=$!
python -m astrocats.scripts.bibliocat -c sne &
pids[4]=$!
python -m astrocats.supernovae.scripts.erratacat &
pids[5]=$!
python -m astrocats.scripts.hostcat -c sne &
pids[6]=$!
python -m astrocats.scripts.hammertime -c sne &
pids[7]=$!
python -m astrocats.supernovae.scripts.histograms &
pids[8]=$!
python -m astrocats.scripts.atelscbetsiaucs -c sne &
pids[9]=$!
python -m astrocats.supernovae.scripts.frbcat &
pids[10]=$!
for pid in ${pids[*]}; do
	wait $pid
done
cd /var/www/html/sne/astrocats/astrocats/supernovae/output/html
bash thumbs.sh
cd /var/www/html/sne/astrocats
