#!/bin/python
import os
from twitter_search import Search

access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']

hashtagArr = ["Marvel", "Starwars", "CaptainAmericaCivilWar", "mystupidboss", "assassinscreed", "acapella", "taylorswift", "justinbeiber", "Cannes2016", "NowStreaming", "InvictusGames", "SummerVibes", "beautyboys", "bootymonday", "legday", "mondaymotivation"]

for hashtag in hashtagArr:
	search = Search(hashtag)
	potential_influencers = search.search_twitter()
