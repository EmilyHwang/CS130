#!/usr/bin/python
from collections import OrderedDict
import logging

logfile = logging.getLogger('file')

# Description: returns data from influencerList that matches criteria in filterList
# Input:
#   - influencerList: influencer data returned by the influencer search function
#               expected in the form:
# Output: filtered data that matches criteria
def applyFilters(influencerList, minFollowers, maxFollowers, minStatuses, maxStatuses):
	logfile.info("===== Applying filters! =====")

	filteredData = {}
	minF = int(minFollowers)
	maxF = int(maxFollowers)
	minS = int(minStatuses)
	maxS = int(maxStatuses)

	# do filtering
	for influencer, influencer_info in influencerList.iteritems():
		numFollowers = int(influencer_info['followers'])
		numStatuses = int(influencer_info['numTweets'])
		if minF <= numFollowers <= maxF and minS <= numStatuses <= maxS:
			filteredData[influencer] = influencer_info

	return filteredData