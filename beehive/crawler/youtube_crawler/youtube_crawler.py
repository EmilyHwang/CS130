#!/bin/python

# This function will be used to crawl youtube.com with the search query and get:
# Top 1000 popular videos
# The uploaders' followers, uploader channel URL, uploader name, twitter url

import time, re
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

class YoutubeCrawler:
	def __init__(self, hashtag, timeFrame):
		self.query = hashtag
		# usng view count
		if timeFrame == 7: 
			self.timeframeURL = "CAMSAggD"
		elif timeFrame == 1:
			self.timeframeURL = "CAASAggC"
		else:
			self.timeframeURL = "CAA%253D" # by relevance
		self.driver = webdriver.Chrome(executable_path=r"/Users/IreneY/Library/chromedriver")

	def crawl(self):
		display = Display(visible=0, size=(800, 600))
		display.start()
		for i in range(0,10):
			self.driver.get("https://www.youtube.com/results?search_query=" + self.query + "&sp=" + self.timeframeURL + "&page=" + str(i+1))
			
			# Get all the 
			tmp = self.driver.find_elements_by_css_selector('.item-section a.yt-uix-sessionlink.g-hovercard.spf-link')
			links = []

			# prevent links from being stale after clicking on new links, store all links into a new list
			for j in tmp:
				links.append(j.get_attribute("href") + "/about")

			for j in links:
				self.driver.get(j)
				user = self.driver.find_element_by_css_selector(".spf-link.branded-page-header-title-link.yt-uix-sessionlink").text
				try:
					follower_count = self.driver.find_element_by_css_selector(".yt-subscription-button-subscriber-count-branded-horizontal.subscribed.yt-uix-tooltip").text.replace(',','')
				except:
					continue

				try:
					channel_id = self.driver.find_element_by_css_selector("button.yt-uix-button.yt-uix-button-size-default.yt-uix-button-default.yt-uix-button-empty.yt-uix-button-has-icon.yt-uix-subscription-preferences-button")
					channel_id = channel_id.get_attribute("data-channel-external-id")
				except:
					channel_id = ""
				try:
					twitter_url = self.driver.find_element_by_partial_link_text('Twitter').get_attribute("href")
				except:
					twitter_url = ""
				print str(follower_count) + ",'" + channel_id + "','" + user + "','" + twitter_url + "'"
			
	def getQuery(self):
		print self.query

	def quit(self):
		self.driver.quit()

if __name__ == "__main__":
	y = YoutubeCrawler(sys.argv[1], sys.argv[2])
	y.crawl()
	y.quit()