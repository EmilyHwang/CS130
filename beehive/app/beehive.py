from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_oauth import OAuth
from tweepy import OAuthHandler, API
import rand_influencers
import pdb
import categories
import filter_influencers
import twitter_search
import twitter_auth
import twitter_interact

from flask_socketio import SocketIO, emit, disconnect
from threading import Thread
import eventlet

# Configurations
DEBUG = True
DATABASE = ''
SECRET_KEY = 'SUPER SECRET CIA_FBI_NSA DEVELOPMENT KEY'
USER_NAME = ''
PASSWORD = ''

# monkey patching is necessary because this application uses a background
# thread
async_mode = 'eventlet'
eventlet.monkey_patch()

# Create Flask application
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app, async_mode=async_mode)
thread = None


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

origData = {}
query = ''


@app.route('/')
@app.route('/index')
def index():
	# 'data' is a variable that passes info to template for rendering
	# So for example, place stuff we retrieve from the database, api call, etc. into data
	#data = {}

	cats = categories.getAllCategories();

	users = rand_influencers.get_users(3)

	links = []
	for user in users:
		links.append('https://twitter.com/' + user['screen_name'])

	return render_template('index.html', users=users, links=links, categories=cats)


@app.route('/search', methods=['POST'])
def search():
	# Before completing the search, first make sure that the user is logged in.
	twitter_token = session.get('twitter_token')
	if twitter_token is None:
		session.clear()
		session['query'] = request.form['user-input']
		return redirect(url_for('login'))

	if request.method == 'POST':
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		
		global query
		query = request.form['user-input']
		search = twitter_search.Search(query, auth)

		# Get a list of users back
		potential_influencers = search.search_users()

		global origData
		origData = potential_influencers['first_10']

		links = []
		for name in potential_influencers['first_10']:
			links.append('https://twitter.com/' + name)

		return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers['first_10'])

	else:
		return redirect('/search-page')

@app.route('/search-page')
def search_page():
	return render_template('search_page.html')

@app.route('/filtered_results', methods=['POST'])
def applyFilters():
	print request.form
	print origData
	minFollowers = request.form['minFollowers']
	maxFollowers = request.form['maxFollowers']

	filtered_influencers = filter_influencers.applyFilters(origData, minFollowers, maxFollowers)
	print filtered_influencers
	links = []
	for name in filtered_influencers:
		links.append('https://twitter.com/' + name)

	return render_template('search_results.html', query=query, links=links, potential_influencers=filtered_influencers)


@app.route('/influencers/<path:category>', methods=['GET'])
def getInfluencersByCategory(category):
	cats = categories.getAllCategories()

	users = rand_influencers.get_users_by_category(12, category)

	links = []
	for user in users:
		links.append('https://twitter.com/' + user['screen_name'])

	return render_template('index.html', users=users, links=links, categories=cats)


'''
@app.route('/search', methods=['POST', 'GET'])
def search():
	if request.method == 'POST':
		searchword = request.form['searchterm']
		potential_influencers = twitter.search_twitter(searchword)
		return render_template('search_result.html', potential_influencers=potential_influencers)
	else:
		data = {}
		return render_template('search.html', data=data)
'''

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

	query = session.get('query')
	if query is None:
		return redirect(url_for('index'))

	search = twitter_search.Search(query, auth)

	# Get a list of users back
	potential_influencers = search.search_users()

	global origData
	origData = potential_influencers['first_10']

	links = []
	for name in potential_influencers['first_10']:
		links.append('https://twitter.com/' + name)

	return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers['first_10'])


@app.route('/about')
def about():
	data = {}
	return render_template('about.html', data=data)


@app.route('/contact')
def contact():
	data = {}
	return render_template('contact.html', data=data)
	
@app.route('/follow', methods=['POST'])
def follow():
	twitter_token = session.get('twitter_token')
	user_to_follow = request.form['user-to-follow']
	if twitter_token:
		access_token = twitter_token[0]
		access_token_secret = twitter_token[1]
		auth = twitter_auth.UserAuth(access_token, access_token_secret)
		interaction = twitter_interact.Interact(query, auth)
		interaction.follow_user(user_to_follow)
	potential_influencers = origData

	links = []
	for name in potential_influencers:
		links.append('https://twitter.com/' + name)
	return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers)


if __name__ == '__main__':
    socketio.run(app, debug=DEBUG)
