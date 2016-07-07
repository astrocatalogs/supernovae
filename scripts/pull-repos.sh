#!/bin/bash

git pull
repos=($(awk -F= '{print $1}' ../input/rep-folders.txt))
repos+=('../input/sne-internal')
repos+=('../input/sne-external')
repos+=('../input/sne-external-radio')
repos+=('../input/sne-external-xray')
repos+=('../input/sne-external-spectra')
repos+=('../input/sne-external-WISEREP')
echo ${repos[*]}
cd ../output
for repo in ${repos[@]}; do
	cd ${repo}
	pwd
	git pull
	cd ..
done
