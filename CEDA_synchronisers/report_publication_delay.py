'''
Wrapper script to take a simple list iof UID's culled from a log file and recursivelt report on each of these

grep  'successfully downloaded from' /srh/data/logs/dhus.log | awk '{print $12}'
 | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}'
  | sort -u  > list.txt
'''

import os,sys
from get_product_details import get_product_details,report_line, average_delay_hours, analyse_delay
import click

#see https://click.palletsprojects.com/en/7.x/options/  !!
@click.command()
@click.option('-c', '--hub-config', 'hub_config', type=str, required=True, help='Location of hub admin credos')
@click.option('-l', '--list', 'list', required=True, type=str, help='List of UIDs to submit to hub to extract publication delay info on')
@click.option('--line', is_flag=True)
def main(hub_config, list, line):

    with open(list) as r:
        uids = [i.rstrip() for i in r.readlines()]

    delays = []

    for uid in uids:

        try:
            hub_domain, publication_delay = get_product_details(hub_config, uid)

            delays.append(publication_delay)

            if line:
                days, hrs, mins, secs = analyse_delay(publication_delay)
                report_line(uid, hub_domain, days, hrs, mins, secs)

        except Exception as ex:
            print (ex)

    if len(delays) != 0:
        avg_hrs, avg_mins = average_delay_hours(delays)

        print (f"Average publication delay: {avg_hrs} hrs {avg_mins} mins for {len(uids)} records from {hub_domain}")

    else:
        print (f"Could not calculate publication delay as no products found!")

if __name__ == '__main__':
    main()