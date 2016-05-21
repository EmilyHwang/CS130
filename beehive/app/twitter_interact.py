#!/usr/bin/python
from tweepy import *
from cass_orm import Cassandra

class Interact:
	def __init__(self, query, auth):
		self.hashtag = "#" + query
		self.auth = auth
		self.api = auth.create_api()
		
	def follow_user(self, user_to_follow):
		if not self.is_following_user(user_to_follow):
			self.api.create_friendship(screen_name=user_to_follow)
		else:
			print "Friendship exists"
			return False
		# Update cassandra
		cass = Cassandra('beehive') 
		cass.update_num_interaction_create(user_to_follow, self.hashtag)
		return True
			
	def is_following_user(self, user_to_follow):
		curr_user = self.api.me().screen_name
		print "ME: " + curr_user
		print "target: " + user_to_follow
		return self.api.show_friendship(target_screen_name=user_to_follow)[1].followed_by
		
	def unfollow_user(self, user_to_unfollow):
		if self.is_following_user(user_to_unfollow):
			self.api.destroy_friendship(screen_name=user_to_unfollow)
		else:
			print "Friendship doesn't exist, can't unfollow"
			return False
		# Update cassandra
		cass = Cassandra('beehive') 
		cass.update_num_interaction_destroy(user_to_unfollow, self.hashtag)
		return True