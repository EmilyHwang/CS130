#!/bin/sh

python youtube_crawler.py $1 $2 > tmp.csv 

sort -t, -k1 -g -n -u -r tmp.csv > youtube_output.csv
rm tmp.csv