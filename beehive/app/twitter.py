
#!/usr/bin/python
from tweepy import *
import json
import sys
import time
import os
import pdb

from collections import Counter, OrderedDict

# -----------------------------------------------------------------------
# API credentials and other global variables
# Limits on API 45000 tweets to grab, 3200 tweets per user --> 16 users to list, 1000 tweets --> 60 users
# -----------------------------------------------------------------------
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']

MAX_TWEETS = 100
MIN_NUM_OF_FOLLOWERS = 500
MIN_INFLUENCER_LIST = 20
MAX_USER_TIMELINE_TWEETS = 200

#initial_query = sys.argv[1]
# -----------------------------------------------------------------------
# authenticate API
# -----------------------------------------------------------------------

auth = AppAuthHandler(consumer_key, consumer_secret)
api = API(auth)
# auth = OAuthHandler(consumer_key, consumer_secret)
# auth.set_access_token(access_token, access_token_secret)

# api = API(auth)


# -----------------------------------------------------------------------
# perform a basic search
# parameters: query
# returns: list of tweets
# Twitter API docs:
# https://dev.twitter.com/docs/api/1/get/search
# -----------------------------------------------------------------------
def query_search(query):
    data = Cursor(api.search, q=query, result_type="mixed", count=100).items(MAX_TWEETS)

    query_results = []
    for tweet in data:
        query_results.append(json.loads(json.dumps(tweet._json)))
    print "original query size: " + str(len(query_results))
    return query_results


# -----------------------------------------------------------------------
# Finds users of tweets
# parameters: list of tweets
# returns: [users, hashtags]
# -----------------------------------------------------------------------
def get_users_and_hashtags(tweets):
    mentioned_users = []
    hashtags = []
    users = []
    for tweet in tweets:
        if tweet['user']['followers_count'] > MIN_NUM_OF_FOLLOWERS:
            users.append(tweet['user']['screen_name'])

        mentions = tweet['entities']['user_mentions']

        mentioned_users.extend([mention['screen_name'] for mention in mentions])

        if mentioned_users:
            users.extend(prune_users(mentioned_users))

        hashtag_list = tweet['entities']['hashtags']
        hashtags.extend([hashtag['text'] for hashtag in hashtag_list])

    return [set(users), hashtags]


# -----------------------------------------------------------------------
# Helper function to chunkify list into lists of size
# -----------------------------------------------------------------------
def chunk_list(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))


# -----------------------------------------------------------------------
# prunes given list of users to only users > min num of followers
# parameters: list of users as screen_names
# returns: list of screen names
# -----------------------------------------------------------------------
def prune_users(users):
    potential_influencers = []
    if len(users) > 100:
        for group in chunk_list(users, 100):
            potential_influencers.extend(search_users_100(group))
    else:
        potential_influencers = search_users_100(users)
    return potential_influencers


# -----------------------------------------------------------------------
# helper function: out of list of users, returns list with users > MIN num of followers
# parameters: list of users as screen_names (maximum 100 users)
# returns: list of user screen-names
# -----------------------------------------------------------------------
def search_users_100(users):
    users_results = api.lookup_users(screen_names=users)
    potential_influencers = []

    #convert from json
    users_data = []
    for user in users_results:
        users_data.append(json.loads(json.dumps(user._json)))

    for user in users_data:
        if user['followers_count'] > MIN_NUM_OF_FOLLOWERS:
            potential_influencers.append(user['screen_name'])
    return potential_influencers


# -----------------------------------------------------------------------
# searches user timeline, retrieves 200 tweets each time, API max = 3200, current max set to 1000
# parameters: user as screen_nam
# returns: json
# -----------------------------------------------------------------------
def query_user_timeline(user):
    data = Cursor(api.user_timeline, screen_name=user, count=200, include_rts=1).items(MAX_USER_TIMELINE_TWEETS)
    query_results = []
    for tweet in data:
        query_results.append(json.loads(json.dumps(tweet._json)))
    return query_results


# -----------------------------------------------------------------------
# gives average number of replies for pas MAX_TWEETS/100
# parameters: user as screen_name and all tweets he wrote
# returns: int - avg num of replies
# -----------------------------------------------------------------------
def extract_avg_num_of_replies(user_screenname, all_tweet_ids):
    data = Cursor(api.search, q="@"+user_screenname, result_type="popular", count=100).items(MAX_TWEETS)

    query_results = []
    for tweet in data:
        query_results.append(json.loads(json.dumps(tweet._json)))

    for tweet in query_results:
        if tweet['in_reply_to_status_id_str'] in all_tweet_ids:
            all_tweet_ids[tweet['in_reply_to_status_id_str']] += 1

    return sum(all_tweet_ids.values())/len(all_tweet_ids)


