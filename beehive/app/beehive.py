from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_oauth import OAuth
from tweepy import OAuthHandler, API
import math
import json
import re
import time
import sys

import pdb
import twitter.rand_influencers as rand_influencers
import twitter.categories as categories
import twitter.filter_influencers as filter_influencers
import twitter.twitter_auth as twitter_auth

from twitter.twitter_search import Search
from twitter.twitter_interact import Interact

# Logging
import logging, logging.config, yaml

# Configurations
DEBUG = False
DATABASE = ''
SECRET_KEY = 'SUPER SECRET CIA_FBI_NSA DEVELOPMENT KEY'
USER_NAME = ''
PASSWORD = ''

# Create Flask application
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = SECRET_KEY


# For user-level authentication
oauth = OAuth()
twitter_oauth = oauth.remote_app('twitter',
								 base_url='https://api.twitter.com/1/',
								 request_token_url='https://api.twitter.com/oauth/request_token',
								 access_token_url='https://api.twitter.com/oauth/access_token',
								 authorize_url='https://api.twitter.com/oauth/authenticate',
								 consumer_key=twitter_auth.CONSUMER_KEY,
								 consumer_secret=twitter_auth.CONSUMER_SECRET
								 )


@twitter_oauth.tokengetter
def get_twitter_token(token=None):
	return session.get('twitter_token')


# Global variables for filtering and pagination
query = ''					# query term
origData = []				# a copy of the original data where each entry is a 'page' of results, in case user wants to change filter params
leftoverData = {}			# users who we have not collected all info on yet
search = None				# search object so we can fetch next page of results
currPage = 0				# current page of results to display (starts at page 0)
pmax = 0					# max page

# const globals
RESULTS_PER_PAGE = 10		# num results to display per page; must correspond w/ num results returned from back end
FILTERS_ENABLED = ""		# show filters when all results are available
FILTERS_DISABLED = "hidden" # hide filters when paginating
BTN_ENABLED = ""			# used for pagination
BTN_DISABLED = "disabled='disabled'" # used for pagination

# Helper Functions

# not suitable for use with random_influencers
def getProfileLinks(potential_influencers):

	links = []
	print potential_influencers
	for name in potential_influencers:
		links.append('https://twitter.com/' + name)
	return links


# Insert clickable links into Twitter tweet text
# tweet = user['status']['text']
# entities = user['status']['entities']
def insertTextLinks(tweet, entities):
	# make mentions clickable
	if 'user_mentions' in entities:
		if len(entities['user_mentions']) != 0:
			for user in entities['user_mentions']:
				profile_link = "<a href=" + "'https://twitter.com/" + user['screen_name'] + "'>@" + user['screen_name'] + "</a>"
				screen_name = '@' + user['screen_name']
				tweet = re.sub(screen_name, profile_link, tweet, flags=re.IGNORECASE)

	# make hashtags clickable
	if 'hashtags' in entities:
		if len(entities['hashtags']) != 0:
			for hashtag in entities['hashtags']:
				tag_link = "<a href=" + "'https://twitter.com/hashtag/" + hashtag['text'] + "'>#" + hashtag['text'] + "</a>"
				tag = '#' + hashtag['text']
				tweet = re.sub(tag, tag_link, tweet, flags=re.IGNORECASE)

	# make URLs clickable
	if 'urls' in entities:
		if len(entities['urls']) != 0:
			for url in entities['urls']:
				url_link = "<a href=" + url['expanded_url'] + "'>" + url['display_url'] + "</a>"
				tco_url = url['url']
				tweet = re.sub(tco_url, url_link, tweet, flags=re.IGNORECASE)

	# embed images
	if 'media' in entities:
		if len(entities['media']) != 0:
			for m in entities['media']:
				url_link = "<img class='img-responsive' src='" + m['media_url'] + ":small'>"
				tco_url = m['url']
				tweet = re.sub(tco_url, url_link, tweet, flags=re.IGNORECASE)

	# make cashtags (stock symbols) clickable
	if 'symbols' in entities:
		if len(entities['symbols']) != 0:
			for cashtag in entities['symbols']:
				tag_link = "<a href=" + "'https://twitter.com/search?q=%24" + cashtag['text'] + "&src=ctag'>$" + cashtag['text'] + "</a>"
				tag = '\$' + cashtag['text']
				tweet = re.sub(tag, tag_link, tweet, flags=re.IGNORECASE)

	return tweet

