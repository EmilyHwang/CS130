#!/bin/bash

# we are inside category_people directory
python crawler.py
mkdir ../../data/tmp

echo "Sorting output files"
for i in ../../data/category_people/*
do
	name=`basename $i`
	sort -u $i > ../../data/tmp/$name
done

echo "Removing temp files"
rm ../../data/category_people/*
mv ../data/tmp/* ../../data/category_people/
rm ../../data/tmp