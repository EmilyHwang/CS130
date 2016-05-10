from flask import Flask, render_template, request, redirect
import twitter
import rand_influencers
import pdb
import categories


# Configurations
DEBUG = True
DATABASE = ''
SECRET_KEY = ''
USER_NAME = ''
PASSWORD = ''


# Create Flask application
app = Flask(__name__)
app.config.from_object(__name__)


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