# basically only checking for SQL injection right now
# does not check for well-formulated hashtag (e.g. does not start w/ number ...)
def notValidHashtag(query):
	# no spaces or punctuation
	regex = r"^[^\s\t\-;!%=(){}&|@<>\$\^\*\+\.\?\\]+$"
	# hashtag is valid
	if re.search(regex, query):
		return False
	# hashtag not valid
	return True


# View Routing

@app.route('/')
@app.route('/index')
def index():
	# 'data' is a variable that passes info to template for rendering
	# So for example, place stuff we retrieve from the database, api call, etc. into data
	#data = {}
	logfile.info('==== Landing Page ====')
	logfile.info('Get all categories')
	cats = categories.getAllCategories()

	logfile.info('Get random influencers from subcategory')
	# get 6 random users
	users = rand_influencers.get_users(6)

	links = []
	for user in users:
		links.append('https://twitter.com/' + user['screen_name'])

	# make links in tweet clickable
	for user in users:
		user['status']['text'] = insertTextLinks(user['status']['text'], user['status']['entities'])

	return render_template('index.html', users=users, links=links, categories=cats)


@app.route('/search', methods=['POST'])
def search():
	# Before completing the search, first make sure that the user is logged in.
	twitter_token = session.get('twitter_token')
	if twitter_token is None:
		logfile.info("User is not logged in. Redirect")
		logconsole.info("User is not logged in. Redirect")
		session.clear()
		session['query'] = request.form['user-input']
		return redirect(url_for('login'))

	if request.method == 'POST':
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)

		global query
		global search
		query = request.form['user-input']
		# check if hashtag is valid before querying
		if notValidHashtag(query):
			logfile.info("User searched invalid hashtag: #%s" % query)
			error_msg = "WHOOPS! That doesn't look like a valid hashtag ... Please check your input so we can give you some awesome results!"
			return render_template('search_results.html', query=query, links=[], potential_influencers={}, left_btn_view=BTN_DISABLED, right_btn_view=BTN_DISABLED, filters_view=FILTERS_DISABLED, error_msg = error_msg)
		logfile.info("Search initiated for hashtag: #%s" % query)

		search = Search(query, auth)

		# Get a list of users back
		start = time.time()
		logfile.info("time started: " + str(start))
		influencers = search.search_users()

		end = time.time()
		logfile.info("time started: " + str(start))
		logfile.info("Searching for: " + query)
		logfile.info("time ended: " + str(end))
		logfile.info("time elapsed: " + str(end-start))

		potential_influencers = influencers['first_pull']
		leftover_influencers = influencers['leftover']

		# store variables for pagination
		global currPage
		currPage = 0
		global origData
		origData = []
		origData.append(potential_influencers)

		global leftoverData
		leftoverData = {}
		leftoverData = leftover_influencers
		logfile.info("Number of results left: %d" % len(leftoverData))

		global pmax
		pmax = 0
		num_results = len(potential_influencers) + len(leftover_influencers)
		logfile.info("Total number of results: %d" % num_results)
		# cast to float to prevent rounding before ceil() is called
		pmax = math.ceil(num_results/float(RESULTS_PER_PAGE)) - 1

		links = getProfileLinks(potential_influencers)

		# disable buttons and filters appropriately
		left_btn_view = BTN_DISABLED
		right_btn_view = BTN_ENABLED
		filters_view = FILTERS_DISABLED

		if len(leftoverData) == 0:
			pmax = 0
			left_btn_view = BTN_DISABLED
			right_btn_view = BTN_DISABLED
			# enable filters if all results are returned (i.e. no pagination needed)
			filters_view = FILTERS_ENABLED

		return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)
	else:
		return redirect('/search-page')

# only paginate if not all results available upon query
@app.route('/search/results', methods=['POST'])
def paginate():
	request_page = request.form['page']
	global currPage
	global origData
	global leftoverData
	global pmax

	# prohibit filter options b/c not all results available
	filters_view = FILTERS_DISABLED

	if request_page == "previous":
		if currPage != 0:
			currPage = currPage - 1
			potential_influencers = origData[currPage]

			links = getProfileLinks(potential_influencers)

			# disable buttons appropriately
			left_btn_view = BTN_ENABLED
			right_btn_view = BTN_ENABLED
			if currPage == 0:
				left_btn_view = BTN_DISABLED

			return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)
	if request_page == "next":
		if currPage != pmax:
			currPage = currPage + 1

			# disable buttons appropriately
			left_btn_view = BTN_ENABLED
			right_btn_view = BTN_ENABLED
			if currPage == pmax:
				right_btn_view = BTN_DISABLED

			# check if results already cached before querying
			# this could be the case if user clicked next, previous, next
			if currPage < len(origData) :
				potential_influencers = origData[currPage]

				links = getProfileLinks(potential_influencers)

				return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)
			# results not cached, go ahead and query
			else:
				influencers = search.search_users_detail(leftoverData)
				potential_influencers = influencers['first_pull']
				leftover_influencers = influencers['leftover']

				# add new page of influencers to origData
				origData.append(potential_influencers)
				leftoverData = leftover_influencers
				logfile.info("New number of results left: %d" % len(leftoverData))

				links = getProfileLinks(potential_influencers)

				return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)

	# redirect to home and display error b/c we should never get here
	error_msg = "WHOOPS! Well that wasn't supposed to happen. Please try again."
	return redirect('/index', error_msg=error_msg)


