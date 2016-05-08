#!/bin/bash

# Clean up data
echo "Dropping old data..."
mysql < drop.sql

# Create the database and the table
echo "Creating Database 'beehive' and Tables..."
mysql < create.sql

# Populating table 'Categories'
echo "Populating Categories table..."
mysql beehive -e "LOAD DATA LOCAL INFILE '../data/twitter_categories.csv' INTO TABLE Categories FIELDS TERMINATED BY ','"

# Populating table 'SubCategoryPeople'
echo "Populating SubCategoryPeople table..."
for f in ../data/category_people/*
do
	echo "Processing file "$f
	subcatid=`basename $f .csv`
	while IFS='@' read col1 col2
	do
		if [[ ${col2} != "" ]]
			then
			statement='INSERT INTO SubCategoryPeople (subCategoryId, username, fullname) VALUES ("'$subcatid'", "'${col2}'", "'${col1%?}'")'
			mysql beehive -e "${statement}"
		fi
	done < $f
done