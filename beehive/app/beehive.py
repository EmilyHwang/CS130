from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_oauth import OAuth
from tweepy import OAuthHandler, API
import math

import pdb
import twitter.rand_influencers as rand_influencers
import twitter.categories as categories
import twitter.filter_influencers as filter_influencers
import twitter.twitter_auth as twitter_auth

from twitter.twitter_search import Search
from twitter.twitter_interact import Interact
from instagram.instagram_search import InstagramSearch

# Logging
import logging, logging.config, yaml

import urllib, urlparse

# Configurations
DEBUG = False
DATABASE = ''
SECRET_KEY = 'SUPER SECRET CIA_FBI_NSA DEVELOPMENT KEY'
USER_NAME = ''
PASSWORD = ''

REDIRECT_URI = "http://127.0.0.1:5000/authorized"

# Create Flask application
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = SECRET_KEY

CLIENT_ID = "88c6f49c38f540fa8fa70521b35c50d3"
CLIENT_SECRET = "1f888dc7f45c4c5fb5823052807ed9fe"

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

instagram_oauth = oauth.remote_app('instagram',
								 base_url='https://api.instagram.com',
								 authorize_url='https://api.instagram.com/oauth/authorize',
								 request_token_url=None,
								 request_token_params = {'response_type': 'token', 'scope':'public_content'},
								 access_token_url='https://api.instagram.com/oauth/access_token',
								 access_token_method='POST',
								 access_token_params = {},
								 consumer_key=CLIENT_ID,
								 consumer_secret=CLIENT_SECRET
								 )


@twitter_oauth.tokengetter
def get_twitter_token(token=None):
	return session.get('twitter_token')

@instagram_oauth.tokengetter	
def get_instagram_token(token=None):
	return session.get('instagram_token')


# Global variables for filtering and pagination
query = ''					# query term
origData = []				# a copy of the original data, in case user wants to change filter params
leftoverData = {}			# users who we have not collected all info on yet
search = None				# search object so we can fetch next page of results
currPage = 0				# current page of results to display (starts at page 0)
pmax = 0					# max page

# const globals
RESULTS_PER_PAGE = 10		# num results to display per page; must correspond w/ num results returned from back end
FILTERS_ENABLED = ""		# show filters when all results are available
FILTERS_DISABLED = "hidden"	# hide filters when paginating
BTN_ENABLED = ""			# used for pagination
BTN_DISABLED = "disabled='disabled'" # used for pagination

# Helper functions used across multiple routes
def getProfileLinks(potential_influencers):
	links = []
	for name in potential_influencers:
		links.append('https://twitter.com/' + name)
	return links


# View Routing

@app.route('/')
@app.route('/index')
def index():
	# 'data' is a variable that passes info to template for rendering
	# So for example, place stuff we retrieve from the database, api call, etc. into data
	#data = {}
	logfile.info('==== Landing Page ====')
	logfile.info('Get all categories')
	cats = categories.getAllCategories();

	logfile.info('Get random influencers from subcategory')
	# get 3 random users
	users = rand_influencers.get_users(3)

	links = []
	for user in users:
		links.append('https://twitter.com/' + user['screen_name'])

	return render_template('index.html', users=users, links=links, categories=cats)


@app.route('/search', methods=['POST'])
def search():
	# Before completing the search, first make sure that the user is logged in.
	twitter_token = session.get('twitter_token')
	instagram_token = session.get('instagram_access_token')
	if twitter_token is None:
		logfile.info("User is not logged in. Redirect")
		logconsole.info("User is not logged in. Redirect")
		session.clear()
		session['query'] = request.form['user-input']
		return redirect(url_for('login_twitter'))
	
	if instagram_token is None:
		session.clear()
		session['query'] = request.form['user-input']
		return redirect(url_for('login_instagram'))
		
	logfile.info("instagram token: " + instagram_token)

	if request.method == 'POST':
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)

		global query
		global search
		query = request.form['user-input']
		logfile.info("Search initiated for hashtag: #%s" % query)

		search = Search(query, auth)
		
		search_instagram = InstagramSearch(instagram_token, query)
		search_instagram.search_instagram()

		# Get a list of users back
		influencers = search.search_users()
		potential_influencers = influencers['first_pull']
		leftover_influencers = influencers['leftover']

		# store variables for pagination
		global origData
		origData.append(potential_influencers)

		global leftoverData
		leftoverData = leftover_influencers
		print "length of leftoverData: "
		print len(leftoverData)

		global pmax
		num_results = len(potential_influencers) + len(leftover_influencers)
		pmax = math.ceil(num_results/RESULTS_PER_PAGE) - 1

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
	print request_page
	print pmax
	global currPage
	global origData
	global leftoverData

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
				print len(leftoverData)

				links = getProfileLinks(potential_influencers)

				return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)

	# TODO
	# redirect to error page
	return redirect('/index')

@app.route('/search-page')
def search_page():
	return render_template('search_page.html')


# Note - this route should not be accessed if pagination is in effect
@app.route('/filtered_results', methods=['POST'])
def applyFilters():
	logfile.info("original data")
	logfile.info(origData)

	minFollowers = request.form['minFollowers']
	maxFollowers = request.form['maxFollowers']


	filtered_influencers = filter_influencers.applyFilters(origData, minFollowers, maxFollowers)

	links = getProfileLinks(filtered_influencers)

	left_btn_view = BTN_DISABLED
	right_btn_view = BTN_DISABLED
	filters_view = FILTERS_ENABLED

	return render_template('search_results.html', query=query, links=links, potential_influencers=filtered_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)


@app.route('/influencers/<path:category>', methods=['GET'])
def getInfluencersByCategory(category):
	cats = categories.getAllCategories()

	# get 12 users to display
	users = rand_influencers.get_users_by_category(12, category)

	links = getProfileLinks(users)

	return render_template('index.html', users=users, links=links, categories=cats)


@app.route('/login_twitter')
def login_twitter():
	return twitter_oauth.authorize(callback=url_for('oauth_authorized',
									next=request.args.get('next') or request.referrer or None))
@app.route('/login_instagram')
def login_instagram():
	if session.has_key('instagram_access_token'):
		del session['instagram_access_token']
	return instagram_oauth.authorize(callback=REDIRECT_URI)

@app.route('/logout')
def logout():
	session.clear()
	return redirect('/index')
	
@app.route('/authorized')
@instagram_oauth.authorized_handler
def authorized(resp):
	try:
		pass
	except Exception:
		pass
	session.clear()
	print request
	print resp
	access_token = request.args.get('access_token')
	session['instagram_access_token'] = access_token
	logfile.info("authorized instagram with access_token: " + access_token)
	return redirect('/index')

@app.route('/oauth-authorized')
@twitter_oauth.authorized_handler
def oauth_authorized(response):
	next_url = request.args.get('next') or url_for('index')
	if response is None:
		flash(u'You denied the request to sign in.')
		return redirect(next_url)

	# Since auth is defined in twitter.py. Later change twitter to twitter_search
	print response
	access_token = response['oauth_token']
	access_token_secret = response['oauth_token_secret']
	session['twitter_screen_name'] = response['screen_name']

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


@app.route('/about')
def about():
	data = {}
	return render_template('about.html', data=data)


@app.route('/follow', methods=['POST'])
def follow():
	twitter_token = session.get('twitter_token')
	user_to_follow = request.form['user-to-follow']
	if twitter_token:
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		interaction = Interact(query, auth)
		interaction.follow_user(user_to_follow)
	potential_influencers = origData[currPage]

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

	return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers, left_btn_view=left_btn_view, right_btn_view=right_btn_view, filters_view=filters_view)


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
