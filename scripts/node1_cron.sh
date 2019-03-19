5-55/10  *  *  *  * root /srh_data/operations/test_program/test_scripts/colhub-get.sh https://colhub.copernicus.eu/dhus /datacentre/processing/sentinel/relay_hub_testing/ingest/colhub/node1 GRD  >> /datacentre/processing/sentinel/relay_hub_testing/logs/colhub/node1/colhub-get_$(date +\%Y\%m\%d).log 2>&1
10 0  *  *  * /bin/ln -sf /datacentre/processing/sentinel/relay_hub_testing/logs/colhub/node1/colhub-get_$(date +\%Y\%m\%d).log /datacentre/processing/sentinel/relay_hub_testing/logs/colhub/node1/colhub-get.log 2>&1 > /dev/null

#check the inventory
30 2  *  *  * /srh_data/operations/test_program/test_scripts/check-inventory.sh -d $(date -d"1 day ago" -I) -k -r -w /datacentre/processing/sentinel/relay_hub_testing/logs/colhub/node1/inventory_$(date -d"1 day ago" +\%Y) >> /datacentre/processing/sentinel/relay_hub_testing/logs/colhub/node1/check-inventory_$(date -d"1 day ago" -I).log 2>&1
