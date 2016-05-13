import MySQLdb

class MySQL(object):
	def __init__(self, database):
		self.database = database
		self.db = MySQLdb.connect(host="localhost",    # your host, usually localhost
				 user="",         # your username
				 passwd="",  # your password
				 db=self.database)        # name of the data base

		self.cur = self.db.cursor(MySQLdb.cursors.DictCursor)

	# Return a set
	def getHashtags(self):
		self.cur.execute("""SELECT hashtag FROM Hashtags;""")
		arr = set()
		for i in self.cur.fetchall():
			arr.add(i["hashtag"])
		return arr

