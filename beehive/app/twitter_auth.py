from tweepy import *
import os

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']

class UserAuth:
	def __init__(self, access_token, access_token_secret, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET):
		
		self.auth = OAuthHandler(consumer_key, consumer_secret)
		self.auth.set_access_token(access_token, access_token_secret)	
	
	def create_api(self):
		return API(self.auth, wait_on_rate_limit=True)

class AppAuth:
	def __init__(self, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET):
		self.auth = AppAuthHandler(consumer_key, consumer_secret)
	
	def create_api(self):
		return API(self.auth, wait_on_rate_limit=True)