#!/bin/bash

PATH=/opt/local/bin:/usr/local/bin:$PATH ; export PATH
LD_LIBRARY_PATH=/usr/local/lib:/opt/local/lib ; export LD_LIBRARY_PATH

if [ $# -eq 0 ]
  then
    echo "No arguments supplied, exiting"
	exit
fi

./pull-repos.sh

git commit -a -m "$1"
git push
repos=($(awk -F= '{print $1}' rep-folders.txt))
repos+=('sne-internal')
repos+=('sne-external')
repos+=('sne-external-radio')
repos+=('sne-external-xray')
repos+=('sne-external-spectra')
repos+=('sne-external-WISEREP')
echo ${repos[*]}
cd ..
for repo in ${repos[@]}; do
	echo ${repo}
	cd ${repo}
	pwd
	git add -A
	git commit -a -m "$1"
	git push
	cd ..
done
