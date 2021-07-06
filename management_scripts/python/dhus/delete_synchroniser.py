#script to delete one or a list of dhus
import os, sys
import requests
from requests.auth import HTTPBasicAuth
import click

from dhus_odata_api import *

def parse_the_args(hub_creds, syncs, name):
    '''Need this as several different modes'''
    try:
        existing_synchronisers = synchroniser_summary(get_synchronisers(hub_creds))
        sync_ids = [i['id'] for i in existing_synchronisers.values()]

    except:
        print ("Unable to contact hub!")
        sys.exit()

    # crappy way to do it but I'm outa time for fancy pancy arg parsing and logic.
    if syncs == 'None' and name == 'None':
        print ("Please supply either a synchroniser id (-i) or specify all")
        sys.exit()

    elif syncs in ['All', 'all', 'ALL'] and name in ['None', 'none', None]:
        #All dhus and no name match
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
        print("Please supply proper args - please use -h option")
        sys.exit()


@click.command()
@click.option('-c', '--hub-config', 'hub_creds', type=str, required=True, help='Location of hub admin credos')
@click.option('-i', '--id', 'syncs', type=str, help='ID integer of specific synchroniser on target hub.  "ALL" will delete all')
@click.option('-n', '--name', 'name', type=str, help='Name or substring of name of synchroniser for mass targeted operarations.  i.e. S1A_SLC')
def main(hub_creds, syncs, name):

    '''
    hub_creds = sys.argv[1]
    syncs = sys.argv[2]
    name = sys.argv[3]
    '''

    sync_ids = parse_the_args(hub_creds, syncs, name)

    hub, hub_uname, hub_password = get_hub_creds(hub_creds)

    for id in sync_ids:
        #Synchronizers
        sync = synchroniser_id_url(hub,id)

        response = requests.delete(sync, auth=HTTPBasicAuth(hub_uname, hub_password))

        if response.status_code == 204:
            print (f"Have successfully deleted synchroniser {id} for hub creds {hub_creds}")

        else:
            print(f"ERROR: cannot delete synchroniser {id} for hub creds {hub_creds} (error code {response.status_code})")


if __name__ == '__main__':
    main()
