#!/bin/bash

#Script to wrap colhub-get.sh to use on ingest cluster

/srh_data/operations/test_program/test_scripts/colhub-get.sh https://colhub.copernicus.eu/dhus /datacentre/processing/sentinel/relay_hub_testing/ingest/ingest_download1_test/node1/ GRD  >> /datacentre/processing/sentinel/relay_hub_testing/ingest/ingest_download1_test/logs/node1/colhub-get_$(date +\%Y\%m\%d).log 2>&1

