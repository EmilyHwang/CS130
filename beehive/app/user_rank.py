from cass_orm import Cassandra
from datetime import datetime, timedelta, date

class UserRank:

	def __init__(self, cass):
		self.cass = cass


	def __get_followers_growth(self, user):
		last_week = datetime.now()-timedelta(days=7)
		last_beg = last_week.replace(hour=0, minute=0, second=0, microsecond=0)
		last_end = last_week.replace(hour=23, minute=59, second=59)

		most_recent_users = self.cass.get_most_recent_user(user)

		for most_recent_user in most_recent_users:
			if most_recent_user.lastupdated < datetime.now()-timedelta(days=1):
				print "Most recent user is older than 1 day, using oldest rank"
				return most_recent_user.userrank
			else:
				print "Most recent user is within 1 day"
				curr_user = most_recent_user

		last_users = self.cass.get_user_from_dates(user, last_beg, last_end)

		if not last_users:
			print "no timestamp older than one week found"
			last_users = self.cass.get_oldest_user(user)
			for user in last_users:
				last_user = user
		else:
			print "found user with week old timestamp"
			for temp in last_users:
				last_user = temp

		print "current user follower: " + str(curr_user.followers)
		print "old user followers: " + str(last_user.followers)
		return (curr_user.followers - last_user.followers)/last_user.followers

	def calculate_user_rank(self, avglikes, avgretweets, followers, numtweets, followers_growth, numinteractions):
		return .2*avglikes + .2*avgretweets + .05*followers + .03*numtweets + .202*followers_growth + .3*numinteractions

	def update_users_rank(self):
		hashtags = self.cass.get_all_hashtags()
		for hashtag in hashtags:
			users = self.cass.get_hashtag(hashtag)
			for user in users:
				print user
				followers_growth = self.__get_followers_growth(user.username)
				user_rank = self.calculate_user_rank(user.avglikes, user.avgretweets, user.followers, user.numtweets, followers_growth, user.numinteractions)

				if user_rank != user.userrank:
					# update tables
					print "User rank changed from: " + str(user.userrank) + "to: " + str(user_rank)
					self.cass.update_user_rank(user.username, hashtag.hashtag, user_rank)

if __name__ == "__main__":
	userrank = UserRank()
	userrank.update_users_rank()
