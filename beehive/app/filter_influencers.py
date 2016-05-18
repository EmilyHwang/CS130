#!/usr/bin/python
from collections import OrderedDict

# Description: returns data from influencerList that matches criteria in filterList
# Input:
#   - influencerList: influencer data returned by the influencer search function
#               expected in the form:
# Output: filtered data that matches criteria
def applyFilters(influencerList, minFollowers, maxFollowers):
	filteredData = {}
	minF = int(minFollowers)
	maxF = int(maxFollowers)
	# do filtering
	for influencer, influencer_info in influencerList.iteritems():
		numFollowers = int(influencer_info['followers'])
		print numFollowers
		if minF <= numFollowers <= maxF:
			filteredData[influencer] = influencer_info
	#return OrderedDict(sorted(filteredData.items(), key=lambda(k,v): v[4], reverse=True))
	return filteredData