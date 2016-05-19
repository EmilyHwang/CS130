
#!/usr/bin/python
from tweepy import *
import json
import sys
import time
import os
from datetime import datetime, timedelta
from cass_orm import Cassandra
from user_rank import UserRank
import MySQLdb

#from collections import Counter, OrderedDict
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

MAX_TWEETS = 100
MAX_USER_TIMELINE_TWEETS = 200
MIN_NUM_OF_FOLLOWERS = 100

access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']

auth = AppAuthHandler(consumer_key, consumer_secret)
api = API(auth, wait_on_rate_limit=True)

# This is for multiprocessing
def unwrap_self_f(arg, **kwarg):
    return Search.query_user_timeline(*arg, **kwarg)

class Search:
	def __init__(self, query, max_tweets=MAX_TWEETS, max_user_timeline_tweets=MAX_USER_TIMELINE_TWEETS):
		q = "#" + query
		self.hashtag = q.lower()
		self.max_tweets = max_tweets
		self.max_user_timeline_tweets = max_user_timeline_tweets

		# Connect to MySQLdb
		self.db = MySQLdb.connect(host="localhost",    # your host, usually localhost
				 user="",         # your username
				 passwd="",  # your password
				 db="beehive")        # name of the data base

		# you must create a Cursor object. It will let
		#  you execute all the queries you need
		self.cur = self.db.cursor(MySQLdb.cursors.DictCursor)

		# Connect to Cassandra
		self.cass = Cassandra('beehive') 
	
	def __get_users_and_hashtags(self, query):
		data = Cursor(api.search, q=query, result_type="recent", count=10).items(10)

		query_results = []
		mentioned_users = []
		hashtags = []
		users = {}

		for tweet in data:
			if tweet.user.followers_count > MIN_NUM_OF_FOLLOWERS:
				tweet_datetime = tweet.created_at
				tweet_user = tweet.user.screen_name

				#if user already exists in dict, check if datetime is more recent
				if tweet_user not in users or (tweet_user in users and users[tweet_user]['tweetCreated'] < tweet_datetime):
					users[tweet_user] = {'fullname': tweet.user.name, 'tweetText': tweet.text, 'tweetCreated': tweet_datetime}
				
				mentions = tweet.entities['user_mentions']
				mentioned_users.extend([mention['screen_name'] for mention in mentions])

				hashtag_list = tweet.entities['hashtags']
				hashtags.extend([hashtag['text'] for hashtag in hashtag_list])

		return [users, set(mentioned_users), hashtags]

	# -----------------------------------------------------------------------
	# searches user timeline, retrieves 200 tweets each time, API max = 3200, current max set to 1000
	# parameters: user as screen_nam
	# returns: json
	# -----------------------------------------------------------------------
	def query_user_timeline(self, user):
		data = Cursor(api.user_timeline, screen_name=user, include_rts=0).items(self.max_user_timeline_tweets)

		last_status = None

		favorite_count_sum = 0
		retweet_count_sum = 0
		total_num_tweets = 0

		for status in data:
			last_status = status
			total_num_tweets += 1
			favorite_count_sum += status.favorite_count
			retweet_count_sum += status.retweet_count

		if last_status is None:
			return {'followers': 0, 'numTweets': 0, 'avgLikes': 0, 'avgRetweets': 0}

		else:
			followers_count = last_status.user.followers_count
			statuses_count = last_status.user.statuses_count
			avg_favorite_count = favorite_count_sum/total_num_tweets
			avg_retweet_count = retweet_count_sum/total_num_tweets
			print 'process %s - user: %s, followers: %d, numTweets: %d' % (os.getpid(), user, followers_count, statuses_count)
			return {'followers': followers_count, 'numTweets': statuses_count, 'avgLikes': avg_favorite_count, 'avgRetweets': avg_retweet_count}

	
	def update_cassandra(self, potential_influencers):
		query = self.hashtag

		for user in potential_influencers:
			# add to tables
			user_info = potential_influencers[user]
			
			userrank = UserRank(self.cass)
			rank = userrank.calculate_user_rank(user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], 0)
			
			cassUsers = self.cass.get_user(user)
			if not cassUsers:
				print "Inserting user: %s" % (user_info['fullname'])
				self.cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], 1, user_info['numTweets'], rank)
				
				self.cass.new_hashtag(query, user, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], rank)
				potential_influencers[user]['userRank'] = rank
				
			else: # user already associated with another hashtag. need to update time appeared
				print "User %s exits, update time"
				cassUsers = self.cass.get_most_recent_user(user)
				for most_recent_user in cassUsers:
					cassUser = most_recent_user
				updatedNumAppeared = cassUser.numappeared + 1
				self.cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], updatedNumAppeared, user_info['numTweets'], cassUser.userrank)
				
				self.cass.new_hashtag(query, user, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], cassUser.userrank)
				potential_influencers[user]['userRank'] = rank
				
		return potential_influencers
			
	# ----------------------------------------------------------------------
	# parameters: users (<10)
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, 'userRank'}, user2: {}}
	# 
	# This function will query Twitter API and the timeline (or Cassandra if needed) to retreive
	# 	10 users information
	# -----------------------------------------------------------------------
	def search_users_detail(self, users):
		count = 0
		potential_influencers = {}

		for user in users:
			print "Search user: %s timeline..." % user
			user_info = self.query_user_timeline(user)
			if user_info is not None:
				all_info = users[user].copy()
				all_info.update(user_info)
				potential_influencers[user] = all_info
				count += 1
			if count == 10:
				self.update_cassandra(potential_influencers)
				return potential_influencers

		self.update_cassandra(potential_influencers)
		return potential_influencers

	def search_users(self):
		query = self.hashtag
		# if hashtags exists in table, use datatabse, otherwise search twitter
		
		potential_influencers = {}
	
		self.cur.execute("SELECT * FROM Hashtags WHERE hashtag=%s", (query,))
		data = self.cur.fetchone()

		if data is None: # hashtag doesn't exist, search twitter
			print "Hashtag not found. Searching twitter"

			# This is a list of all users appeared form searching the hashtag
			init_results = self.__get_users_and_hashtags(self.hashtag)
			users = init_results[0]
			print users

			try:
				self.cur.execute("""INSERT INTO Hashtags VALUES (%s, %s, %s)""", (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
				self.db.commit()
			except:
				self.db.rollback()

			return {'potential_influencers': users, 'exist': False}

		else :
			#check timestamp

			# older than one day, search twitter, and return the first 10 {potential_users, exist=false}
			if data['lastUpdated'] < datetime.now()-timedelta(days=1):	
				print "Hashtag too old. Searching twitter"
				users = self.__get_users_and_hashtags(self.hashtag)
				print users

				try:
					self.cur.execute("""UPDATE Hashtags SET lastUpdated=%s, timeSearched=%s WHERE hashtag=%s""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['timeSearched']+1, query))
					self.db.commit()
				except:
					self.db.rollback()
					
				return {'potential_influencers': users, 'exist': False}

			# If the hashtags exists, we want to return {potential_users, exist=true}
			else: # database has updated info
				# go to cassandra
				print "Retrieving data from Cassandra"
				users = self.cass.get_hashtag(query)
				if users is not None:
					for user in users:
						potential_influencers[user.username] = {'tweetText': user.tweettext, 'tweetCreated': user.tweetcreated, 'followers': user.followers, 'numTweets': user.numtweets, 'avgLikes': user.avglikes, 'avgRetweets': user.avgretweets, 'userRank': user.userrank}
				
					#update timesearched
					print "timesSearched: " + str(data['timeSearched'])
					try:
						self.cur.execute("""UPDATE Hashtags SET timeSearched=%s WHERE hashtag=%s""", (data['timeSearched']+1, query))
						self.db.commit()
					except:
						self.db.rollback()

					return {'potential_influencers': potential_influencers, 'exist': True}
				else:
					print "mysql and cassandra databases out of sync. Search user detail?"


	################
	# For Crawlers
	################

	# ----------------------------------------------------------------------
	# parameters: hashtag
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, 'userRank'}, user2: {}}
	# NEED USER RANK MODIFICATION
	# -----------------------------------------------------------------------
	def search_twitter(self):
		query = self.hashtag
		# if hashtags exists in table, use datatabse, otherwise search twitter
		
		potential_influencers = {}
	
		self.cur.execute("SELECT * FROM Hashtags WHERE hashtag=%s", (query,))
		data = self.cur.fetchone()
		
		if data is None: #hashtag doesn't exist, search twitter
			print "Hashtag not found. Searching twitter"
			potential_influencers = self.search_twitter_api()
			
			# check database for user rank?
			# for user in potential_influencers:
				# potential_influencers[user]['userRank'] = 0
			try:
				self.cur.execute("""INSERT INTO Hashtags VALUES (%s, %s, %s)""", (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
				self.db.commit()
			except:
				self.db.rollback()

			self.update_cassandra(potential_influencers)
		else:
			#check timestamp
			if data['lastUpdated'] < datetime.now()-timedelta(days=1):	# older than one day, search twitter	
				print "Hashtag too old. Searching twitter"
				potential_influencers = self.search_twitter_api(query)

				try:
					self.cur.execute("""UPDATE Hashtags SET lastUpdated=%s, timeSearched=%s WHERE hashtag=%s""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['timeSearched']+1, query))
					self.db.commit()
				except:
					self.db.rollback()
					
				self.update_cassandra(potential_influencers)
			else: # database has updated info
				# go to cassandra
				print "Retrieving data from Cassandra"
				users = self.cass.get_hashtag(query)
				if users is not None:
					for user in users:
						potential_influencers[user.username] = {'tweetText': user.tweettext, 'tweetCreated': user.tweetcreated, 'followers': user.followers, 'numTweets': user.numtweets, 'avgLikes': user.avglikes, 'avgRetweets': user.avgretweets, 'userRank': user.userrank}
				
					#update timesearched
					print "timesSearched: " + str(data['timeSearched'])
					try:
						self.cur.execute("""UPDATE Hashtags SET timeSearched=%s WHERE hashtag=%s""", (data['timeSearched']+1, query))
						self.db.commit()
					except:
						self.db.rollback()
				else:
					print "mysql and cassandra databases out of sync"
			
		print potential_influencers
		return potential_influencers

	# ----------------------------------------------------------------------
	# parameters: hashtag
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, }, user2: {}}
	# -----------------------------------------------------------------------
	def search_twitter_api(self):
		potential_influencers = {}
		users_hashtag_list  = self.__get_users_and_hashtags(self.hashtag)
		user_dict = users_hashtag_list[0]
		# print user_dict
		mentioned_users = users_hashtag_list[1]

		# Each 
		for user in user_dict:
			user_info = self.query_user_timeline(user)
			if user_info is not None:
				all_info = user_dict[user].copy()
				all_info.update(user_info)
				# print user + ": " + str(all_info)
				potential_influencers[user] = all_info
		return potential_influencers





