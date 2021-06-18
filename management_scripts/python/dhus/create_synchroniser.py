#Script to replace shell script for update of SRH sycnhronizers.
# SJD April 2020

import sys, os
import requests
from requests.auth import HTTPBasicAuth
import datetime
import click
import configparser

from dhus_odata_api import *

def label(params_file, filter= None, src_hub = None, loc = None):
    '''
    Method to generate a synchroniser or evictor label according to ceda convention
    :return:
    '''

    # label
    if src_hub:
        hub_label = src_hub.replace('https://', '').replace('http://', '').split('.')[0]

    else:
        hub_label = ''

    if loc:
        loc = loc

    else:
        #assume global extent if no loc label.  perfectly reasonable....
        loc = 'GLOB'

    if not filter:
        label_base = f"{os.path.basename(params_file)}_{loc}_{hub_label}_"

    else:
        label_base = f"{filter}_{loc}_{hub_label}_"

    #label = f"{label_base}_{datetime.datetime.now().strftime('%d%m%YT%H%M%S')}"
    #NOTE: just return label base for now as the dt can be added in the sync generator
    return label_base

def create_synchroniser(sync_template, params, src_hub, src_uname, src_password,  lastcreationdate, label_base, geofilter=None, existing_synchronisers = None, filter = None):
    '''
    Method to put together the various bits and create the relevant synchroniser.  Will append a label tag if needed
    :param sync_template:
    :param params:
    :param geofilter:
    :return:
    '''

    for line in params:
        hook = line.split("=")[0]
        value = line.split("=")[1]

        #over ride filter parameter
        if 'D_FILTERPARAM' in hook and filter:
            sync_template = sync_template.replace('D_FILTERPARAM', f"startswith(Name,'{filter}')")

        sync_template = sync_template.replace(hook, value)

    label_tag = f"{label_base}_{datetime.datetime.now().strftime('%d%m%YT%H%M%S')}"

    sync_template = sync_template.replace('D_LABEL', label_tag)

    if existing_synchronisers:
        for used_labels in existing_synchronisers.keys():
            if label_base in used_labels:
                return (f"Looks like there is already a synchroniser for '{label_base} ({used_labels})'!"), False

    # source hub
    sync_template = sync_template.replace('D_SERVICEURL', src_hub)
    sync_template = sync_template.replace('D_SERVICELOGIN', src_uname)
    sync_template = sync_template.replace('D_SERVICEPASSWORD', src_password)

    # last creation date
    lcd = lastcreationdate

    sync_template = sync_template.replace('D_LASTCREATIONDATE', lcd)

    if geofilter:
        sync_template = sync_template.replace('D_GEOFILTER', geofilter)

    return sync_template, True

@click.command()
@click.option('-p', '--params-file', 'params_file', type=str, required=True, help='Basic parameters file for dhus')
@click.option('-c', '--HOST-hub-config', 'this_hub_creds', type=str, required=True, help='hub credentials file for hub to run dhus FROM (i.e. ceda relay hub)')
@click.option('-s', '--SOURCE-hub-config', 'source_hub_creds', type=str, required=True, help='hub credentials file for hub to dhus TO (i.e. colhub)')
@click.option('-l', '--LastCreationDate', 'lastcreationdate', type=str,  required=False, help='LastCreationDate. Use format YYYY-MM-DDTHH:MM:SS. If not set will default to 00:00:00 pf current date')
@click.option('-b', '--BoundingBox-config', 'bboxes_cfg', type=str,  required=False, help='Boundingbox config if supplied.')
@click.option('-P', '--product-string', 'product_string', type=str,  required=False, help='Product string - will override D_FILTERPARAM in params file.')

def main(params_file, this_hub_creds, source_hub_creds, lastcreationdate, bboxes_cfg, product_string):

    '''
    if len(sys.argv) != 6:
        print (f"Usage: {os.path.basename(sys.argv[0])} <sync params file> <creds for hub the synchroniser will run ON> <creds for hub synchroninising FROM>  <last creation date.\
          Use 'None' and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS> <bounding box config.  Use 'None' for no bboxes>")
        sys.exit()

    params_file = sys.argv[1] # params file
    this_hub_creds = sys.argv[2] # creds for hub the synchroniser will run ON
    source_hub_creds = sys.argv[3] # creds for hub synchroninising FROM
    lastcreationdate = sys.argv[4] #last creation date.  Use "None" and will set to 00:00:00 of todays date.  Note format YYYY-MM-DDTHH:MM:SS
    bboxes_cfg = sys.argv[5]
    '''

    geo = False
    remote_incoming = False

    if not lastcreationdate:
        lastcreationdate = datetime.datetime.now().strftime('%Y-%m-%dT00:00:00')

    if not bboxes_cfg:
        areas = None

    else:
        geo = True

        # get the bboxes etc from the cfg
        bboxes = get_config(bboxes_cfg)

        areas = {}

        # extract priority search strings
        for bbox in bboxes.sections():
            areas[bbox] = (bboxes.get(bbox, 'string'))

    #get params file
    try:
        with open(params_file, 'r') as reader:
            params = [i.strip() for i in reader.readlines()]

    except Exception as ex:
        print (f"Cannot open template file ({ex}")
        sys.exit()

    #is remote incoming in the list of params?
    for parameter in params:
        if 'D_REMOTEINCOMING' in parameter:
            remote_incoming = True

    sync_template = get_sync_template(geo = geo, remote_incoming = remote_incoming)

    #override product string?
    if product_string:
        filter_param = product_string

    else:
        filter_param = None

    try:

        #hub to synchronise FROM
        src_hub, src_uname, src_password = get_hub_creds(source_hub_creds)

        #local hub to synchronise TO
        hub, hub_uname, hub_password = get_hub_creds(this_hub_creds)

    except Exception as ex:
        print (f"Cannot access configurations: {ex}")
        sys.exit()

    #get existing dhus, if any
    try:
        existing_synchronisers = synchroniser_summary(get_synchronisers(this_hub_creds))

    except Exception as ex:
        print (f"Cannot access hub to assess existing dhus: {ex}")
        sys.exit()

    #extract params
    if not os.path.exists(params_file):
        print (f"No params file: {params_file}")
        sys.exit()

    existing_synchronisers = None
    if areas is None:
        #No geographic areas, assume global extent

        # work out label
        label_base = label(params_file, src_hub, filter_param, loc=None)

        sync_template, cont = create_synchroniser(sync_template, params, src_hub, src_uname, src_password, lastcreationdate, label_base, existing_synchronisers = existing_synchronisers, filter = filter_param)

        #sys.exit()

        # Now post to SRH hub.
        if cont:
            hub = synchroniser_id_url(hub)

            header = {"Content-type": "application/atom+xml",
                      "Accept": "application/atom+xml"}

            resp = POST_to_hub(hub, hub_uname, hub_password, header, data=sync_template)

        print (resp)

    else:
        for bbox in areas.keys():

            # work out label
            label_base = label(params_file, src_hub, filter_param, loc = bbox)

            sync_template, cont = create_synchroniser(sync_template, params, src_hub, src_password, lastcreationdate, label_base, geofilter=areas[bbox], \
                                existing_synchronisers = existing_synchronisers)


            if cont:
                resp = POST_to_hub(hub, hub_uname, hub_password, data=sync_template)

            print (resp)

if __name__ == '__main__':
    main()
