#!/bin/python

#########################################################
# This script is used to update the hashtag User table  #
#########################################################

import os, sys, MySQLdb, datetime, time
from cass_orm import Cassandra
from mysql_orm import MySQL
from twitter_search import Search

class HashtagUsers:
	def __init__(self):
		self.mysql = MySQL("beehive")

	def update(self):
		# Get all the hashtags from MySQL table
		hashtagSets = self.mysql.getHashtags()
		# For each hashtag
		for hashtag in hashtagSets:
			hashtag = hashtag[1:]
			s = Search(hashtag)
			
			# Do new searches
			potential_influencers = s.search_twitter_api(hashtag)
			# Update the hashtag timestamp in MySQL
			self.mysql.updateHashtag(hashtag)
			# Update the Cassandra table
			s.update_cassandra(potential_influencers)

if __name__ == "__main__":
	y = HashtagUsers()
	y.update()