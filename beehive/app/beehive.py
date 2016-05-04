from flask import Flask, render_template, request
import twitter
import rand_influencers

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
    data = {}
    return render_template('index.html', data=data)

@app.route('/search', methods=['POST'])
def search():
	if request.method == 'POST':
		searchword = request.form['searchterm']
		potential_influencers = twitter.search_twitter(searchword)
		return render_template('search_result.html', potential_influencers=potential_influencers)
	else: 
		data = {}
		return render_template('search.html', data=data)

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
