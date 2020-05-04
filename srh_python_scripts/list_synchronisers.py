#Script to list sychronisers on a given SRH hub

import os, sys

from synchroniser import *

#from .synchroniser import get_synchronisers

if __name__ == '__main__':

    try:
        synchronisers = get_synchronisers(sys.argv[1])

    except:
        print (f"Could not list synchronisers for hub: {sys.argv[1]}")

    for sync in synchronisers.keys():
        print (f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']})")

