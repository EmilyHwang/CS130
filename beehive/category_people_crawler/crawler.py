#!/bin/python

import time, re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CategoryPeopleCrawler:
	def __init__(self, pages, source_url, dest_url):
		self.pages = pages
		self.source_url = source_url
		self.dest_url = dest_url

	def crawl(self):
		with open(self.source_url) as f:
			for line in f:
				x = line.split(',')
				url = x[1]
				driver = webdriver.Chrome(executable_path=r"/Users/IreneY/Library/chromedriver")
				driver.get("https://twitter.com/i/streams/stream/" + url)

				# scroll down the page iteratively with a delay
				for _ in xrange(0, self.pages):
				  driver.execute_script("window.scrollTo(0, 10000);")
				  time.sleep(2)

				# After scrolling, we want to find all of the people found on this page
				fullname = driver.find_elements_by_css_selector('.fullname.js-action-profile-name')
				username = driver.find_elements_by_css_selector('.username.js-action-profile-name')

				fout = file(self.dest_url + url + ".csv", "w")
				for full, user in zip (fullname, username):
					tmp_str = full.text + "," + user.text + '\n'
					fout.write(tmp_str.encode('utf-8'))

				fout.close()
				driver.quit()

if __name__ == "__main__":
	y = CategoryPeopleCrawler(3, '../data/twitter_categories.csv', '../data/category_people/')
	y.crawl()