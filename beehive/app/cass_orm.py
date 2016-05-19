import datetime
import re
from cassandra.cluster import Cluster

class Cassandra(object):
	def __init__(self,keyspace):
		self.keyspace = keyspace
		cluster = Cluster()
		self.session = cluster.connect(self.keyspace)

	###############################################################################
	# func: 	new_hashtag  																												#
	# input:	hashtag, username, tweettext, tweetcreated													#
	# output:																																			#
	# desc:		Insert a hashtag-username pair whenever a hashtag is searched				#
	###############################################################################
	def new_hashtag(self, hashtag, username, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank):
		query = self.session.prepare("""INSERT INTO hashtagusers(hashtag, username, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank) VALUES(?,?,?,?,?,?,?,?,?);""")
		print query
		self.session.execute(query,[hashtag, username, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank])

	def get_hashtag(self, hashtag):
		query = "SELECT * FROM hashtagusers WHERE hashtag = '%s'" % hashtag
		res = self.session.execute(query)
		if not res:
			print "Could not find hashtag: %s" % hashtag
			return None
		else:
			return res
			
	def get_all_hashtags(self):
		query = "SELECT DISTINCT hashtag FROM hashtagusers"
		res = self.session.execute(query)
		if not res:
			print "No hashtags in database"
			return None
		else:
			return res

	###############################################################################
	# func: 	new_user		 																												#
	# input:	username, fullname, lastupdated, avelikes, averetweets, followers, 	#
	#					numappeared, numtweets, userrank																		#
	# output:																																			#
	# desc:		Insert a user with stats to the user table													#
	###############################################################################
	def new_user(self, username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank):
		query = self.session.prepare("""INSERT INTO users(username, fullname, lastupdated, avglikes, avgretweets, followers, numappeared, numtweets, userrank) VALUES(?,?,?,?,?,?,?,?,?);""")
		  
		print query
		self.session.execute(query, [username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank])

	def get_user(self,username):
		query = "SELECT * FROM users WHERE username = '%s'" % username
		res = self.session.execute(query)
		if not res:
		  print "Could not find user: %s" % username
		return res
	
	# the user with most recent timestamp
	def get_most_recent_user(self, username):
		query = "SELECT * FROM users WHERE username = '%s' ORDER BY lastupdated DESC limit 1" % username
		res = self.session.execute(query)
		if not res:
		  print "Could not find most recent user: %s" % username
		return res
		
	# user with oldest timestamp
	def get_oldest_user(self, username):
		query = "SELECT * FROM users WHERE username = '%s' ORDER BY lastupdated ASC limit 1" % username
		res = self.session.execute(query)
		if not res:
		  print "Could not find oldest user: %s" % username
		return res

	def get_user_from_hashtag(self,hashtag):
		query = "SELECT username FROM hashtagusers WHERE hashtag = '%s'" % hashtag
		res = self.session.execute(query)
		return res
	
	# user within given time range
	def get_user_from_dates(self, user, date_beg, date_end):
		query = session.prepare("""SELECT * from users where username=? and lastupdated > ? and lastupdated < ?;""")
		res = self.session.execute(query, [user, date_beg, date_end])
		if not res:
			print "no user and timestamp in that date"
			return None
		else:
			return res
##############################################################################################################
#
# Update both tables
#
###################################################################################################

	# used update both tables in user_rank.py
	def update_user_rank(self, username, hashtag, user_rank):
		query1 = session.prepare("""UPDATE hashtagusers SET userrank = ? WHERE username = ? and hashtag = ?;""")
		query2 = session.prepare("""UPDATE users SET userrank = ? WHERE username = ? and lastupdated = ?;""")
		
		most_recent_users = self.get_most_recent_user(username)
	
		for most_recent_user in most_recent_users:
			most_recent_updated = most_recent_user.lastupdated
		
		self.session.execute(query1, [user_rank, username, hashtag])
		self.session.execute(query2, [user_rank, username, most_recent_updated])
