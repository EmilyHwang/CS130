# Beehive - Social media analytics for everyone
##### UCLA CS 130, Spring 2016

## Setup
1.) First, make sure you have `virtualenv` installed:
```
$ pip install virtualenv
```

2.) Then change into the `/CS130/beehive` folder to create a virtual environment for Beehive:
```
$ cd CS130/beehive
$ virtualenv venv
```

You should now have a `venv` folder inside the `beehive` folder. Make sure that your virtual environment uses Python 2.7 (you will see the Python version when this line is output `New python executable in...`). If not, remove the `venv` folder and use Python 2.7:

```
$ virtualenv -p /usr/bin/python2.7 venv
```

3.) To begin using the virtual environment, activate it:
```
source venv/bin/activate
```

4.) Install packages and dependencies needed for Beehive:
```
pip install -r requirements.txt
```

5.) Set up environment variable permanently
You will need the access token and the secret keys to run the script now. Add the following line to your ~/.bash_profile file
```
export ACCESS_TOKEN="[ACCESS_TOKEN]"
export ACCESS_TOKEN_SECRET="[ACCESS_TOKEN_SECRET]"
export CONSUMER_KEY="CONSUMER_KEY"
export CONSUMER_SECRET="CONSUMER_SECRET"
```
Restart the terminal and do 
```
echo $ACCESS_TOKEN
```
This should output your key

6.) Now Beehive is ready to be run.
```
cd app
python beehive.py
```

7.) When you are done working in the virtual environment, deactivate it:
```
deactivate
```

8.) If you install any new packages, please make sure to do a:
```
pip freeze > requirements.txt
```

## Import data to MySQL
There are several data files inside beehive/data directory. In order to get it on your machine, make sure that you have mysql install. 

1. If you don't have a mysql config file, please create one
```
vi ~/.my.cnf 
```
Insert the following line with your mysql user and password
```
[client]
user=root
password=[your password]
```

2. After this, go to the beehive directory and run
```
./database_setup.sh
```
This will create a database (beehive), two tables, and populate the tables with data from the data/ directory

## Running Beehive
You only need to do the setup once. Subsequently, to run Beehive, the workflow is as follows:

1. While in the `CS130/beehive` directory, activate the virtual environment: `source venv/bin/activate`
Windows: 'source venv/Scripts/activate'

2. Make edits/work on code/run Beehive: `python beehive.py`

3. Deactivatr virtual environment: `deactivate`

## Running Youtube Crawler (No need for now. Need chrome executable and change path to work)

1.) Running the command with hashtag
```
cd youtube_crawler
./youtube_helper [search_keyword] [7|1|0] 
```
The search keyword is the hashtag with/without '#'
The second parameter is the time frame. 
If you want to do the last week, then 7 (by view count)
If you want to search from today, then 1 (by view count)
If you want to just search by relevance, then 0
 
2.) View Result
The result is in youtube_output.csv file, sorted by followers count

### Setting up Cassandra (Mac)

1.) In the beehive directory, activate the virtualenv
```
source venv/bin/activate
```

2.) Run the install script (Java 1.7 or 1.8 must be installed)
```
bash ccm_install.sh
```

3.) Check if there are three nodes running
```
ccm status
```
You should see the following outputs
```
Cluster: 'test'
---------------
node1: UP
node3: UP
node2: UP
```

4.) Now we can create keyspace and tables inside the Cassandra clusters
Run the following command to set up your database
```
bash cass_database_setup.sh
```

5.) Commands to try in Cassandra 
To connect to the local Cassandra cluster
```
ccm node1 cqlsh
```

To show all keyspaces (this is like database in MySQL)
```
desc KEYSPACES
```

To use a certain KEYSPACE
``` 
Use [Keyspace]
```

To show all tables
```
desc tables
```

To describe a table
``` 
desc table [Table name]
```
