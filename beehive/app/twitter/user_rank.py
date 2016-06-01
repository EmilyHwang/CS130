from orm.cass_orm import Cassandra
from datetime import datetime, timedelta, date
import logging

logfile = logging.getLogger('file')

class UserRank:

	def __init__(self, cass):
		self.cass = cass


	def get_followers_growth(self, user):
		last_week = datetime.now()-timedelta(days=7)
		last_beg = last_week.replace(hour=0, minute=0, second=0, microsecond=0)
		last_end = last_week.replace(hour=23, minute=59, second=59)

		most_recent_users = self.cass.get_most_recent_user(user)

		for most_recent_user in most_recent_users:
			if most_recent_user.lastupdated < datetime.now()-timedelta(days=1):
				return most_recent_user.userrank
			else:
				curr_user = most_recent_user
				if not curr_user:
					print "no user exists"
					return 0

		last_users = self.cass.get_user_from_dates(user, last_beg, last_end)

		if not last_users:
			last_users = self.cass.get_oldest_user(user)
			for user in last_users:
				last_user = user
		else:
			for temp in last_users:
				last_user = temp

		return (curr_user.followers - last_user.followers)/last_user.followers

	def calculate_user_rank(self, avglikes, avgretweets, followers, numtweets, followers_growth, numinteractions):
		return .5*avglikes + .5*avgretweets + .1*followers + .001*numtweets + .6*followers_growth + .6*numinteractions
		
	def update_users_rank(self):
		logfile.info("====== Update User Ranking ======")

		hashtags = self.cass.get_all_hashtags()
		for hashtag in hashtags:
			users = self.cass.get_hashtag(hashtag)
			for user in users:
				followers_growth = self.get_followers_growth(user.username)
				user_rank = self.calculate_user_rank(user.avglikes, user.avgretweets, user.followers, user.numtweets, followers_growth, user.numinteractions)

				if user_rank != user.userrank:
					# update tables
					logfile.info("User rank changed from: " + str(user.userrank) + "to: " + str(user_rank))
					self.cass.update_user_rank(user.username, hashtag.hashtag, user_rank)

if __name__ == "__main__":
	cass = Cassandra('beehive')
	userrank = UserRank(cass)
	userrank.update_users_rank()