from orm import Cassandra
import datetime

c = Cassandra('beehive')
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# c.new_hashtag('ucla2016', 'ireneyeh', 5, 1, 100, 12, timestamp, 'today is awesome', 0)
# c.new_hashtag('ucla2016', 'kurtisv', 6, 2, 200, 12, timestamp, 'today is awesome too', 0)

users = c.get_hashtag('#ucla2016')

if users is not None:
	for user in users:
		res = c.get_most_recent_user(user.username)
		for r in res:
			print r.username
			print r.lastupdated
		