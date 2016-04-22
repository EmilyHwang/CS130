
#!/usr/bin/python


from tweepy import *
import json

from collections import Counter

#-----------------------------------------------------------------------
# API credentials and other global variables
#-----------------------------------------------------------------------
access_token = "722946575224283136-tBg9rusqZzvlRh7xEYVe0BSa6AvkGPD"
access_token_secret = "b45lsA2ZBh00lvCTZms0reK6Mg4FkRosewWMYsTVl1eEb"
consumer_key = "hnj89shYGLhgfmuazbzjLkDk5"
consumer_secret = "GrpnJF3EliKd05UnVtcjeIkXdWHw8M9gjc1MnNyOsXi1dTOjHx"

MAX_TWEETS = 8000

initial_query = sys.argv[1]
#-----------------------------------------------------------------------
# authenticate API
#-----------------------------------------------------------------------
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = API(auth)

#-----------------------------------------------------------------------
# perform a basic search 
# parameters: query
# returns: list of tweets
# Twitter API docs:
# https://dev.twitter.com/docs/api/1/get/search
#-----------------------------------------------------------------------
def query_search(query):
	data = Cursor(api.search, q=query, result_type="popular", count=100).items(MAX_TWEETS)

	query_results = []
	for tweet in data:
		query_results.append(json.loads(json.dumps(tweet._json)))
	return query_results

#-----------------------------------------------------------------------
# Finds users of tweets
# parameters: list of tweets
# returns: [mentioned_users, hashtags, dictionary of potential influencers: users -->[followers_count, statuses_count]]
#-----------------------------------------------------------------------
def get_users_and_hashtags(tweets):
	mentioned_users = []
	hashtags = []
	users = {}
	for tweet in tweets:
		users[tweet['user']['screen_name']] = [tweet['user']['followers_count'], tweet['user']['statuses_count']]
		mentions = tweet['entities']['user_mentions']
		mentioned_users.extend([mention['screen_name'] for mention in mentions])
		hashtag_list = tweet['entities']['hashtags']
		hashtags.extend([hashtag['text'] for hashtag in hashtag_list])
	return [mentioned_users, hashtags, users]

#-----------------------------------------------------------------------
# Finds users of tweets
# parameters: list of users as screen_names
# returns: dictionary of potential influencers: users -->[followers_count, statuses_count]
#-----------------------------------------------------------------------	
def search_users(users):
	users_results = api.lookup_users(screen_names=users)
	potential_influencers = {}
	
	#convert from json
	users_data = []
	for user in users_results:
		users_data.append(json.loads(json.dumps(user._json)))
		
	for user in users_data:
		potential_influencers[user['screen_name']] = [user['followers_count'], user['statuses_count']]
	return potential_influencers

def find_potential_influencers(potential_influencers, queries):
	print queries
	if not queries or len(potential_influencers) > 50:
		return potential_influencers
	related_hashtags = []
	for query in queries:
		tweets = query_search(query)
		#users who tweeted popular tweets
		users_hashtag_list = get_users_and_hashtags(tweets)
		potential_influencers.update(users_hashtag_list[2])
		#users mentioned in the tweets
		mentioned_users = users_hashtag_list[0]
		potential_influencers.update(search_users(mentioned_users))
		#hashtags in the tweets
		related_hashtags += users_hashtag_list[1]
	counted_hashtags = Counter(related_hashtags)
	print counted_hashtags
	for hashtag in counted_hashtags:
		if not hashtag in queries and counted_hashtags[hashtag] > len(related_hashtags)/2:
			find_potential_influencers(potential_influencers, related_hashtags)
	
#Main method
potential_influencers = {}
find_potential_influencers(potential_influencers, [initial_query])
print "Number of Influencers: " + str(len(potential_influencers))
	