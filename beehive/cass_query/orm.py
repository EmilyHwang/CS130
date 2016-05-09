import datetime
from cassandra.cluster import Cluster

KEYSPACE = 'beehive'
cluster = Cluster()
session = cluster.connect(KEYSPACE)

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
		query = """
		INSERT INTO hashtagusers(hashtag, username, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank)
		VALUES('%s','%s',%s,%s,%s,%s,'%s','%s',%s)
		""" % \
		  (hashtag, username, avglikes, avgretweets, followers, numtweets, tweetcreated, tweettext, userrank)
		print query
		self.session.execute(query)

	def get_hashtag(self, hashtag):
		query = "SELECT * FROM hashtagusers WHERE hashtag = '%s'" % hashtag
		res = self.session.execute(query)
		if not res:
			print "Could not find hashtag: %s" % hashtag
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
		query = """
		INSERT INTO users(username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank)
		VALUES('%s','%s','%s',%s,%s,%s,%s,%s,%s)
		""" % \
		  (username, fullname, lastupdated, avelikes, averetweets, followers, numappeared, numtweets, userrank)
		print query
		self.session.execute(query)

	def get_user(self,username):
		query = "SELECT * FROM users WHERE username = '%s'" % username
		res = self.session.execute(query)
		if not res:
		  print "Could not find user: %s" % username
		else:
		  for r in res:
		      print r.username,r.avelikes,r.averetweets,r.followers,r.fullname,r.numappeared,r.numstatus,r.numtweets,r.updatedtime
