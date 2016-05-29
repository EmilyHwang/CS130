# So calling rand_influencers.get_users(x) will return a json object with x users. There's a sample what the object will
# look like here: https://dev.twitter.com/rest/reference/get/users/lookup and https://dev.twitter.com/rest/reference/get/users/show
# Example of how I parsed it:
	# # convert from json
	# # users_data = []
	# # for user in users_results:
		# # users_data.append(json.loads(json.dumps(user._json)))

	# # for user in users_data:
	# #	print user['screen_name']
# The stats I think you'll want to pay attention to
	# user['screen_name']
	# user['name']
	# user['profile_image_url']
	# user['status']['text']
	# user['status']['retweet_count']
	# user['status']['favorite_count']
	# user['entities']['media']['display_url']

#!/usr/bin/python
import MySQLdb
import json
import twitter_auth

from orm.mysql_orm import MySQL

mysql = MySQL('beehive')

# -----------------------------------------------------------------------
# searches users - get most recent status
# parameters: list of users as screen_names
# returns: [full name, status]
# -----------------------------------------------------------------------
def get_users_info(usernames):
	auth = twitter_auth.AppAuth()
	api = auth.create_api()

	users_results = api.lookup_users(screen_names=usernames)

	users_data = []
	for user in users_results:
		users_data.append(json.loads(json.dumps(user._json)))
	return users_data

# Main functions
def get_users(number):
	users = mysql.getRandomUsers(number, None)
	users_info = get_users_info(users)
	return users_info

def get_users_by_category(number, category):
	users = mysql.getRandomUsers(number, category)
	users_info = get_users_info(users)
	return users_info
