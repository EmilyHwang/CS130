import datetime
import re
from cassandra.cluster import Cluster

import logging
logfile = logging.getLogger('file')

class Cassandra(object):
	def __init__(self,keyspace):
		self.keyspace = keyspace
		cluster = Cluster()
		self.session = cluster.connect(self.keyspace)

	###############################################################################
	# func:		new_hashtag																													#
	# input:	hashtag, username, tweettext, tweetcreated													#
	# output:																																			#
	# desc:		Insert a hashtag-username pair whenever a hashtag is searched				#
	###############################################################################
	def new_hashtag(self, hashtag, username, fullname, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank, numinteractions):
		logfile.info("Inserting/Updateing to hashtagusers table: #%s" % hashtag)
		query = self.session.prepare("""INSERT INTO hashtagusers(hashtag, username, fullname, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank, numinteractions) VALUES(?,?,?,?,?,?,?,?,?,?,?);""")
		self.session.execute(query,[hashtag, username, fullname, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank, numinteractions])

	def get_hashtag(self, hashtag):
		logfile.info("Query * from hashtagusers : #%s" % hashtag)
		query = "SELECT * FROM hashtagusers WHERE hashtag = '%s'" % hashtag
		res = self.session.execute(query)
		if not res:
			logfile.warning("Could not find hashtag: #%s" % hashtag)
			return None
		else:
			return res
			
	def get_all_hashtags(self):
		logfile.info("Get all hashtags")
		query = "SELECT DISTINCT hashtag FROM hashtagusers"
		res = self.session.execute(query)
		if not res:
			logfie.warning("No hashtags in database")
			return None
		else:
			return res
	
	def get_user_hashtag(self, username, hashtag):
		logfile.info("Get * from hashtagusers table by username: %s and hashtag: %s" % (username, hashtag))
		query = self.session.prepare("""SELECT * FROM hashtagusers WHERE hashtag = ? and username = ?;""")
		res = self.session.execute(query, [hashtag, username])
		if not res:
			logfile.warning("Could not find hashtag and username: %s, %s" % (hashtag, username))
			return None
		else:
			return res
			
	# used to increment numinteractiosn everytime someone is followed
	# numInteraction in users table is sum of all interactions in hashtagUser
	def update_num_interaction_create(self, username, hashtag):
		logfile.info("Update Number interactions create for user %s and hashtag %s" % (username, hashtag))
		query1 = self.session.prepare("""UPDATE hashtagusers SET numinteractions = ? WHERE username = ? and hashtag = ?;""")
		users = self.get_user_hashtag(username, hashtag)
		if users:
			for user in users:
				num_to_update = user.numinteractions + 1
		else:
			logfile.error("Error in database, trying to update interaction for non-existing user/hashtat")
				
		self.session.execute(query1, [num_to_update, username, hashtag])
		
	def update_num_interaction_destroy(self, username, hashtag):
		logfile.info("Update Number interactions destroy for user %s and hashtag %s" % (username, hashtag))
		query1 = self.session.prepare("""UPDATE hashtagusers SET numinteractions = ? WHERE username = ? and hashtag = ?;""")
		users = self.get_user_hashtag(username, hashtag)
		if users:
			for user in users:
				num_to_update = user.numinteractions - 1
		else:
			logfile.error("Error in database, trying to update interaction for non-existing user/hashtat")
				
		self.session.execute(query1, [num_to_update, username, hashtag])
	
	###############################################################################
	# func:		new_user																														#
	# input:	username, fullname, lastupdated, avelikes, averetweets, followers,	#
	#					numappeared, numtweets, userrank																		#
	# output:																																			#
	# desc:		Insert a user with stats to the user table													#
	###############################################################################
	def new_user(self, username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank):
		query = self.session.prepare("""INSERT INTO users(username, fullname, lastupdated, avglikes, avgretweets, followers, numappeared, numtweets, userrank) VALUES(?,?,?,?,?,?,?,?,?);""")
		self.session.execute(query, [username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank])

	def get_user(self,username):
		query = "SELECT * FROM users WHERE username = '%s'" % username
		res = self.session.execute(query)
		if not res:
		  logfile.error("Could not find user: %s" % username)
		return res
	
	# the user with most recent timestamp
	def get_most_recent_user(self, username):
		query = "SELECT * FROM users WHERE username = '%s' ORDER BY lastupdated DESC limit 1" % username
		res = self.session.execute(query)
		if not res:
		  logfile.error("Could not find user: %s" % username)
		return res
		
	# user with oldest timestamp
	def get_oldest_user(self, username):
		query = "SELECT * FROM users WHERE username = '%s' ORDER BY lastupdated ASC limit 1" % username
		res = self.session.execute(query)
		if not res:
		  logfile.error("Could not find user: %s" % username)
		return res
	
	# user within given time range
	def get_user_from_dates(self, user, date_beg, date_end):
		query = self.session.prepare("""SELECT * from users where username=? and lastupdated > ? and lastupdated < ?;""")
		res = self.session.execute(query, [user, date_beg, date_end])
		if not res:
			logfile.error("no user and timestamp in that date")
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
		query1 = self.session.prepare("""UPDATE hashtagusers SET userrank = ? WHERE username = ? and hashtag = ?;""")
		query2 = self.session.prepare("""UPDATE users SET userrank = ? WHERE username = ? and lastupdated = ?;""")
		
		most_recent_users = self.get_most_recent_user(username)
	
		for most_recent_user in most_recent_users:
			most_recent_updated = most_recent_user.lastupdated
		
		self.session.execute(query1, [user_rank, username, hashtag])
		self.session.execute(query2, [user_rank, username, most_recent_updated])

	#####################################################
	# USED FOR TESTING 
	#################################################
	def delete_hashtag(self, username, hashtag):
		query1 = self.session.prepare("""DELETE FROM hashtagusers WHERE username = ? and hashtag = ?;""")
		
		self.session.execute(query1, [username, hashtag])

	def delete_user(self, username, timestamp):
		query1 = self.session.prepare("""DELETE FROM users WHERE username = ? and lastupdated = ?;""")
			
		self.session.execute(query1, [username, timestamp])
