from tweepy import *
import os
import logging

logfile = logging.getLogger('file')

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']

class UserAuth:
	def __init__(self, access_token, access_token_secret, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET):
		
		logfile.info("Initialize UserAuth")
		self.auth = OAuthHandler(consumer_key, consumer_secret)
		self.auth.set_access_token(access_token, access_token_secret)	
	
	def create_api(self):
		logfile.info("Create UserAuth")
		return API(self.auth, wait_on_rate_limit=False, retry_count=2, retry_delay=2, retry_errors=set([500, 503]))

class AppAuth:
	def __init__(self, consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET):

		logfile.info("Initialize AppAuth")
		self.auth = AppAuthHandler(consumer_key, consumer_secret)
	
	def create_api(self):

		logfile.info("Create AppAuth")
		return API(self.auth, wait_on_rate_limit=False, retry_count=2, retry_delay=2, retry_errors=set([500, 503]))