@app.route('/search-page')
def search_page():
	return render_template('search_page.html')


# Note - this route should not be accessed if pagination is in effect
@app.route('/filtered_results', methods=['POST'])
def applyFilters():
	logfile.info("original data")
	logfile.info(origData)

	left_btn_view = BTN_DISABLED
	right_btn_view = BTN_DISABLED
	filters_view = FILTERS_ENABLED

	minFollowers = request.form['minFollowers']
	maxFollowers = request.form['maxFollowers']
	minStatuses = request.form['minStatuses']
	maxStatuses = request.form['maxStatuses']

	# set defaults for filter computation if no input provided
	default_set = {'minFollowers': False, 'maxFollowers': False, 'minStatuses': False, 'maxStatuses': False}
	if len(minFollowers) == 0:
		minFollowers = 0
		default_set['minFollowers'] = True
	if len(maxFollowers) == 0:
		maxFollowers = sys.maxint
		default_set['maxFollowers'] = True
	if len(minStatuses) == 0:
		minStatuses = 0;
		default_set['minStatuses'] = True
	if len(maxStatuses) == 0:
		maxStatuses = sys.maxint
		default_set['maxStatuses'] = True

	# validate user input
	try:
		minFollowers = int(minFollowers)
		maxFollowers = int(maxFollowers)
		minStatuses = int(minStatuses)
		maxStatuses = int(maxStatuses)

	except ValueError:
		error_msg = "WHOOPS! That can't be right ... Please check your filter range."
		links = getProfileLinks(origData[0])
		# hide default values from user
		if default_set['minFollowers'] == True:
			minFollowers = ""
		if default_set['maxFollowers'] == True:
			maxFollowers = ""
		if default_set['minStatuses'] == True:
			minStatuses = ""
		if default_set['maxStatuses'] == True:
			maxStatuses = ""
		return render_template('search_results.html', query=query, links=links, potential_influencers=origData[0], left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view, minFollowers=minFollowers, maxFollowers=maxFollowers, minStatuses=minStatuses, maxStatuses=maxStatuses, error_msg=error_msg)

	if minFollowers < 0 or maxFollowers < 0 or maxFollowers < minFollowers or minStatuses < 0 or maxStatuses < 0 or maxStatuses < minStatuses:
		# hide default values from user
		if default_set['minFollowers'] == True:
			minFollowers = ""
		if default_set['maxFollowers'] == True:
			maxFollowers = ""
		if default_set['minStatuses'] == True:
			minStatuses = ""
		if default_set['maxStatuses'] == True:
			maxStatuses = ""
		error_msg = "WHOOPS! That can't be right ... Please check your filter ranges."
		links = getProfileLinks(origData[0])
		return render_template('search_results.html', query=query, links=links, potential_influencers=origData[0], left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view, minFollowers=minFollowers, maxFollowers=maxFollowers, minStatuses=minStatuses, maxStatuses=maxStatuses, error_msg=error_msg)

	all_results = origData[0]
	filtered_influencers = filter_influencers.applyFilters(all_results, minFollowers, maxFollowers, minStatuses, maxStatuses)

	links = getProfileLinks(filtered_influencers)

	# hide default values from user
	if default_set['minFollowers'] == True:
		minFollowers = ""
	if default_set['maxFollowers'] == True:
		maxFollowers = ""
	if default_set['minStatuses'] == True:
		minStatuses = ""
	if default_set['maxStatuses'] == True:
		maxStatuses = ""

	return render_template('search_results.html', query=query, links=links, potential_influencers=filtered_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view, minFollowers=minFollowers, maxFollowers=maxFollowers, minStatuses=minStatuses, maxStatuses=maxStatuses)


