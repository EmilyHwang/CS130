#!/usr/bin/python
import MySQLdb
import string

# returns all categories and subcategories like:
# { {categoryName, [subCategory, subCategory, ...] }, ... }
# so for every entry, entry['categoryName'] is categoryName, entry['subCategories'] is subCategories list
def getAllCategories():
	db = MySQLdb.connect(host="localhost",    # your host, usually localhost
						 user="",         # your username
						 passwd="",  # your password
						 db="beehive")

	# create cursor object to execute query
	cur_main = db.cursor()

	categories = []
	cur_main.execute("SELECT DISTINCT categoryName from Categories")
	main_cats = cur_main.fetchall()
	print main_cats
	# use tuple to strip extra syntax
	for (cat,) in main_cats:
		cur_sub = db.cursor()
		cur_sub.execute("SELECT subCategory FROM Categories WHERE categoryName = %s", (cat,) )
		sub_cats = cur_sub.fetchall()
		# strip extra syntax and format ampersands
		pretty_sub_cats = []
		for (sub_cat, ) in sub_cats:
			pretty_sub_cats.append( string.replace(sub_cat, '&amp;', '&') )
		entry = {}
		entry['categoryName'] = cat;
		entry['subCategories'] = pretty_sub_cats;
		print entry
		categories.append(entry)
	return categories