import unittest
from twitter_search import Search
from twitter_interact import Interact
import twitter_auth
import os

access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

class SearchTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		query = "ucla2016"
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		self.search = Search(query, auth)
	
	def tearDown(self):
		 """Call after every test case."""
		 pass
		 
	### MAKE SURE test case name starts with test
	def testSearchUser(self):
		#self.assert blah blah blah
		pass
		
class InteractTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		query = "ucla2016"
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		self.interact = Interact(query, auth)
		self.user_to_follow = "UCLA"
	
	def tearDown(self):
		 """Call after every test case."""
		 self.interact.unfollow_user(self.user_to_follow)
	
	def testFollowUnfollowed(self):
		self.assertFalse(self.interact.is_following_user(self.user_to_follow))
		self.interact.follow_user(self.user_to_follow)
		self.assertTrue(self.interact.is_following_user(self.user_to_follow))
		self.interact.unfollow_user(self.user_to_follow)
		self.assertFalse(self.interact.is_following_user(self.user_to_follow))
	
	def testUnFollowUnfollowed(self):
		self.assertFalse(self.interact.unfollow_user(self.user_to_follow))
	
	def testFollowFollowed(self):
		self.interact.follow_user(self.user_to_follow)
		self.assertFalse(self.interact.follow_user(self.user_to_follow))
	

if __name__ == "__main__":
	unittest.main() # run all tests