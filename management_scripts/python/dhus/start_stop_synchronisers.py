#script to bulk start or stop dhus

import sys, os
import click
from dhus_odata_api import *
from delete_synchroniser import parse_the_args

@click.command()
@click.option('-c', '--hub-config', 'this_hub_creds', type=str, required=True, help='Location of hub admin credos')
@click.option('-o', '--operation', 'op', type=str, required=True, help='Operation to perform on sycnhroniser.  Can only be "start" or "stop"')
@click.option('-i', '--id', 'id', type=str, help='ID integer of specific synchroniser on target hub')
@click.option('-n', '--name', 'name', type=str, help='Name or substring of name of synchroniser for mass targeted operarations.  i.e. S1A_SLC')
@click.option('-A', '--all', is_flag=True, help='Name or substring of name of synchroniser for mass targeted operarations.  i.e. S1A_SLC')
def main(this_hub_creds, op, id, name, all):

    if not op:
        print ("Please  specify an operation.  either 'start' or 'stop' will do.")
        sys.exit()

    if op not in ['start', 'stop']:
        print ("Please use either 'start' or 'stop' ")
        sys.exit()

    if not all:

        if not id and not name:
            print("Please supply either an ID (-i) OR a name or substring (-n) for dhus! (or just use -A flag to select all) ")
            sys.exit()

        if id and name:
            print("Please supply either an ID (-i) OR a name or substring (-n) for dhus! (or just use -A flag to select all)")
            sys.exit()

    sync_ids = parse_the_args(this_hub_creds, id, name, all)

    hub, hub_uname, hub_password = get_hub_creds(this_hub_creds)

    try:
        sync_template = get_synchronisers(this_hub_creds)

        entries = synchroniser_entries_request(sync_template, request=op)

    except Exception as ex:
        print(f"Could not list dhus for hub: {this_hub_creds} ({ex}")
        sys.exit()

    if not id and name:
        #find matching ids by name
        pass

    for id in sync_ids:

        entry_xml = entries[id]

        odata_stub = 'v1/Synchronizers'

        resp = POST_to_hub(hub, hub_uname, hub_password, entry_xml, PUT=True, synchroniser_id = id, odata_stub = odata_stub)
        #resp = POST_to_hub(hub, hub_uname, hub_password, entry_xml, synchroniser_id=id, odata_stub=odata_stub)

        print(resp)

    #for sync in entries.keys():
     #   print (f"Label: {sync} (id = {entries[sync]['id']}, status = {entries[sync]['status']})")

    print (f"{op} {len(sync_ids)} dhus for hub {this_hub_creds} ")

if __name__ == '__main__':
    main()
