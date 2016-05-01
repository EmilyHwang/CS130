CREATE DATABASE IF NOT EXISTS beehive;

USE beehive;

CREATE TABLE IF NOT EXISTS Categories (
	categoryName VARCHAR(50), 
	subCategoryId CHAR(18) NOT NULL, 
	subCategory VARCHAR(50), 
	PRIMARY KEY (subCategoryId)
);

CREATE TABLE IF NOT EXISTS SubCategoryPeople(
	subCategoryId CHAR(18),
	username VARCHAR(50),
	fullname VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Hashtags(
	hashtag VARCHAR(50),
	lastUpdated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
	timeSearched INT
);

# The default encoding for mysql is latin1. We want utf-8 encoding
SET foreign_key_checks = 0; 
ALTER TABLE Categories CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci; 
ALTER TABLE SubCategoryPeople CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci; 
SET foreign_key_checks = 1; 


