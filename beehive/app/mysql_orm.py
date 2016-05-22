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
		self.cur.execute("""SELECT * FROM Hashtags WHERE hashtag=%s;""", (hashtag,))
		return self.cur.fetchone()

	def newHashtag(self, hashtag):
		try:
			logfile.info("Update Hashtag table")
			self.cur.execute("""INSERT INTO Hashtags VALUES (%s, %s, %s)""", (query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
			self.db.commit()
		except:
			self.db.rollback()
