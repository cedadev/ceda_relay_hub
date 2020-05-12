#script to bulk start or stop synchronisers

import sys, os

from synchroniser import *
from delete_synchroniser import parse_the_args

def usage():
    print(
        f"Usage: {os.path.basename(sys.argv[0])} <hub params file> <start or stop> <synchronoser id or 'None' for all> <string to match to remove. 'None' if using number>")
    sys.exit()


if __name__ == '__main__':

    if len(sys.argv) != 5:
        usage()

    this_hub_creds = sys.argv[1]
    op = sys.argv[2]
    id = sys.argv[3]
    name = sys.argv[4]

    operations = ['start', 'stop']

    if id in ['None', 'none']:
        id = None

    if op not in operations:
        print ("Please use either 'start' or 'stop' ")
        sys.exit()

    if name in ['None', 'none']:
        name = None

    if not id and not name:
        usage()

    if id and name:
        usage()

    sync_ids = parse_the_args(this_hub_creds, id, name)

    hub, hub_uname, hub_password = get_hub_creds(this_hub_creds)

    try:
        sync_template = get_synchronisers(this_hub_creds)

        entries = synchroniser_entries_request(sync_template, request=op)

    except Exception as ex:
        print(f"Could not list synchronisers for hub: {sys.argv[1]} ({ex}")
        sys.exit()

    if not id and name:
        #find matching ids by name
        pass

    for id in sync_ids:

        entry_xml = entries[id]

        resp = POST_to_hub(hub, hub_uname, hub_password, entry_xml, PUT=True, synchroniser_id = id)

        #print(resp)

    #for sync in entries.keys():
     #   print (f"Label: {sync} (id = {entries[sync]['id']}, status = {entries[sync]['status']})")

    print (f"{op} {len(sync_ids)} synchronisers for hub {sys.argv[1]} ")