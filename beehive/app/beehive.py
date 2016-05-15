from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_oauth import OAuth
from tweepy import OAuthHandler, API
import twitter
import rand_influencers
import pdb
import categories


# Configurations
DEBUG = True
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
                                 consumer_key=twitter.consumer_key,
                                 consumer_secret=twitter.consumer_secret
                                 )


@twitter_oauth.tokengetter
def get_twitter_token(token=None):
    return session.get('twitter_token')


@app.route('/')
@app.route('/index')
def index():
    # 'data' is a variable that passes info to template for rendering
    # So for example, place stuff we retrieve from the database, api call, etc. into data
    #data = {}

    #test code
    cats = categories.getAllCategories();
    #end test code

    users = rand_influencers.get_users(3)
    return render_template('index.html', users=users, categories=cats)


@app.route('/search', methods=['POST'])
def search():
    # Before completing the search, first make sure that the user is logged in.
    access_token = session.get('twitter_token')
    if access_token is None:
        session.clear()
        session['query'] = request.form['user-input']
        return redirect(url_for('login'))

    if request.method == 'POST':
        query = request.form['user-input']
        potential_influencers = twitter.search_twitter(query)

        links = []
        for name in potential_influencers:
            links.append('https://twitter.com/' + name)

        return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers)

    else:
        return redirect('/search-page')


@app.route('/search-page')
def search_page():
    return render_template('search_page.html')


@app.route('/login')
def login():
    return twitter_oauth.authorize(callback=url_for('oauth_authorized',
                                                    next=request.args.get('next') or request.referrer or None))


@app.route('/oauth-authorized')
@twitter_oauth.authorized_handler
def oauth_authorized(response):
    next_url = request.args.get('next') or url_for('index')
    if response is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    # Since auth is defined in twitter.py. Later change twitter to twitter_search
    twitter.access_token = response['oauth_token']
    twitter.access_token_secret = response['oauth_token_secret']
    session['screen_name'] = response['screen_name']

    session['twitter_token'] = (
        response['oauth_token'],            # access token
        response['oauth_token_secret']      # access token secret
    )

    # For web apps, we need to re-build the auth handler...
    twitter.auth = OAuthHandler(twitter.consumer_key, twitter.consumer_secret)
    twitter.auth.set_access_token(twitter.access_token, twitter.access_token_secret)
    twitter.api = API(twitter.auth)

    query = session.get('query')
    if query is None:
        return redirect(url_for('index'))

    potential_influencers = twitter.search_twitter(query)
    links = []
    for name in potential_influencers:
        links.append('https://twitter.com/' + name)

    return render_template('search_results.html', query=query, links=links, potential_influencers=potential_influencers)


@app.route('/about')
def about():
    data = {}
    return render_template('about.html', data=data)


@app.route('/contact')
def contact():
    data = {}
    return render_template('contact.html', data=data)


if __name__ == '__main__':
    app.run()
