#!/bin/python

#########################################################
# This script is used to update the hashtag User table  #
#########################################################

import os, sys, MySQLdb
from orm import Cassandra

# Get all the hashtags from MySQL table
# For each hashtag
#		Find the list of users for this hashtag and put it in a dictionary
# 	
