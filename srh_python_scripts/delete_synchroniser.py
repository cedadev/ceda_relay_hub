#script to delete one or a list of synchronisers
import os, sys
import requests
from requests.auth import HTTPBasicAuth

from synchroniser import *

def usage():
    usage = f"Usage {os.path.basename(sys.argv[0])} <hub params file> <synchroniser ID number or 'All' to remove all. 'None' if using name> <string to match to remove. 'None' if using number> "
    sys.exit()

def parse_the_args(hub_creds, syncs, name):

    try:
        existing_synchronisers = synchroniser_summary(get_synchronisers(hub_creds))
        sync_ids = [i['id'] for i in existing_synchronisers.values()]

    except:
        print ("Unable to contact hub!")
        sys.exit()

    # crappy way to do it but I'm outa time for fancy pancy arg parsing and logic.
    if syncs == 'None' and name == 'None':
        usage()

    elif syncs in ['All', 'all'] and name in ['None', 'none', None]:
        #All synchronisers and no name match
        return sync_ids

    elif name in ['None', 'none', None]:
        #Specific id
        if syncs in sync_ids:
            return [syncs]

    elif syncs in ['None', 'none', None] and name not in ['None', 'none', None]:
        #Synchronisers based on name match and

        sync_ids = []

        # find
        for label in existing_synchronisers.keys():
            if name in label:
                sync_ids.append(existing_synchronisers[label]['id'])

        return sync_ids

    elif syncs != 'All' and name == 'None':

        sync_ids = [syncs]

    else:
        usage()



if __name__ == '__main__':

    if len(sys.argv) != 4:
        print (usage)
        sys.exit()

    hub_creds = sys.argv[1]
    syncs = sys.argv[2]
    name = sys.argv[3]

    sync_ids = parse_the_args(hub_creds, syncs, name)

    hub, hub_uname, hub_password = get_hub_creds(hub_creds)

    for id in sync_ids:

        response = requests.delete(synchroniser_id_url(hub,id), auth=HTTPBasicAuth(hub_uname, hub_password))

        if response.status_code == 204:
            print (f"Have successfully deleted synchroniser {id} for hub creds {hub_creds}")

        else:
            print(f"ERROR: cannot delete synchroniser {id} for hub creds {hub_creds} (error code {response.status_code})")
