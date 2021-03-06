
#!/usr/bin/python
from tweepy import *
import json
import sys
import time
import os
from datetime import datetime, timedelta
from user_rank import UserRank
from collections import OrderedDict

from orm.cass_orm import Cassandra
from orm.mysql_orm import MySQL

#from collections import Counter, OrderedDict
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

#logging
import logging

MAX_TWEETS = 100
MAX_USER_TIMELINE_TWEETS = 200
MIN_NUM_OF_FOLLOWERS = 100

logfile = logging.getLogger('file')
logconsole = logging.getLogger('console')

class Search:
	def __init__(self, query, auth, max_tweets=MAX_TWEETS, max_user_timeline_tweets=MAX_USER_TIMELINE_TWEETS):
		q = "#" + query
		self.hashtag = q.lower()
		self.max_tweets = max_tweets
		self.max_user_timeline_tweets = max_user_timeline_tweets
		self.auth = auth
		self.api = auth.create_api()

		# Connect to MySQLdb
		self.mysql = MySQL('beehive')

		# Connect to Cassandra
		self.cass = Cassandra('beehive')


	# -----------------------------------------------------------------------
	# Get Users and Hashtags
	# Input: None
	# Output: [{username: {fullname: , tweetText:, tweetCreated}}, set(mentioned_users), mentioned_hashtags]
	# -----------------------------------------------------------------------
	def get_users_and_hashtags(self):
		logfile.info("========== Get User And Hashtag ===========")
		data = Cursor(self.api.search, q=self.hashtag, result_type="recent", count=100).items(self.max_tweets)

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

				# Store this information inside Cassandra HashtagUsers table even though there is no complete info
				# Next time when query, there will be information about the user and this hashtag
				# If this user is in the results of the query, query user timeline
				self.cass.new_hashtag(self.hashtag, tweet_user, tweet.user.name, 0, 0, 0, 0, tweet_datetime, tweet.text, 0, 0)

				mentions = tweet.entities['user_mentions']
				mentioned_users.extend([mention['screen_name'] for mention in mentions])

				hashtag_list = tweet.entities['hashtags']
				hashtags.extend([hashtag['text'] for hashtag in hashtag_list])
		return [users, set(mentioned_users), hashtags]

	# -----------------------------------------------------------------------
	# searches user timeline, retrieves 200 tweets each time, API max = 3200, current max set to 1000
	# parameters: user as screen_nam
	# returns: if there's status: {'fullname': status.user.name, 'followers': [int], 'numTweets': [int], 'avgLikes': [float], 'avgRetweets': [float]}
	#					 else {'followers': 0, 'numTweets': 0, 'avgLikes': 0, 'avgRetweets': 0}
	# -----------------------------------------------------------------------
	def query_user_timeline(self, user):
		logfile.info("========= Query User Timeline ===========")
		logfile.info("Looking at user %s's timeline ..." % user )
		data = Cursor(self.api.user_timeline, screen_name=user, include_rts=0, count=200).items(self.max_user_timeline_tweets)

		favorite_count_sum = 0
		retweet_count_sum = 0
		total_num_tweets = 0

		status = None
		logfile.info("Calculating ...")

		try:
			for status in data:
				logfile.info("calculating status id %s" % status.id)
				total_num_tweets = total_num_tweets + 1
				favorite_count_sum = status.favorite_count + favorite_count_sum
				retweet_count_sum = status.retweet_count + retweet_count_sum

			if status is None:
				return {'followers': 0, 'numTweets': 0, 'avgLikes': 0, 'avgRetweets': 0}

			else:
				followers_count = status.user.followers_count
				statuses_count = status.user.statuses_count
				avg_favorite_count = favorite_count_sum/total_num_tweets
				avg_retweet_count = retweet_count_sum/total_num_tweets

				return {'fullname': status.user.name, 'followers': status.user.followers_count, 'numTweets': status.user.statuses_count, 'avgLikes': favorite_count_sum/total_num_tweets, 'avgRetweets': retweet_count_sum/total_num_tweets}
		except: 
			logfile.error("Unable to parse user %s" % user)
			return {'followers': 0, 'numTweets': 0, 'avgLikes': 0, 'avgRetweets': 0}

	def update_cassandra(self, potential_influencers):
		logfile.info("========= Updating Cassandra ===========")
		query = self.hashtag

		for user in potential_influencers:
			# add to tables
			user_info = potential_influencers[user]

			userrank = UserRank(self.cass)
			rank = userrank.calculate_user_rank(user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], 0, 0)

			cassUsers = self.cass.get_user(user)
			if not cassUsers:
				self.cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], 1, user_info['numTweets'], rank)

				self.cass.new_hashtag(query, user, user_info['fullname'], user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], rank, 0)
				potential_influencers[user]['userRank'] = rank

			else: # user already associated with another hashtag. need to update time appeared
				cassUsers = self.cass.get_most_recent_user(user)
				for most_recent_user in cassUsers:
					cassUser = most_recent_user
				updatedNumAppeared = cassUser.numappeared + 1
				self.cass.new_user(user, cassUser.fullname, datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], updatedNumAppeared, user_info['numTweets'], cassUser.userrank)

				self.cass.new_hashtag(query, user, cassUser.fullname, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], cassUser.userrank, 0)
				potential_influencers[user]['userRank'] = rank

		return potential_influencers

	# ----------------------------------------------------------------------
	# parameters: users: user_dictionary
	# 	two type of users
	#		1. Results from Cassandra
	#		2. Results from get_users_and_hashtags (needs API)
	# returns: [first pull: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y',
	#															'avgLikes': z, 'avgRetweets': a, 'userRank'}, user2: {}},
	#						leftover]
	#
	# This function will query Twitter API and the timeline (or Cassandra if needed) to retreive
	# 	10 users information; it will return all results in 'first_pull' if data if all info is already in cassandra db
	# -----------------------------------------------------------------------
	def search_users_detail(self, users):
		logfile.info("========= SEARCH USERS DETAIL ===========")
		count = 0
		potential_influencers = {}

		# if len(users) == 0:
		# 	return {'first_pull': {}, 'leftover': {}}

		if type(users) is dict:
			logfile.info("This is a fresh set of results, need to query Twitter API")
			# this is a result from get_users_and_hashtags
			leftover = users.copy()
			for user in users:
				user_info = self.query_user_timeline(user)

				if user_info['followers'] != 0:
					all_info = users[user].copy()
					all_info.update(user_info)
					potential_influencers[user] = all_info
					try:
						potential_influencers[user]['followStatus'] = self.api.show_friendship(target_screen_name=user)[1].followed_by
					except: 
						potential_influencers[user]['followStatus'] = False
				leftover.pop(user, None)

				count += 1
				if count == 10:
					self.update_cassandra(potential_influencers)
					return {'first_pull': OrderedDict(sorted(potential_influencers.items(), key=lambda x: x[1]['userRank'], reverse=True)), 'leftover': leftover}

			self.update_cassandra(potential_influencers)
			return {'first_pull': OrderedDict(sorted(potential_influencers.items(), key=lambda x: x[1]['userRank'], reverse=True)), 'leftover': {}}

		else:
			# This is a Cassandra Object
			logfile.info("These data are from Cassandra dataset")
			user_update_queue = {}
			for user in users:
				# If we already spend time searching for 10 users, we don't want to do it anymore
				if user.followers == 0 and count >= 10:
					# Iterate the rest of the un-updated one and return
					user_update_queue[user.username] = {'fullname': user.fullname, 'tweetText': user.tweettext, 'tweetCreated': user.tweetcreated}

				# If not, we will continue searching
				else:
					# Check whether it needs to use Twitter API or not
					if user.followers != 0:
						logfile.info("User %s has information in our database! No need to API" % user.username)
						try:
							followStatus = self.api.show_friendship(target_screen_name=user.username)[1].followed_by
						except:
							followStatus = False
						potential_influencers[user.username] = {'fullname': user.fullname, 
																										'tweetText': user.tweettext, 
																										'tweetCreated': user.tweetcreated, 
																										'followers': user.followers, 
																										'numTweets': user.numtweets, 
																										'avgLikes': user.avglikes, 
																										'avgRetweets': user.avgretweets,
																										'followStatus': followStatus}
					else:
						# This object is a cassandra object but it's not updated
						logfile.info("User %s doesn't have information :( Search API" % user.username)
						user_info = self.query_user_timeline(user.username)

						if user_info['followers'] != 0:
							try:
								followStatus = self.api.show_friendship(target_screen_name=user.username)[1].followed_by
							except:
								followStatus = False
							potential_influencers[user.username] = {'fullname': user.fullname, 
																											'tweetText': user.tweettext, 
																											'tweetCreated': user.tweetcreated, 
																											'followers': user_info['followers'], 
																											'numTweets': user_info['numTweets'], 
																											'avgLikes': user_info['avgLikes'], 
																											'avgRetweets': user_info['avgRetweets'],
																											'followStatus': followStatus}

						count += 1

			self.update_cassandra(potential_influencers)
			return {'first_pull': OrderedDict(sorted(potential_influencers.items(), key=lambda x: x[1]['userRank'], reverse=True)), 'leftover': user_update_queue}

	# ----------------------------------------------------------------------
	# parameters:
	# returns: {'first_pull': first 10 users information (or all user info if already exists in cassandra db), 'leftover': rest of the users}
	#
	# This function will return a potential influencers list that has all the info
	#		or < 10 per page based on whether hashtag exist in the database or not
	# -----------------------------------------------------------------------
	def search_users(self):
		query = self.hashtag
		logfile.info("======= Search Users for hashtag #%s =======" % query)
		# if hashtags exists in table, use datatabse, otherwise search twitter

		potential_influencers = {}

		data = self.mysql.findHashtag(query)

		if not data: # hashtag doesn't exist, search twitter
			logfile.info("Hashtag not found. Searching twitter")

			# This is a list of all users appeared form searching the hashtag
			init_results = self.get_users_and_hashtags()
			users = init_results[0]

			potential_influencers = self.search_users_detail(users)

			# Update MySQL Hashtag table
			self.mysql.newHashtag(query)

			return potential_influencers

		else :
			#check timestamp
			# older than one day, search twitter, and return the first 10 {potential_users, exist=false}
			if data['lastUpdated'] < datetime.now()-timedelta(days=1):
				logfile.info("Hashtag too old. Searching twitter")
				init_results = self.get_users_and_hashtags()
				users = init_results[0]
				potential_influencers = self.search_users_detail(users)

				# Update hashtag table
				self.mysql.updateHashtag(query, data['timeSearched']+1)

				return potential_influencers

			# If the hashtags exists and it's updated
			else:
				# go to cassandra
				logfile.info("Retrieving data from Cassandra")
				users = self.cass.get_hashtag(query)

				if users is not None:
					potential_influencers = self.search_users_detail(users)

					# Update hashtag table
					self.mysql.updateHashtag(query, data['timeSearched']+1)

					return potential_influencers

				else:
					logfile.error("mysql and cassandra databases out of sync. Search user detail?")
					logconsole.error("mysql and cassandra databases out of sync. Search user detail?")
					return {}
