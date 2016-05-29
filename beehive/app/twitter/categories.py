#!/usr/bin/python
import MySQLdb
import string
import logging
from orm.mysql_orm import MySQL

logfile = logging.getLogger('file')

def getAllCategories():
    logfile.info("Get all categories")

    mysql = MySQL('beehive')
    categories = mysql.getCatAndSub()

    # {'Nonprofits': ['Nonprofits &amp; Foundations', 'Humanitarian'], 'Music': [...]
    catSub_dict = {}
    for pair in categories:
        catSub_dict.setdefault(pair['categoryName'], []).append(pair['subCategory'])

    results = []

    for key in catSub_dict:
        pretty_sub_cats = {}
        pretty_sub_cats['categoryName'] = key
        pretty_sub_cats['subCategories'] = catSub_dict[key]
        results.append(pretty_sub_cats)

    return results
