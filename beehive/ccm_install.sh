#!/bin/bash

# Java 7 or 8 must be installed


# Install java build servers
sudo brew install ant

# Download ccm git repo
git clone https://github.com/pcmanus/ccm.git /tmp/ccm

cd /tmp/ccm && ./setup.py install

# Setup network interfaces
sudo ifconfig lo0 alias 127.0.0.2
sudo ifconfig lo0 alias 127.0.0.3

# Create ccm cassandra instance
ccm create test -v 2.0.9

# Create 3 nodes for our test cluster
ccm populate -n 3

# start cluster
ccm start

# check output
ccm status
