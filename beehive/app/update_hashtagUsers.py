#!/bin/python

#########################################################
# This script is used to update the hashtag User table  #
#########################################################

import os, sys, MySQLdb, datetime, time
from cass_orm import Cassandra
from mysql_orm import MySQL
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class HashtagUsers:
	def __init__(self):
		self.driver = webdriver.Chrome(executable_path=r"/Users/IreneY/Library/chromedriver")
		today = datetime.datetime.now()
		self.end_date = "%s-%s-%s" % (today.year, today.month, today.day)
		weekAgo = today - datetime.timedelta(days=7)
		self.start_date = "%s-%s-%s" % (weekAgo.year, weekAgo.month, weekAgo.day)

	def update(self):
		mysql = MySQL("beehive")
		cass = Cassandra("beehive")
		totalValidResults = 0

		# Get all the hashtags from MySQL table
		hashtagSets = mysql.getHashtags()
		# For each hashtag
		for hashtag in hashtagSets:
			hashtag = hashtag[1:]
			#	Find the list of users for this hashtag and put it in a dictionary, D
			users_temp = cass.get_user_from_hashtag(hashtag)
			users = set()
			for user in users_temp:		
				users.add(user.username)

			# Use selenium to crawl the hashtag search tweets results
			query = "https://twitter.com/search?vertical=default&q=%23" + hashtag + "%20since%3A" + self.start_date + "%20until%3A" + self.end_date + "%20include%3Aretweets&src=typd"		
			self.driver.get(query)
			# If the tweets have more than 10 retweets, then look at the user info

			#	In each results, find the user associated
			#	If go to the user profile, get their information (follower, tweets, retweets count)				

	def scroll():
		for _ in xrange(0, 10):
		  self.driver.execute_script("window.scrollTo(0, 10000);")
		  time.sleep(2)

	def quit(self):
		self.driver.quit()

if __name__ == "__main__":
	y = HashtagUsers()
	y.update()
	y.quit()