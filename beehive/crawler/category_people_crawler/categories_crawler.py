#!/bin/python

import re, urllib

textfile = file("categories.txt","w")

# Sports
myurl = "https://twitter.com/i/streams/category/686639666771046402"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Sports," + i[0] + "," + i[1] + "\n")

# News
myurl = "https://twitter.com/i/streams/category/686639666779394057"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("News," + i[0] + "," + i[1] + "\n")

# Musics
myurl = "https://twitter.com/i/streams/category/686639666779426835"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Musics," + i[0] + "," + i[1] + "\n")

# Entertainment
myurl = "https://twitter.com/i/streams/category/686639666779394055"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Entertainment," + i[0] + "," + i[1] + "\n")

# Lifestyle
myurl = "https://twitter.com/i/streams/category/686639666779426842"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Lifestyle," + i[0] + "," + i[1] + "\n")

# Technology and Science
myurl = "https://twitter.com/i/streams/category/686639666779394060"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Technology and Science," + i[0] + "," + i[1] + "\n")

# Art & Culture
myurl = "https://twitter.com/i/streams/category/686639666779426845"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Art & Culture," + i[0] + "," + i[1] + "\n")

# Government & Politics
myurl = "https://twitter.com/i/streams/category/686639666779394072"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Government & Politics," + i[0] + "," + i[1] + "\n")

# Gaming
myurl = "https://twitter.com/i/streams/category/690675490684678145"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Gaming," + i[0] + "," + i[1] + "\n")

# Nonprofits
myurl = "https://twitter.com/i/streams/category/692079932940259328"
for i in re.findall('<div class="TweetWithPivotModule-header">\s+<a href="https://twitter.com/i/streams/stream/(.*)" class="js-nav">(.*)<span class="Icon Icon--caretRight"></span></a>', urllib.urlopen(myurl).read(), re.I):
	textfile.write("Nonprofits," + i[0] + "," + i[1] + "\n")

textfile.close()