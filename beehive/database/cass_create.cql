CREATE KEYSPACE Beehive 
   with replication =  { 'class' : 'SimpleStrategy', 'replication_factor' : 2 };

Use Beehive;

CREATE TABLE HashtagUsers (
	hashtag text,
	username text,
	userRank double,
	tweetText text,
	tweetCreated timestamp,
	avgLikes float,
	avgRetweets float,
	followers int,
	numTweets int,
	numInteractions int,
	PRIMARY KEY (hashtag, username)
);

CREATE TABLE Users (
	username text,
	fullname text,
	lastUpdated timestamp,
	numAppeared int,
	avgLikes float,
	avgRetweets float,
	followers int,
	numTweets int,
	userRank double,
	PRIMARY KEY (username, lastUpdated)
) WITH CLUSTERING ORDER BY (lastUpdated DESC);