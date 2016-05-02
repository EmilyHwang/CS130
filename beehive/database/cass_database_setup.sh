#!/bin/bash

# Clean up everything
ccm node1 cqlsh < cass_drop.cql

# Create the database and table
ccm node1 cqlsh < cass_create.cql