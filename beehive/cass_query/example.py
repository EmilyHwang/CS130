#!/bin/env/python

from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

cluster = Cluster(['127.0.0.3'])
session = cluster.connect('system')

rows = session.execute('SELECT * from schema_keyspaces')

for user_row in rows:
	print user_row.keyspace_name
