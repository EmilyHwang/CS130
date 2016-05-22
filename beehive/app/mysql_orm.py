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

	def updateHashtag(self, hashtag):
		try:
			self.cur.execute("""UPDATE Hashtags SET lastUpdated=%s, timeSearched=%s WHERE hashtag=%s""", (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), data['timeSearched']+1, hashtag))
			self.db.commit()
		except:
			self.db.rollback()

	def findHashtag(self, hashtag):
		self.cur.execute("""SELECT hashtag FROM Hashtags WHERE hashtag=%s;""", (hashtag,))
		if self.cur.fetchone() is None:
			return False
		else:
			return True
