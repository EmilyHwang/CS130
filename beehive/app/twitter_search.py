
#!/usr/bin/python
from tweepy import *
import json
import sys
import time
import os
import pdb
from datetime import datetime, timedelta
from orm import Cassandra
import MySQLdb

#from collections import Counter, OrderedDict
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

MAX_TWEETS = 100
MAX_USER_TIMELINE_TWEETS = 200

access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']

auth = AppAuthHandler(consumer_key, consumer_secret)
api = API(auth)

class Search:

	def __init__(self, query):
		self.hashtag = query
	
	def __api_query_search(self, query):
		data = Cursor(api.search, q=query, result_type="mixed", count=100).items(MAX_TWEETS)

		query_results = []
		for tweet in data:
			query_results.append(json.loads(json.dumps(tweet._json)))
		print "original query size: " + str(len(query_results))
		return query_results
	
	# -----------------------------------------------------------------------
	# Finds users of tweets
	# parameters: list of tweets
	# returns: [{'user_name': {tweetText, tweetCreated}}, mentioned_users hashtags]
	# -----------------------------------------------------------------------
	def __get_users_and_hashtags(self, tweets):
		mentioned_users = []
		hashtags = []
		users = {}
		for tweet in tweets:
			#if tweet['user']['followers_count'] > MIN_NUM_OF_FOLLOWERS:
			
			tweet_datetime = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
			tweet_user = tweet['user']['screen_name']

			#if user already exists in dict, check if datetime is more recent
			if tweet_user not in users or (tweet_user in users and users[tweet_user]['tweetCreated'] < tweet_datetime):
				users[tweet_user] = {'fullname': tweet['user']['name'], 'tweetText': tweet['text'], 'tweetCreated': tweet_datetime}
			
			mentions = tweet['entities']['user_mentions']
			mentioned_users.extend([mention['screen_name'] for mention in mentions])

			hashtag_list = tweet['entities']['hashtags']
			hashtags.extend([hashtag['text'] for hashtag in hashtag_list])

		return [users, set(mentioned_users), hashtags]
	# -----------------------------------------------------------------------
	# searches user timeline, retrieves 200 tweets each time, API max = 3200, current max set to 1000
	# parameters: user as screen_nam
	# returns: json
	# -----------------------------------------------------------------------
	def __query_user_timeline(self, user):
		data = Cursor(api.user_timeline, screen_name=user, count=200, include_rts=1).items(MAX_USER_TIMELINE_TWEETS)
		query_results = []
		for tweet in data:
			query_results.append(json.loads(json.dumps(tweet._json)))
		return query_results
	# -----------------------------------------------------------------------
	# searches user timeline - last 3200 statuses
	# parameters: user as screen_names
	# returns: {'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a}
	# -----------------------------------------------------------------------
	def __extract_user_timeline_info(self, user):
		print "Extracting user: " + user
		query_results = self.__query_user_timeline(user)
		# extract user info once from first tweet, should be same for ALL tweets
		if len(query_results) > 1:
			user_info = query_results[0]['user']
		followers_count = user_info['followers_count']
		statuses_count = user_info['statuses_count']
		#all_tweet_ids = {}

		favorite_count_sum = 0
		retweet_count_sum = 0
		#if followers_count > MIN_NUM_OF_FOLLOWERS: #check should be redundant
		for tweet in query_results:
			retweet_count_sum += tweet['retweet_count']
			favorite_count_sum += tweet['favorite_count']
				#all_tweet_ids[tweet['id_str']] = 0
		# else:
			# print "discarded: " + user
			# return None

		avg_favorite_count = favorite_count_sum/len(query_results)
		avg_retweet_count = retweet_count_sum/len(query_results)
		#avg_num_of_replies = extract_avg_num_of_replies(user, all_tweet_ids)
		return {'followers': followers_count, 'numTweets': statuses_count, 'avgLikes': avg_favorite_count, 'avgRetweets': avg_retweet_count}
	
	# ----------------------------------------------------------------------
	# parameters: hashtag
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, }, user2: {}}
	# -----------------------------------------------------------------------
	def __search_twitter_api(self, query):
		potential_influencers = {}
		tweets = self.__api_query_search(query)
		users_hashtag_list = self.__get_users_and_hashtags(tweets)
		user_dict = users_hashtag_list[0]
		print user_dict
		mentioned_users = users_hashtag_list[1]
		
		for user in user_dict:
			user_info = self.__extract_user_timeline_info(user)
			if user_info is not None:
				all_info = user_dict[user].copy()
				all_info.update(user_info)
				print user + ": " + str(all_info)
				potential_influencers[user] = all_info
		return potential_influencers
	
	def __update_cassandra(self, potential_influencers):
		cass = Cassandra('beehive') 
		query = self.hashtag

		for user in potential_influencers:
			# add to tables
			user_info = potential_influencers[user]
			
			cass.new_hashtag(query, user, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], 0)
			
			cassUsers = cass.get_user(user)
			if not cassUsers:
				cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], 1, user_info['numTweets'], 0)
			else: # user already associated with another hashtag. need to update time appeared
				cassUser = cass.get_most_recent_user(user)
				updatedNumAppeared = cassUser.numappeared + 1
				cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], updatedNumAppeared, user_info['numTweets'], 0)

	# ----------------------------------------------------------------------
	# parameters: hashtag
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, 'userRank'}, user2: {}}
	# NEED USER RANK MODIFICATION
	# -----------------------------------------------------------------------
	def search_twitter(self):
		query = self.hashtag
		# if hashtags exists in table, use datatabse, otherwise search twitter
		db = MySQLdb.connect(host="localhost",    # your host, usually localhost
						 user="",         # your username
						 passwd="",  # your password
						 db="beehive")        # name of the data base

		# you must create a Cursor object. It will let
		#  you execute all the queries you need
		cur = db.cursor(MySQLdb.cursors.DictCursor)
		
		potential_influencers = {}
	
		cur.execute("SELECT * FROM Hashtags WHERE hashtag=%s", (query,))
		data = cur.fetchone()
		
		if data is None: #hashtag doesn't exist, search twitter
			print "Hashtag not found. Searching twitter"
			potential_influencers = self.__search_twitter_api(query)
			
			# check database for user rank?
			# for user in potential_influencers:
				# potential_influencers[user]['userRank'] = 0
			try:
				cur.execute("""INSERT INTO Hashtags VALUES (%s, %s, %s)""", (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
				db.commit()
			except:
				db.rollback()
			
			self.__update_cassandra(potential_influencers)
			for user in potential_influencers:
				potential_influencers[user].update({'userRank': 0})
		else:
			#check timestamp
			if data['lastUpdated'] < datetime.now()-timedelta(days=1):	# older than one day, search twitter	
				print "Hashtag too old. Searching twitter"
				potential_influencers = self.__search_twitter_api(query)

				try:
					cur.execute("""UPDATE Hashtags SET lastUpdated=%s, timeSearched=%s WHERE hashtag=%s""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['timeSearched']+1, query))
					db.commit()
				except:
					db.rollback()
					
				self.__update_cassandra(potential_influencers)
				for user in potential_influencers:
					potential_influencers[user].update({'userRank': 0})
			else: # database has updated info
				# go to cassandra
				print "Retrieving data from Cassandra"
				cass = Cassandra('beehive')
				users = cass.get_hashtag(query)
				if users is not None:
					for user in users:
						potential_influencers[user.username] = {'tweetText': user.tweettext, 'tweetCreated': user.tweetcreated, 'followers': user.followers, 'numTweets': user.numtweets, 'avgLikes': user.avglikes, 'avgRetweets': user.avgretweets, 'userRank': user.userrank}
				
					#update timesearched
					print "timesSearched: " + str(data['timeSearched'])
					try:
						cur.execute("""UPDATE Hashtags SET timeSearched=%s WHERE hashtag=%s""", (data['timeSearched']+1, query))
						db.commit()
					except:
						db.rollback()
				else:
					print "mysql and cassandra databases out of sync"
			
		print potential_influencers
		return potential_influencers
				
	#def get_user_info(usernames):

# if __name__ == "__main__":
	# searcher = Search('#ucla2016')
	# searcher.search_twitter()