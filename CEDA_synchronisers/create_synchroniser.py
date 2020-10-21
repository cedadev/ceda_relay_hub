#Script to replace shell script for update of SRH sycnhronizers.
# SJD April 2020

import sys, os
import requests
from requests.auth import HTTPBasicAuth
import datetime
import configparser

from synchroniser import *

def create_synchroniser(sync_template, params, src_hub, geofilter=None, label_tag=None, existing_synchronisers = None):
    '''
    Method to put together the various bits and create the relevant synchroniser.  Will append a label tag if needed
    :param sync_template:
    :param params:
    :param geofilter:
    :return:
    '''

    if not label_tag:
        loc = 'GLOB'

    else:
        loc = label_tag

    for line in params:
        hook = line.split("=")[0]
        value = line.split("=")[1]
        sync_template = sync_template.replace(hook, value)

    # label
    label_base = (f"{os.path.basename(params_file)}_{loc}_")
    label = (f"{label_base}_{datetime.datetime.now().strftime('%d%m%YT%H%M%S')}")
    sync_template = sync_template.replace('D_LABEL', label)

    if existing_synchronisers:
        for used_labels in existing_synchronisers.keys():
            if label_base in used_labels:
                return (f"Looks like there is already a synchroniser for '{label_base} ({used_labels})'!"), False

    # source hub
    sync_template = sync_template.replace('D_SERVICEURL', src_hub)
    sync_template = sync_template.replace('D_SERVICELOGIN', src_uname)
    sync_template = sync_template.replace('D_SERVICEPASSWORD', src_password)

    # last creation date
    if lastcreationdate is None or lastcreationdate == 'None' or lastcreationdate == 'none':
        lcd = datetime.datetime.now().strftime('%Y-%m-%dT00:00:00')

    else:
        lcd = lastcreationdate

    sync_template = sync_template.replace('D_LASTCREATIONDATE', lcd)

    if geofilter:
        sync_template = sync_template.replace('D_GEOFILTER', geofilter)

    return sync_template, True


if __name__ == '__main__':

    if len(sys.argv) != 6:
        print (f"Usage: {os.path.basename(sys.argv[0])} <sync params file> <creds for hub the synchroniser will run ON> <creds for hub synchroninising FROM>  <last creation date.\
          Use 'None' and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS> <bounding box config.  Use 'None' for no bboxes>")
        sys.exit()

    params_file = sys.argv[1] # params file
    this_hub_creds = sys.argv[2] # creds for hub the synchroniser will run ON
    source_hub_creds = sys.argv[3] # creds for hub synchroninising FROM
    lastcreationdate = sys.argv[4] #last creation date.  Use "None" and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS
    bboxes_cfg = sys.argv[5]

    #hub to synchronise FROM
    src_hub, src_uname, src_password = get_hub_creds(source_hub_creds)

    #local hub to synchronise TO
    hub, hub_uname, hub_password = get_hub_creds(this_hub_creds)

    #get existing synchronisers, if any
    try:
        existing_synchronisers = synchroniser_summary(get_synchronisers(this_hub_creds))

    except Exception as ex:
        print (f"Cannot access hub to assess existing synchronisers: {ex}")
        sys.exit()

    if bboxes_cfg is None or bboxes_cfg == 'None' or bboxes_cfg == 'none':
        sync_template = get_sync_template()

        areas = None

    else:
        sync_template = get_sync_template(geo=True)

        #get the bboxes etc from the cfg
        bboxes = get_config(bboxes_cfg)

        areas = {}

        # extract priority search strings
        for bbox in bboxes.sections():
            areas[bbox] = (bboxes.get(bbox, 'string'))

    #extract params
    if os.path.exists(params_file):
        with open(params_file, 'r') as reader:
            params = [i.strip() for i in reader.readlines()]

    else:
        print (f"No params file: {params_file}")
        sys.exit()

    existing_synchronisers = None
    if areas is None:
        #No geographic areas
        sync_template, cont = create_synchroniser(sync_template, params, src_hub, existing_synchronisers = existing_synchronisers)

        #sys.exit()

        # Now post to SRH hub.
        if cont:
            resp = POST_to_hub(hub, hub_uname, hub_password, data=sync_template)

        print (resp)

    else:
        for bbox in areas.keys():
            sync_template, cont = create_synchroniser(sync_template, params, src_hub, geofilter=areas[bbox], label_tag=bbox, \
                                existing_synchronisers = existing_synchronisers)


            #sys.exit()

            if cont:
                resp = POST_to_hub(hub, hub_uname, hub_password, data=sync_template)

            print (resp)


