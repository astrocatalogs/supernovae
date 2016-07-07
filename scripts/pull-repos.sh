#!/bin/bash

git pull
repos=($(awk -F= '{print $1}' ../input/rep-folders.txt))
repos+=('sne-internal')
repos+=('sne-external')
repos+=('sne-external-radio')
repos+=('sne-external-xray')
repos+=('sne-external-spectra')
repos+=('sne-external-WISEREP')
echo ${repos[*]}
cd ../output
for repo in ${repos[@]}; do
	cd ${repo}
	pwd
	git pull
	cd ..
done
