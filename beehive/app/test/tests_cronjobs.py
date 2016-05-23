import unittest
from user_rank import UserRank
from datetime import datetime, timedelta
from cass_orm import Cassandra

class UserRankTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		#insert user to database
		self.cass = Cassandra('beehive')
		self.user_rank = UserRank(self.cass)

		self.hashtag = "#testingBeehive"
		self.username = "beehiveTestUser"
		self.fullname = "beehive"
		self.avglikes = 3
		self.avgretweets = 5
		self.followers = 100
		self.numtweets = 200
		self.tweetcreated = datetime.now()
		self.tweettext = "hello beehive"
		self.userrank = 0
		self.numinteractions = 0
		self.cass.new_hashtag(self.hashtag, self.username, self.fullname, self.avglikes, self.avgretweets, self.followers, self.numtweets, self.tweetcreated, self.tweettext, self.userrank, self.numinteractions) 
		self.cass.new_user(self.username, self.fullname, self.tweetcreated, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		
		self.last_week = self.tweetcreated-timedelta(days=7)
		self.cass.new_user(self.username, self.fullname, self.last_week, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
	
	def tearDown(self):
		 """Call after every test case."""
		 self.cass.delete_hashtag(self.username, self.hashtag)
		 self.cass.delete_user(self.username, self.tweetcreated)
		 self.cass.delete_user(self.username, self.last_week)
	
	def testGetFollowersGrowth(self):
		assert self.user_rank.get_followers_growth(self.username) == 0
	
	def testCalculateUserRank(self):
		assert self.user_rank.calculate_user_rank(self.avglikes, self.avgretweets, self.followers, self.numtweets, 0, self.numinteractions) == 12.6

if __name__ == "__main__":
	unittest.main() # run all tests