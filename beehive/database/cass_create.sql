Use Beehive;

CREATE KEYSPACE Beehive 
   with replication =  { 'class' : 'SimpleStrategy', 'replication_factor' : 2 };

CREATE TABLE Users (
	username text,
	fullname text,
	numAppeared int,
	followers int,
	numTweets int,
	numStatus int,
	aveLikes int,
	aveRetweets int,
	updatedTime timestamp,
	PRIMARY KEY (username)
);