@app.route('/influencers/<path:category>', methods=['GET'])
def getInfluencersByCategory(category):
	cats = categories.getAllCategories()
	view_category = ": " + category

	# get 12 users to display
	users = rand_influencers.get_users_by_category(12, category)

	links = []
	for user in users:
		links.append('https://twitter.com/' + user['screen_name'])

	# make links in tweet clickable
	for user in users:
		user['status']['text'] = insertTextLinks(user['status']['text'], user['status']['entities'])

	return render_template('index.html', users=users, links=links, categories=cats, view_category=view_category)


@app.route('/login')
def login():
	return twitter_oauth.authorize(callback=url_for('oauth_authorized',
									next=request.args.get('next') or request.referrer or None))


@app.route('/logout')
def logout():
	session.clear()
	return redirect('/index')


@app.route('/oauth-authorized')
@twitter_oauth.authorized_handler
def oauth_authorized(response):
	next_url = request.args.get('next') or url_for('index')
	if response is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)

	# Since auth is defined in twitter.py. Later change twitter to twitter_search
	access_token = response['oauth_token']
	access_token_secret = response['oauth_token_secret']
	session['screen_name'] = response['screen_name']

	session['twitter_token'] = (
		response['oauth_token'],			# access token
		response['oauth_token_secret']		# access token secret
	)

	# For web apps, we need to re-build the auth handler...
	auth = twitter_auth.UserAuth(access_token, access_token_secret)

	global query
	query = session.get('query')
	if query is None:
		return redirect(url_for('index'))

	# check if hashtag is valid before querying
		if notValidHashtag(query):
			logfile.info("User searched invalid hashtag: #%s" % query)
			error_msg = "WHOOPS! That doesn't look like a valid hashtag ... Please check your input so we can give you some awesome results!"
			return render_template('search_results.html', query=query, links=[], potential_influencers={}, left_btn_view=BTN_DISABLED, right_btn_view=BTN_DISABLED, filters_view=FILTERS_DISABLED, error_msg = error_msg)
		logfile.info("Search initiated for hashtag: #%s" % query)

	search = Search(query, auth)

	# Get a list of users back
	influencers = search.search_users()
	potential_influencers = influencers['first_pull']
	leftover_influencers = influencers['leftover']

	# store variables for pagination
	global origData
	origData.append(potential_influencers)

	global leftoverData
	leftoverData = leftover_influencers

	global pmax
	num_results = len(potential_influencers) + len(leftover_influencers)
	pmax = math.ceil(num_results/RESULTS_PER_PAGE) - 1

	links = getProfileLinks(potential_influencers)

	# disable buttons appropriately
	left_btn_view = BTN_DISABLED
	right_btn_view = BTN_ENABLED
	filters_view = FILTERS_DISABLED
	if len(leftover_influencers) == 0:
		left_btn_view = BTN_DISABLED
		right_btn_view = BTN_DISABLED
		filters_view = FILTERS_ENABLED

	return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)


@app.route('/follow', methods=['POST'])
def follow():
	twitter_token = session.get('twitter_token')
	user_to_follow = request.form['user-to-follow']
	if twitter_token:
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		interaction = Interact(query, auth)
		if request.form['followStatus'] == 'False':
			interaction.follow_user(user_to_follow)
		else:
			interaction.unfollow_user(user_to_follow)

	potential_influencers = origData[currPage]
	potential_influencers[user_to_follow]['followStatus'] = not potential_influencers[user_to_follow]['followStatus']

	links = getProfileLinks(potential_influencers)

	# disable buttons appropriately
	left_btn_view = BTN_ENABLED
	right_btn_view = BTN_ENABLED
	filters_view = FILTERS_DISABLED
	# first page, don't allow click previous
	if currPage == 0:
		left_btn_view = BTN_DISABLED
	# last page, don't allow click next
	if currPage == pmax:
		right_btn_view = BTN_DISABLED
	# all results available, enable filters
	if pmax == 0:
		filters_view = FILTERS_ENABLED

	return json.dumps({'status': 'ok'})
	# return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)


# Error handling
@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
	return render_template('500.html'), 500


if __name__ == '__main__':
	# set up logging to file
	logging.config.dictConfig(yaml.load(open('logging.conf')))
	logfile = logging.getLogger('file')
	logconsole = logging.getLogger('console')

	# Turn off Werkzeug debugger
	werk = logging.getLogger('werkzeug')
	werk.disabled = True
	# log.setLevel(logging.ERROR)

	logconsole.info('Start Application')
	logfile.info('Start Application')
	app.run()
