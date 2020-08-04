import os, sys
from synchroniser import *
from datetime import datetime
from urllib.parse import urlparse


CR_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}CreationDate'
IN_DATE_XP = '{http://schemas.microsoft.com/ado/2007/08/dataservices/metadata}properties/{http://schemas.microsoft.com/ado/2007/08/dataservices}IngestionDate'

if __name__ == '__main__':
    #http: // srh - services3.ceda.ac.uk / odata / v1 / Products('52199a54-790e-449d-ae20-548d83313ae5')

    hub_config = sys.argv[1]
    uid = sys.argv[2]

    stub = f"Products('{uid}')"

    msg = None

    try:
        #whats the hub (for reporting purposes)
        hub, u,pwd  = get_hub_creds(hub_config)

        del u; del pwd

        hub_domain = urlparse(hub).netloc

        #root = access_xml_file(GET_from_hub(hub_config, odata_stub=stub))
        content = GET_from_hub(hub_config, odata_stub=stub)

        if content.status_code in [200,201]:
            root = get_existing_details(content.text)

            creation_date = datetime.strptime(root.find(CR_DATE_XP).text, '%Y-%m-%dT%H:%M:%S.%f')
            ingestion_date = datetime.strptime(root.find(IN_DATE_XP).text, '%Y-%m-%dT%H:%M:%S.%f')

            #whats the difference
            publication_delay = ingestion_date - creation_date

            hrs = int(publication_delay.seconds / 3600)
            mins = int((publication_delay.seconds % 3600) / 60)
            secs = publication_delay.seconds - ( (hrs * 3600) + (mins *60))

            msg = f"Product {uid} on hub {hub_domain}: publication delay (HH:MM:SS): {str(hrs).zfill(2)}:{str(mins).zfill(2)}:{str(secs).zfill(2)}"

        else:
            raise Exception(f"Hub return code: {content.status_code}")

    except Exception as ex:
        msg = f"Cannot extract data on {uid} ({ex})"

    print (msg)
