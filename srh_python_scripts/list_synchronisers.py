#Script to list sychronisers on a given SRH hub

import os, sys

from synchroniser import *

#from .synchroniser import get_synchronisers

if __name__ == '__main__':

    try:
        #Synchronizers
        synchronisers = synchroniser_summary(get_synchronisers(sys.argv[1]))

    except Exception as ex:
        print (f"Could not list synchronisers for hub: {sys.argv[1]} ({ex})")
        sys.exit()

    for sync in synchronisers.keys():
        print (f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']})")

    print (f"Found {len(synchronisers.keys())} synchronisers for hub {sys.argv[1]}")