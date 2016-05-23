import unittest
from twitter_search import Search
from twitter_interact import Interact
import twitter_auth
import os
from datetime import datetime
from cass_orm import Cassandra
from mysql_orm import MySQL
from collections import OrderedDict

access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

class SearchTestCase(unittest.TestCase):
	def setUp(self):
		"""Call before every test case."""
		query = "instafood"
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		self.search = Search(query, auth)
	
	def tearDown(self):
		 """Call after every test case."""
		 pass
		 
	### MAKE SURE test case name starts with test
	def testSearchUser(self):
		results = self.search.search_users()

		# Make sure mysql is updated
		mysql = MySQL('beehive')
		self.assertTrue(mysql.findHashtag('#instafood'))

		# search again
		results = self.search.search_users()
		self.assertTrue(mysql.findHashtag('#instafood'))


	def testGetUsersAndHashtags(self):
		result_triplets = self.search.get_users_and_hashtags()
		users = result_triplets[0]
		anyitem = users.itervalues().next()
		self.assertTrue('fullname' in anyitem)
		self.assertTrue('tweetText' in anyitem)
		self.assertTrue('tweetCreated' in anyitem)

	def testQueryUserTimeline(self):
		user = 'kobebryant'
		user_info = self.search.query_user_timeline(user)

		self.assertTrue('fullname' in user_info)
		self.assertTrue('followers' in user_info)
		self.assertTrue('numTweets' in user_info)
		self.assertTrue('avgLikes' in user_info)
		self.assertTrue('avgRetweets' in user_info)

	def testUpdateCassandra(self):
		cass = Cassandra('beehive')

		empty_potential_influencers = {}
		self.search.update_cassandra(empty_potential_influencers)

		cur_time = datetime.now()
		potential_influencers = {'pigrabbit87': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': cur_time, 
																						 'followers': 100, 'numTweets': 100, 'avgLikes': 0, 'avgRetweets': 0, 
																						 'userRank': 0}}
		# This user is not yet in the database
		self.search.update_cassandra(potential_influencers)
		cassUser = cass.get_user('pigrabbit87')[0]
		self.assertIsNotNone(cassUser)
		self.assertEqual(cassUser.fullname, 'Irene Yeh')
		self.assertEqual(cassUser.username, 'pigrabbit87')
		self.assertEqual(cassUser.followers, 100)
		self.assertEqual(cassUser.numtweets, 100)
		self.assertEqual(cassUser.avglikes, 0)
		self.assertEqual(cassUser.avgretweets, 0)
		time_appeared = cassUser.numappeared

		# update again, check time appeared
		potential_influencers['pigrabbit87']['followers'] = 5000
		self.search.update_cassandra(potential_influencers)
		cassUser = cass.get_most_recent_user('pigrabbit87')[0]
		self.assertEqual(cassUser.followers, 5000)
		self.assertEqual(cassUser.numappeared, time_appeared + 1)

		cass.delete_hashtag('pigrabbit87', '#instafood')
		cass.delete_user_without_time('pigrabbit87')

	def testSearchUsersDetail(self):
		cass = Cassandra('beehive')

		# Empty users
		empty_users = {}
		result = self.search.search_users_detail(empty_users)
		self.assertTrue(len(result['first_10']) == 0)
		self.assertTrue(len(result['leftover']) == 0)

		# New Search, everybody is dictionary users
		users_dict = {'kobebryant': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'katyperry': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'taylorswift13': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'BarackObama': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'YouTube': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'rihanna': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'TheEllenShow': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'ladygaga': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'jtimberlake': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'twitter': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'KimKardashian': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()},
									'selenagomez': {'fullname': 'Irene Yeh', 'tweetText': 'I love boba <3', 'tweetCreated': datetime.now()}}
		results = self.search.search_users_detail(users_dict)
		first_10 = results['first_10']
		self.assertEqual(len(first_10), 10)

		leftover = results['leftover']
		self.assertEqual(len(leftover), 2)

		# Call again
		results = self.search.search_users_detail(leftover)
		first_10 = results['first_10']
		self.assertEqual(len(first_10), 2)

		leftover = results['leftover']
		self.assertEqual(len(leftover), 0)

		Old Search, everybody is cassandra users
		cassUsers = cass.get_hashtag('#instafood')

		results = self.search.search_users_detail(cassUsers)
		first_10 = results['first_10']
		leftover = results['leftover']

		self.assertEqual(len(first_10), 76)
		while len(leftover) != 0:
			results = self.search.search_users_detail(leftover)
			first_10.update(results['first_10'])
			leftover = results['leftover']

		for item in first_10:
			self.assertNotEqual(first_10[item]['followers'], 0)

		cass.delete_hashtag('kobebryant', '#instafood')
		cass.delete_user_without_time('kobebryant')
		cass.delete_hashtag('katyperry', '#instafood')
		cass.delete_user_without_time('katyperry')
		cass.delete_hashtag('taylorswift13', '#instafood')
		cass.delete_user_without_time('taylorswift13')
		cass.delete_hashtag('BarackObama', '#instafood')
		cass.delete_user_without_time('BarackObama')
		cass.delete_hashtag('YouTube', '#instafood')
		cass.delete_user_without_time('YouTube')
		cass.delete_hashtag('rihanna', '#instafood')
		cass.delete_user_without_time('rihanna')
		cass.delete_hashtag('TheEllenShow', '#instafood')
		cass.delete_user_without_time('TheEllenShow')
		cass.delete_hashtag('ladygaga', '#instafood')
		cass.delete_user_without_time('ladygaga')
		cass.delete_hashtag('jtimberlake', '#instafood')
		cass.delete_user_without_time('jtimberlake')
		cass.delete_hashtag('twitter', '#instafood')
		cass.delete_user_without_time('twitter')
		cass.delete_hashtag('KimKardashian', '#instafood')
		cass.delete_user_without_time('KimKardashian')
		cass.delete_hashtag('selenagomez', '#instafood')
		cass.delete_user_without_time('selenagomez')

		
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