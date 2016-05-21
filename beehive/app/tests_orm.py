import unittest
from datetime import datetime, timedelta
from cass_orm import Cassandra

class CassOrmTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		#insert user to database
		self.cass = Cassandra('beehive')
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
		
	def tearDown(self):
		 """Call after every test case."""
		 self.cass.delete_hashtag(self.username, self.hashtag)
		 self.cass.delete_user(self.username, self.tweetcreated)
	
	def testNewAndGetHashtag(self):
		self.cass.new_hashtag(self.hashtag, self.username, self.fullname, self.avglikes, self.avgretweets, self.followers, self.numtweets, self.tweetcreated, self.tweettext, self.userrank, self.numinteractions) 
		self.assertIsNotNone(self.cass.get_hashtag(self.hashtag))
		self.assertIsNotNone(self.cass.get_user_hashtag(self.username, self.hashtag))
		self.cass.delete_hashtag(self.username, self.hashtag)
	
	def testUpdateNumInteractionCreateDestroy(self):
		self.cass.new_hashtag(self.hashtag, self.username, self.fullname, self.avglikes, self.avgretweets, self.followers, self.numtweets, self.tweetcreated, self.tweettext, self.userrank, self.numinteractions) 
		self.cass.update_num_interaction_create(self.username, self.hashtag)
		users = self.cass.get_user_hashtag(self.username, self.hashtag)
		if users:
			for user in users:
				self.assertEqual(user.numinteractions, 1)
		self.cass.update_num_interaction_destroy(self.username, self.hashtag)
		users = self.cass.get_user_hashtag(self.username, self.hashtag)
		if users:
			for user in users:
				self.assertEqual(user.numinteractions, 0)
		self.cass.delete_hashtag(self.username, self.hashtag)

	def testNewGetUser(self):
		self.cass.new_user(self.username, self.fullname, self.tweetcreated, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		self.assertIsNotNone(self.cass.get_user(self.username))
		self.cass.delete_user(self.username, self.tweetcreated)
	
	def testGetMostRecentOldestUser(self):
		self.cass.new_user(self.username, self.fullname, self.tweetcreated, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		
		last_week = self.tweetcreated-timedelta(days=7)
		self.cass.new_user(self.username, self.fullname, last_week, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		
		most_recent_users = self.cass.get_most_recent_user(self.username)
	
		for most_recent_user in most_recent_users:
			print most_recent_user.username
			most_recent_updated = most_recent_user.lastupdated
			self.assertEqual(most_recent_updated, self.tweetcreated)
		
		oldest_users = self.cass.get_oldest_user(self.username)
	
		for old_user in oldest_users:
			old_updated = old_user.lastupdated
			self.assertEqual(old_updated, last_week)
		
		self.cass.delete_user(self.username, self.tweetcreated)
		self.cass.delete_user(self.username, last_week)
	
	def testGetUserFromDates(self):
		self.cass.new_user(self.username, self.fullname, self.tweetcreated, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		beg = self.tweetcreated.replace(hour=0, minute=0, second=0, microsecond=0)
		end = self.tweetcreated.replace(hour=23, minute=59, second=59)
		self.assertIsNotNone(self.cass.get_user_from_dates(self.username, beg, end))
		self.cass.delete_user(self.username, self.tweetcreated)
	
	def testUpdateUserRank(self):
		self.cass.new_user(self.username, self.fullname, self.tweetcreated, self.avglikes, self.avgretweets, self.followers, 1, self.numtweets, self.userrank)
		self.cass.update_user_rank(self.username, self.hashtag, 1000)
		users = self.cass.get_user_hashtag(self.username, self.hashtag)
	
		for user in users:
			self.assertEqual(user.userrank, 1000)
		self.cass.delete_user(self.username, self.tweetcreated)

class MySqlOrmTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		#insert user to database
		pass
		
	def tearDown(self):
		"""Call after every test case."""
		pass

if __name__ == "__main__":
	unittest.main() # run all tests