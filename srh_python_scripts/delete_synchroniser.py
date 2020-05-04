#script to delete one or a list of synchronisers
import os, sys
import requests
from requests.auth import HTTPBasicAuth

from synchroniser import *

if len(sys.argv) != 4:
    print (f"Usage {os.path.basename(sys.argv[0])} <hub params file> <synchroniser ID number or 'ALL' to remove all. 'None' if using name> <string to match to remove. 'None' if using number> ")
    sys.exit()

hub_creds = sys.argv[1]
sync = sys.argv[2]
name = sys.argv[3]

#if sync == 'None' or sync == 'NONE'

hub, hub_uname, hub_password = get_hub_creds(hub_creds)

sync_id = sync

delete_url = synchroniser_id_url(hub,sync_id)

response = requests.get(hub, auth=HTTPBasicAuth(hub_uname, hub_password))

requests.delete(hub_sync_url, auth=HTTPBasicAuth(hub_uname, hub_password))

pass