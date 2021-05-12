
import sys, os
import requests
from requests.auth import HTTPBasicAuth
import datetime
import click
import configparser

from dhus_odata_api import *
from create_synchroniser import label

def create_evictor(template, params, label_base, filter = None):
    '''
    Method to put together the various bits and create the relevant synchroniser.  Will append a label tag if needed
    :param template:
    :param params:
    :param geofilter:
    :return:
    '''

    for line in params:
        hook = line.split("=")[0]
        value = line.split("=")[1]

        #over ride filter parameter
        if 'D_FILTERPARAM' in hook and filter:
            template = template.replace('D_FILTERPARAM', f"startswith(Name,'{filter}')")

        template = template.replace(hook, value)

    label_tag = f"{label_base}_{datetime.datetime.now().strftime('%d%m%YT%H%M%S')}"

    template = template.replace('D_LABEL', label_tag)

    '''
    if existing_synchronisers:
        for used_labels in existing_synchronisers.keys():
            if label_base in used_labels:
                return (f"Looks like there is already a synchroniser for '{label_base} ({used_labels})'!"), False
    '''
    '''
    # last creation date
    lcd = lastcreationdate

    template = template.replace('D_LASTCREATIONDATE', lcd)

    
    if geofilter:
        template = template.replace('D_GEOFILTER', geofilter)
    '''

    return template, True

@click.command()
@click.option('-p', '--params-file', 'params_file', type=str, required=True, help='Basic parameters file for synchronisers')
@click.option('-c', '--HOST-hub-config', 'this_hub_creds', type=str, required=True, help='hub credentials file for hub to run synchronisers FROM (i.e. ceda relay hub)')
@click.option('-P', '--product-string', 'product_string', type=str,  required=False, help='Product string - will override D_FILTERPARAM in params file.')
def main(params_file, this_hub_creds, product_string):

    # get params file
    try:
        with open(params_file, 'r') as reader:
            params = [i.strip() for i in reader.readlines()]

    except Exception as ex:
        print(f"Cannot open template file ({ex}")
        sys.exit()

    evict_template = get_evict_template()

    # work out label
    label_base = label(params_file)

    evict_template = create_evictor(evict_template, params, label_base)

    print ("here")

if __name__ == '__main__':
    main()

