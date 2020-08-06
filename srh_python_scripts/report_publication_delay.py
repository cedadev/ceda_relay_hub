'''
Wrapper script to take a simple list iof UID's culled from a log file and recursivelt report on each of these

grep  'successfully downloaded from' /srh/data/logs/dhus.log | awk '{print $12}'
 | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}'
  | sort -u  > list.txt
'''

import os,sys
from get_product_details import get_product_details

hub_config = sys.argv[1]
list = sys.argv[2]


with open(list) as r:
    uids = [i.rstrip() for i in r.readlines()]

for uid in uids:
    get_product_details(hub_config, uid)