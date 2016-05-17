
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

class Search:
	def __init__(self, query, max_tweets=MAX_TWEETS, max_user_timeline_tweets=MAX_USER_TIMELINE_TWEETS):
		q = "#" + query
		self.hashtag = q.lower()
		self.max_tweets = max_tweets
		self.max_user_timeline_tweets = max_user_timeline_tweets
	
	def __api_query_search(self, query):
		data = Cursor(api.search, q=query, result_type="recent", count=100).items(self.max_tweets)

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
			if tweet['user']['followers_count'] > MIN_NUM_OF_FOLLOWERS:
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

			return {'followers': followers_count, 'numTweets': statuses_count, 'avgLikes': avg_favorite_count, 'avgRetweets': avg_retweet_count}

	# ----------------------------------------------------------------------
	# parameters: hashtag
	# returns: {user: {'tweetText', 'tweetCreated', 'followers': x, 'numTweets': y', 'avgLikes': z, 'avgRetweets': a, }, user2: {}}
	# -----------------------------------------------------------------------
	def search_twitter_api(self, query):
		potential_influencers = {}
		tweets = self.__api_query_search(query)
		users_hashtag_list = self.__get_users_and_hashtags(tweets)
		user_dict = users_hashtag_list[0]
		print user_dict
		mentioned_users = users_hashtag_list[1]
		
		# This is where we parallelize
		# Each 
		for user in user_dict:
			user_info = self.query_user_timeline(user)
			if user_info is not None:
				all_info = user_dict[user].copy()
				all_info.update(user_info)
				print user + ": " + str(all_info)
				potential_influencers[user] = all_info
		return potential_influencers
	
	def update_cassandra(self, potential_influencers):
		cass = Cassandra('beehive') 
		query = self.hashtag

		for user in potential_influencers:
			# add to tables
			user_info = potential_influencers[user]
			
			userrank = UserRank(cass)
			rank = userrank.calculate_user_rank(user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], 0)
			
			cassUsers = cass.get_user(user)
			if not cassUsers:
				cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], 1, user_info['numTweets'], rank)
				
				cass.new_hashtag(query, user, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], rank)
				potential_influencers[user]['userRank'] = rank
				
			else: # user already associated with another hashtag. need to update time appeared
				cassUsers = cass.get_most_recent_user(user)
				for most_recent_user in cassUsers:
					cassUser = most_recent_user
				updatedNumAppeared = cassUser.numappeared + 1
				cass.new_user(user, user_info['fullname'], datetime.now(), user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], updatedNumAppeared, user_info['numTweets'], cassUser.userrank)
				
				cass.new_hashtag(query, user, user_info['avgLikes'], user_info['avgRetweets'], user_info['followers'], user_info['numTweets'], user_info['tweetCreated'], user_info['tweetText'], cassUser.userrank)
				potential_influencers[user]['userRank'] = rank
				
		return potential_influencers
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
			potential_influencers = self.search_twitter_api(query)
			
			# check database for user rank?
			# for user in potential_influencers:
				# potential_influencers[user]['userRank'] = 0
			try:
				cur.execute("""INSERT INTO Hashtags VALUES (%s, %s, %s)""", (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
				db.commit()
			except:
				db.rollback()

			self.update_cassandra(potential_influencers)
		else:
			#check timestamp
			if data['lastUpdated'] < datetime.now()-timedelta(days=1):	# older than one day, search twitter	
				print "Hashtag too old. Searching twitter"
				potential_influencers = self.search_twitter_api(query)

				try:
					cur.execute("""UPDATE Hashtags SET lastUpdated=%s, timeSearched=%s WHERE hashtag=%s""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['timeSearched']+1, query))
					db.commit()
				except:
					db.rollback()
					
				self.update_cassandra(potential_influencers)
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

if __name__ == "__main__":
	searcher = Search('#fitspo')
	a = searcher.query_user_timeline("chelseahandler")
	#print a