#!/bin/sh

# Clean up data
echo "Dropping old data..."
mysql < drop.sql

# Create the database and the table
echo "Creating Database 'beehive' and Tables..."
mysql < create.sql

# Populating table 'Categories'
echo "Populating Categories table..."
mysql beehive -e "LOAD DATA INFILE '/Users/IreneY/Desktop/cs130/CS130/beehive/data/twitter_categories.csv' INTO TABLE Categories FIELDS TERMINATED BY ',';"

# Populaing table 'SubCategoryPeople'
echo "Populating SubCategoryPeople table..."
IFS=,
for f in ./data/category_people/*
do
	subcatid=`basename $f .csv`
	while read column1 column2
	do
		mysql beehive -e "INSERT INTO SubCategoryPeople (subCategoryId, username, fullname) VALUES (\""$subcatid\"", \""$column2"\", \""$column1"\");"
	done < $f
done