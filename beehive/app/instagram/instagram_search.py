#!/bin/python

#otterpup94
#access_token = "3275043577.88c6f49.ab2bbffc632948eebab73ca5b0b52569"
		
import urllib, json
from collections import Counter

MAX_TWEETS = 100
MAX_USER_TIMELINE_TWEETS = 200
MIN_NUM_OF_FOLLOWERS = 100

class InstagramSearch:
	def __init__(self, access_token, tag):
		self.access_token = access_token
		self.hashtag = tag
		
	# input: hashtag
	# out: { pagination: "min_tag_id", data:" [{}, {}]
	def api_tag_recent_media(self):
		urlInstagram = "https://api.instagram.com/v1/tags/" + self.hashtag + "/media/recent?access_token=" + self.access_token
		response = urllib.urlopen(urlInstagram)
		return json.loads(response.read())
		
	def api_users_user_id(self, user_id):
		urlInstagram = "https://api.instagram.com/v1/users/" + user_id + "/?access_token=" + self.access_token
		response = urllib.urlopen(urlInstagram)
		return json.loads(response.read())

	def api_users_user_id_media_recent(self, user_id):
		urlInstagram = "https://api.instagram.com/v1/users/" + user_id + "/media/recent?access_token=" + self.access_token
		response = urllib.urlopen(urlInstagram)
		return json.loads(response.read())
		
	def get_user_info(self, user_id):
		user_posts = self.api_users_user_id_media_recent(user_id)['data']
		
		sum_likes = 0
		total_num_posts = 0
		for post in user_posts:
			total_num_posts += 1
			sum_likes += post['likes']['count']
		
		avg_likes = sum_likes/total_num_posts
		return {'avgLikes' : avg_likes, 'avgRetweets' : 0}

	#returns {'username': {followers, numTweets, avgLikes, avgRetweets:0}}
	def search_instagram(self):
		print "SEARCHING INSTAGRAM"
		# go search instagram
		json_response = self.api_tag_recent_media(self.hashtag)
		pagination = json_response['pagination']
		data = json_response['data']
		influencers = {}

		for post in data:
			user_id = post['user']['id']
			user_info = self.api_users_user_id(user_id)['data']
			username = user_info['username']
			user_dict = {'followers': user_info['counts']['followed_by'], 'numTweets': user_info['counts']['media']}
			user_dict.update(get_user_info(user_id))
			influencers[username] = user_dict
		
		print influencers
		return influencers

	