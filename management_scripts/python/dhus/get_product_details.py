import os, sys
#from synchroniser import *
from dhus_odata_api import *
from datetime import datetime,timedelta
from urllib.parse import urlparse
import math

'''
Run from shell after parsing dhus log file for successfully downloaded files for UID's using shell incantation command like this:

 grep  'successfully downloaded from' /srh/data/logs/dhus.log | awk '{print $12}' | head -100  | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u

'''

CR_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}CreationDate'
IN_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}IngestionDate'

class UIDnotOnHubError(Exception):
    '''
        see https://gist.github.com/StephenFordham/8ea287187a0fde02a8ee82d5a1f2039f
        '''

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'MyCustomError, {0} '.format(self.message)
        else:
            return 'MyCustomError has been raised'


def get_product_details(hub_config, uid):
    '''
    Method to access Products xml file for a given UID on the hub
    :return:
    '''

    stub = f"v1/Products('{uid}')"

    msg = None


    # whats the hub (for reporting purposes)
    hub, u, pwd = get_hub_creds(hub_config)

    del u;
    del pwd

    hub_domain = urlparse(hub).netloc

    # root = access_xml_file(GET_from_hub(hub_config, odata_stub=stub))
    content = GET_from_hub(hub_config, odata_stub=stub)

    if content.status_code in [200, 201]:
        root = get_existing_details(content.text)

        creation_date = datetime.strptime(root.find(CR_DATE_XP).text, '%Y-%m-%dT%H:%M:%S.%f')
        ingestion_date = datetime.strptime(root.find(IN_DATE_XP).text, '%Y-%m-%dT%H:%M:%S.%f')

        return hub_domain, creation_date, ingestion_date

    elif content.status_code in [404]:
        raise UIDnotOnHubError(f"{uid}: Product not found on hub")

    else:
        raise Exception(f"Cannot extract data on {uid}. Hub return code: {content.status_code}")


def get_delay(creation_date, ingestion_date):
    # whats the difference - timedelta object
    # publication_delay = ingestion_date - creation_date
    publication_delay = creation_date - ingestion_date
    
    return publication_delay


def analyse_delay(publication_delay):
    '''
    Method to pretty print report based on days and seconds
    :return:
    '''

    if publication_delay.days < 1:
        #days = 0
        hrs = int(publication_delay.seconds / 3600)
        mins = int((publication_delay.seconds % 3600) / 60)
        #secs = publication_delay.seconds - (mins * 60)
        secs = publication_delay.seconds - ((hrs * 3600) + (mins * 60))
            
    else:
        #days = int(publication_delay.days)
        hrs = 24 + int(publication_delay.seconds / 3600)
        mins = int((publication_delay.seconds % 3600) / 60)
        #secs = publication_delay.seconds - (mins * 60)
        secs = publication_delay.seconds - (((hrs-24) * 3600) + (mins * 60))

    return hrs, mins, secs


def average_delay_hours(dates):

    total_delay_secs = []
    #why not just use the delta.secs()?  and what about days...?
    for date in dates:
        hrs, mins, secs = analyse_delay(date)

        #use total seconds from original dates

        #total_delay_secs.append(((days * (3600 *24) + date.seconds)))
        total_delay_secs.append((hrs*3600) + (mins*60) +secs)
        
    delay = sum([i for i in total_delay_secs]) / len(total_delay_secs) / 3600

    delay_hrs = math.floor(delay)

    #convert fraction to proper mins
    delay_mins = round((60/100)*((delay - delay_hrs)*100))

    return delay_hrs, delay_mins


def daily_report(hrs, mins, secs):
    return (f"{str(hrs).zfill(2)}:{str(mins).zfill(2)}:{str(secs).zfill(2)} (HH:MM:SS)")


def report_line(uid, src_hub_domain, loc_hub_domain, hrs, mins, secs, linenum=None):

    delay_str = daily_report(hrs, mins, secs)

    if not linenum:
        print (
            f"Product {uid} on SOURCE hub {src_hub_domain}/ LOCAL hub {loc_hub_domain}: publication delay: {delay_str}")

    else:
        print(
            f"{linenum} Product {uid} on SOURCE hub {src_hub_domain}/ LOCAL hub {loc_hub_domain}: publication delay: {delay_str}")


if __name__ == '__main__':
    #http: // srh - services3.ceda.ac.uk / odata / v1 / Products('52199a54-790e-449d-ae20-548d83313ae5')

    hub_config = sys.argv[1]
    uid = sys.argv[2]

    try:
        hub_domain, creation_date, ingestion_date = get_product_details(hub_config, uid)

        publication_delay = get_delay(creation_date, ingestion_date)

        hrs, mins, secs = analyse_delay(publication_delay)

        report_line(uid, hub_domain, 'N/A', hrs, mins, secs)

    except Exception as ex:
        print (ex)