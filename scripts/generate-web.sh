#! /bin/bash
set -e

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

cd /var/www/html/sne/astrocats
python3.5 -m astrocats.scripts.webcat -c sne &
$pids[0]=$!
python3.5 -m astrocats.supernovae.scripts.dupecat &
$pids[1]=$!
python3.5 -m astrocats.supernovae.scripts.conflictcat &
$pids[2]=$!
python3.5 -m astrocats.supernovae.scripts.bibliocat &
$pids[3]=$!
python3.5 -m astrocats.supernovae.scripts.erratacat &
$pids[4]=$!
python3.5 -m astrocats.supernovae.scripts.hostcat &
$pids[5]=$!
python3.5 -m astrocats.supernovae.scripts.hammertime &
$pids[6]=$!
python3.5 -m astrocats.supernovae.scripts.histograms &
$pids[7]=$!
for pid in ${pids[*]}; do
	do wait $pid
done
