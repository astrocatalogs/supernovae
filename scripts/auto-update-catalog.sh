#! /bin/bash
set -e

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

cd /var/www/html/sne/astrocats
python3.5 -m astrocats supernovae import -u
SNEUPDATE=$?
echo $SNEUPDATE
if [[ $SNEUPDATE == 0 ]]; then
	astrocats/supernovae/scripts/generate-web.sh
	#stamp=$(date +"%Y-%m-%d %k:%M")
	#./commit-and-push-repos.sh "Auto update: $stamp"
fi
