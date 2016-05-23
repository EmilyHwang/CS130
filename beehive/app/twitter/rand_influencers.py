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
import twitter
import string

# pulls random users from database
def find_users(number):
	db = MySQLdb.connect(host="localhost",    # your host, usually localhost
						 user="",             # your username
						 passwd="",           # your password
						 db="beehive")        # name of the data base

	# you must create a Cursor object. It will let
	# you execute all the queries you need
	cur = db.cursor()

	users = []
	# Use all the SQL you like
	cur.execute("SELECT subCategoryId FROM Categories ORDER BY RAND() LIMIT %s", (number,))
	subCatIds = cur.fetchall()
	for id in subCatIds:
		cur2 = db.cursor()
		cur2.execute("""SELECT username FROM SubCategoryPeople WHERE subCategoryId = %s""", id)
		(username,) = cur2.fetchone()
		users.append(username)
	return users


# pull random users from database with specified category
def find_users_by_category(number, category):
	db = MySQLdb.connect(host="localhost",    # your host, usually localhost
						 user="",             # your username
						 passwd="",           # your password
						 db="beehive")        # name of the data base
	cur_id = db.cursor()
	users = []

	# Use all the SQL you like
	formatted_category = string.replace(category, '&', '&amp;')
	cur_id.execute("SELECT subCategoryId FROM Categories WHERE subCategory = %s", (formatted_category,))
	subCatId = cur_id.fetchone()
	cur_users = db.cursor()
	cur_users.execute("""SELECT username FROM SubCategoryPeople WHERE subCategoryId = %s ORDER BY RAND() LIMIT %s""", (subCatId, number))
	usernames = cur_users.fetchall()
	for (user,) in usernames:
		users.append(user)
	return users

# Main functions
def get_users(number):
	users = find_users(number)
	users_info = twitter.get_users_info(users)
	return users_info

def get_users_by_category(number, category):
	users = find_users_by_category(number, category)
	users_info = twitter.get_users_info(users)
	return users_info
