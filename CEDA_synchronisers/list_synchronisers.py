#Script to list sychronisers on a given SRH hub

import os, sys
import datetime
from get_product_details import analyse_delay, daily_report
from synchroniser import *

PUB_DELAY = 4 #hours!

#from .synchroniser import get_synchronisers

if __name__ == '__main__':

    try:
        #Synchronizers
        synchronisers = synchroniser_summary(get_synchronisers(sys.argv[1]))

    except Exception as ex:
        print (f"Could not list synchronisers for hub: {sys.argv[1]} ({ex})")
        sys.exit()

    for sync in synchronisers.keys():
        lcd = synchronisers[sync]['lcd']

        days, hrs, mins, secs = analyse_delay(datetime.datetime.now() - datetime.datetime.strptime(lcd, '%Y-%m-%dT%H:%M:%S.%f'))

        #delay_report = (f"{str(days).zfill(2)} (days), {str(hrs).zfill(2)}:{str(mins).zfill(2)}:{str(secs).zfill(2)} (HH:MM:SS)")
        delay_str = daily_report(days, hrs, mins, secs)

        if days > 1 or hrs > PUB_DELAY:
            print (f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']}), publication_delay = {delay_str}, last creation date = {lcd}) [WARNING! Publication delay {PUB_DELAY} hrs EXCEEDED!]")

        else:
            print (f"Label: {sync} (id = {synchronisers[sync]['id']}, status = {synchronisers[sync]['status']}, publication_delay = {delay_str}, last creation date = {lcd})")

    print (f"Found {len(synchronisers.keys())} synchronisers for hub {sys.argv[1]}")