# -----------------------------------------------------------------------
# searches user timeline - last 3200 statuses
# parameters: user as screen_names
# returns: [followers_count, statuses_count, avg favorite_count, avg retweet_count]
# -----------------------------------------------------------------------
def extract_user_timeline_info(user):
    query_results = query_user_timeline(user)
    # extract user info once from first tweet, should be same for ALL tweets
    if len(query_results) > 1:
        user_info = query_results[0]['user']
    followers_count = user_info['followers_count']
    statuses_count = user_info['statuses_count']
    #all_tweet_ids = {}

    favorite_count_sum = 0
    retweet_count_sum = 0
    if followers_count > MIN_NUM_OF_FOLLOWERS: #check should be redundant
        for tweet in query_results:
            retweet_count_sum += tweet['retweet_count']
            favorite_count_sum += tweet['favorite_count']
            #all_tweet_ids[tweet['id_str']] = 0
    else:
        print "discarded: " + user
        return None

    avg_favorite_count = favorite_count_sum/len(query_results)
    avg_retweet_count = retweet_count_sum/len(query_results)
    #avg_num_of_replies = extract_avg_num_of_replies(user, all_tweet_ids)
    return [followers_count, statuses_count, avg_favorite_count, avg_retweet_count]


# -----------------------------------------------------------------------
# sets MAX_USER_TIMELINE_TWEETS
# 300 = API limit num of requests for user_timeline
# 200 how many tweets can be retrieved at once
# -----------------------------------------------------------------------
# def set_max_number_of_tweets(num_of_users):
    # num_of_tweets_to_check = (300/num_of_users) * 200
    # if num_of_tweets_to_check > 1000:
        # MAX_USER_TIMELINE_TWEETS = num_of_tweets_to_check

def find_potential_influencers(potential_influencers, queries):
    if not queries or len(potential_influencers) > MIN_INFLUENCER_LIST:
        return potential_influencers

    related_hashtags = []
    for query in queries:
        tweets = query_search(query)
        #users who tweeted popular tweets
        users_hashtag_list = get_users_and_hashtags(tweets)

        users_list = users_hashtag_list[0]

        print "size of pruned users list: " + str(len(users_list))

        print "[followers_count, statuses_count, avg favorite_count, avg retweet_count]"

        for user in users_list:
            user_info = extract_user_timeline_info(user)
            print user + ": " + str(user_info)
            if user_info is not None:
                potential_influencers[user] = user_info
            else:
                print "discarded: " + user
        #hashtags in the tweets
        related_hashtags += users_hashtag_list[1]
    counted_hashtags = Counter(related_hashtags)
    #print counted_hashtags
    # for hashtag in counted_hashtags:
        # print "hash tags searched: " + hashtag
        # if not hashtag in queries and counted_hashtags[hashtag] > len(related_hashtags)/2:
            #find_potential_influencers(potential_influencers, related_hashtags)


#Main method
def search_twitter(query):
    potential_influencers = {}
    find_potential_influencers(potential_influencers, [query])
    print "Number of Influencers: " + str(len(potential_influencers))

    # Generate a crude influencer rating by giving weights to each of the stats
    for influencer, stats in potential_influencers.iteritems():
        ranking = (stats[0]*0.3) + (stats[1]*0.1) + (stats[2]*0.2) + (stats[3]*0.4)
        stats.append(ranking)

    # Sort influencers in descending order by influencer rating
    sorted_potential_influencers = OrderedDict(sorted(potential_influencers.items(),
                                                      key=lambda(k, v): v[4], reverse=True))

    return sorted_potential_influencers


# -----------------------------------------------------------------------
# searches users - get most recent status
# parameters: list of users as screen_names
# returns: [full name, status]
# -----------------------------------------------------------------------
def get_users_info(usernames):
    users_results = api.lookup_users(screen_names=usernames)

    users_data = []
    for user in users_results:
        users_data.append(json.loads(json.dumps(user._json)))
    return users_data
    # users_to_display = {}

    ## convert from json
    # users_data = []
    # for user in users_results:
        # users_data.append(json.loads(json.dumps(user._json)))

    # for user in users_data:
        # users_to_display[user['screen_name']] = [user['name'], user['status']]
    # return users_to_display