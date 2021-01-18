import sys, re, urllib

sys.path.append(".")
sys.path.append("..")

import click
from click import command, option, Option, UsageError
from collections import defaultdict

from analyse_logs.Sentinel import Sentinel_Product

'''
Script to extract SUCCESSFULLY synchronised data from a hub log and index by source and unique ids.

Use as a basis for analysing hub delays as extracts UID's etc which other (older) scripts do not
'''


'''#grep  'successfully downloaded from' /srh/data/logs/dhus.log | grep S3B_SL_1_RBT  
| awk '{print $12}' | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" 
| sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u'''

def get_date_distribution(successful_syncs):
    '''
    Method to analyse the date distribution of retrieved data
    :param successful_syncs:
    :return:
    '''
    prod_by_date = defaultdict(dict)
    for sync in successful_syncs.keys():

        # products for this hub
        for product in [j for j in successful_syncs[sync]['products']]:

            distribution = {}

            for scene in [k for k in successful_syncs[sync]['uids'].values()]:
                if product in scene:
                    k = Sentinel_Product(scene)
                    #dt = k.get_product_date().strftime('%d/%m/%Y')
                    #convert to a simple date object to aid sorting later on....
                    dt = k.get_product_date(date=True)

                    if dt not in distribution.keys():
                        distribution[dt] = 1

                    else:
                        distribution[dt] += 1

            prod_by_date[sync][product] = distribution

    return prod_by_date


def get_successful_downloads(lines):
    '''
    Method to wrap the log analyser using known good values to hook into the log
    :return:
    '''

    successful_syncs, bad_cnt = analyse_log(lines, ['Products(', 'successfully downloaded', '.zip'])

    return successful_syncs, bad_cnt


def analyse_log(lines, phrases):
    '''
    Method to analyse lines of the log for presence of ALL given phrases.  Note some assumptions are made ie. presence of data url etc  - but we know what we're looking for ....
    :param lines:
    :return:
    '''

    # index by source i.e. hub
    successful_syncs = {}

    cnt = 0
    bad_cnt = 0
    for line in lines:
        #if 'Products(' in line and 'successfully downloaded' in line and '.zip' in line:

        #Are ALL the phrases requested present in the current line?
        phrases_present = [i in line for i in phrases]
        line_match = True
        for presence in phrases_present:
            if not presence:
                line_match = False

        if line_match:
            try:
                uid = re.findall("'([a-zA-Z0-9-]*)'", line)[0]
                product_name = re.findall("S[1-3][A-B].*\.zip", line)[0]
                product = product_name[0:12]

                # todo: for some reason url parse failed on pycharm run but NOT debug...? replaced with clunkier one liner.  And http?
                # hub = urllib.parse.urlparse(re.findall('https.*/Products', line)[0]).netloc
                hub = re.findall('https.*/Products', line)[0].replace('https://', '').split('/')[0]

                # prime a data struct if needed
                if hub not in successful_syncs.keys():
                    successful_syncs[hub] = {'uids': {}, 'products': []}

                if product not in successful_syncs[hub]['products']:
                    successful_syncs[hub]['products'].append(product)

                if uid not in successful_syncs[hub]['uids']:
                    successful_syncs[hub]['uids'][uid] = product_name

                '''
                #aids debugging large volumes of uids...
                cnt += 1
                if cnt == 10:
                    return successful_syncs, bad_cnt
                '''

            except Exception as ex:
                # todo something wrong with the log parsing etc.  deal with it later
                # print (ex)
                bad_cnt += 1

    return successful_syncs, bad_cnt


def output_successful_distribution_summary(successful_syncs, successful_sync_distrib, bad_cnt):
    '''
    Method to generate report
    :return:
    '''
    total_of_totals = 0
    for sync in successful_syncs.keys():
        for product in [j for j in successful_syncs[sync]['products']]:
            available_dates = [i for i in successful_sync_distrib[sync][product]]
            available_dates.sort()

            print(f"********* {product} *********")
            total_scenes = 0
            for datek in available_dates:
                number_scenes = successful_sync_distrib[sync][product][datek]
                print(f"{datek.strftime('%d/%m/%Y')} {number_scenes}")
                total_scenes += number_scenes

            print(f"Total: {total_scenes}")
            total_of_totals += total_scenes
            print("\n")

    print(f"Absolute total: {total_of_totals}\n")

    # print (f"len: {len(lines)} num uids: {len(uids)} cnt:{cnt}")
    print(f"*************************** Summary ************************\n")
    print(f"Synchronised from {len(successful_syncs.keys())} Hubs")
    for i in successful_syncs.keys():
        data_prods = [j for j in successful_syncs[i]['products']]
        print(f"Hub: {i} Products synchronised: {len(successful_syncs[i]['uids'].keys())} Data products: {data_prods}")

    print(f"Bad lines: {bad_cnt}")

@click.command()
@click.option('-l', '--log-file', 'log', type=str, required=True, help='Log file to analyse')
def main(log):
    #print (urllib.__spec__) # problem with not running in pycharm run, but does when in debug mode

    with open(log, 'r') as f:
        lines = [i.rstrip() for i in f.readlines()]

    #get successful synchroniser structure
    successful_syncs, bad_cnt =  get_successful_downloads(lines)

    #analyse successful downloads for number of files per days retrieved.
    # i.e. are we only getting data from last few days or are there older reprocessed data in there?
    successful_sync_distrib = get_date_distribution(successful_syncs)

    #print to stdcout/report what we've found
    output_successful_distribution_summary(successful_syncs, successful_sync_distrib, bad_cnt)

    #look for failed downloads
    successful_syncs, bad_cnt = analyse_log(lines, ['[ERROR] PRODUCT SKIPPED', 'failed to download'])



    #todo: summarise by acq date etc and run so can get publication delay using report publication delay.

if __name__ == '__main__':
    main()
