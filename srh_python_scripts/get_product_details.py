import os, sys
from synchroniser import *
from datetime import datetime
from urllib.parse import urlparse

'''
Run from shell after parsing dhus log file for successfully downloaded files for UID's using shell incantation command like this:

 grep  'successfully downloaded from' /srh/data/logs/dhus.log | awk '{print $12}' | head -100  | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u

'''

CR_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}CreationDate'
IN_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}IngestionDate'

def get_product_details(hub_config, uid):
    '''
    Method to access Products xml file for a given UID on the hub
    :return:
    '''

    stub = f"Products('{uid}')"

    msg = None

    try:
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

            # whats the difference
            publication_delay = ingestion_date - creation_date

            if publication_delay.days < 1:
                days = 0
            else:
                days = int(publication_delay.days)

            hrs = int(publication_delay.seconds / 3600)
            mins = int((publication_delay.seconds % 3600) / 60)
            secs = publication_delay.seconds - ((hrs * 3600) + (mins * 60))

            msg = f"Product {uid} on hub {hub_domain}: publication delay (Days - HH:MM:SS): {str(days).zfill(2)} - {str(hrs).zfill(2)}:{str(mins).zfill(2)}:{str(secs).zfill(2)}"

        else:
            raise Exception(f"Hub return code: {content.status_code}")

    except Exception as ex:
        msg = f"Cannot extract data on {uid} ({ex})"

    print(msg)

if __name__ == '__main__':
    #http: // srh - services3.ceda.ac.uk / odata / v1 / Products('52199a54-790e-449d-ae20-548d83313ae5')

    hub_config = sys.argv[1]
    uid = sys.argv[2]

    get_product_details(hub_config, uid)
