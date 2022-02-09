import os, sys, re, urllib

sys.path.append(".")
sys.path.append("..")

import click
from click import command, option, Option, UsageError
from collections import defaultdict
import numpy as np

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


def get_date_from_logline(line):
    #extract date from dhus logline.  i.e. [2.7.8-osf][2021-11-19 00:00:00,002][INFO ] Scheduled eviction job started (EvictionJob.java:39 - DefaultQuartzScheduler_Worker-1)'
    return str(re.findall("[0-9]{4}-[0-9]{2}-[0-9]{2}",str(re.findall("\[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}\:[0-9]{2}\:[0-9]{2},[0-9]{3}\]", line)[0]))[0])


def get_successful_downloads(lines):
    '''
    Method to wrap the log analyser using known good values to hook into the log
    :return:
    '''


    #successful_syncs, bad_cnt = analyse_log(lines, ['Products(', 'successfully downloaded', '.zip'])
    #successful_syncs, bad_cnt = analyse_log(lines, ['Products(', 'successfully downloaded'])
    successful_syncs, bad_cnt = analyse_log_successful(analyse_log(lines, ['Products(', 'successfully downloaded']))

    return successful_syncs, bad_cnt


def get_repeat_downloads(lines):

    # count how many INITIAL synchronising attempts made on a per product basis to the queue
    #in order to pick up synchroniser initiations the etc/log4j2.xml must have this logger: <logger name="fr.gael.dhus.sync.impl.ODataProductSynchronizer" level="debug"/>
    downloads_per_product, product_retries, products_sync_attempted, bad_cnt = analyse_log_progress_duplicates(analyse_log(lines, ['in progress']))
    #downloads_per_product, bad_cnt = analyse_log_progress_duplicates(analyse_log(lines, ['to the queue']))

    return downloads_per_product, product_retries, products_sync_attempted, bad_cnt


def analyse_log_progress_duplicates(lines):
    '''
    Method to pull out product names in lines found with "In progress" as this indicates the start of a sync
    :param lines:
    :return:
    '''
    tot_product_syncs = {} # organise by product - note hub cannot be extracted from this log line.  NOTE only in debug mode..
    bad_cnt = 0
    #print (f"{len(lines)}")
    for line in lines:
        try:
            product_name = re.findall("S[1-5][A-P].*", line)[0].split(' ')[0]

            # now we discover this is not true for S2...
            if 'S2' == product_name[0:2]:
                product = product_name[0:10]
            else:
                product = product_name[0:12]

            if product not in tot_product_syncs.keys():
                tot_product_syncs[product] = [product_name]

            else:
                tot_product_syncs[product].append(product_name)

        except Exception as ex:
            # todo something wrong with the log parsing etc.  deal with it later
            # print (ex)
            bad_cnt += 1

    #now run through the list of retrieve attempts by product and look at how many are duplicated
    duplicates_by_product = {}
    product_retries = {}
    unique_products = {}

    for product in tot_product_syncs.keys():
        dups = {}
        tot_retries = 0
        for uniq_download in np.unique(np.array(tot_product_syncs[product])):
            retries = tot_product_syncs[product].count(uniq_download)
            dups[uniq_download] = retries
            tot_retries += retries
        product_retries[product] = tot_retries
        duplicates_by_product[product] = dups
        unique_products[product] = list(duplicates_by_product[product].keys())

    '''
    #now need to create an array that will allow us to filter by the proper total
    indexable_products = {}
    for product in tot_product_syncs.keys():
        temp = {}
        for i in tot_product_syncs[product]:
            #get how many times this has been downloaded from the simple list
            temp[i] = duplicates_by_product[product][i]

        indexable_products[product] = temp
    '''

    #now work out the distribution
    downloads_per_product = {}
    for product in duplicates_by_product:
        downloads = {}

        for download_attempts in np.unique(np.array(list(duplicates_by_product[product].values()))):
            downloads[download_attempts] = list(duplicates_by_product[product].values()).count(download_attempts)
            #downloads[download_attempts] = tot_product_syncs[product].count(download_attempts)

        downloads_per_product[product] = downloads

    return downloads_per_product, product_retries, unique_products, bad_cnt


def analyse_log_successful(lines):
    successful_syncs = {}
    bad_cnt = 0

    for line in lines:

        try:
            uid = re.findall("'([a-zA-Z0-9-]*)'", line)[0]
            product_name = re.findall("'S[1-5][A-P].*[\.nc,\.zip]'", line)[0].replace('\'', '').split('.')[0]

            # print (product_name)

            # now we discover this is not true for S2...
            if 'S2' == product_name[0:2]:
                product = product_name[0:10]
            else:
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


def analyse_log(lines, phrases):
    '''
    Method to analyse lines of the log for presence of ALL given phrases.  Note some assumptions are made ie. presence of data url etc  - but we know what we're looking for ....
    :param lines:
    :return:
    '''

    cnt = 0

    matching_lines = []

    for line in lines:
        #if 'Products(' in line and 'successfully downloaded' iS[1-5][A-P].[\.nc,\.zip]n line and '.zip' in line:

        #Are ALL the phrases requested present in the current line?
        phrases_present = [i in line for i in phrases]
        line_match = True
        for presence in phrases_present:
            if not presence:
                line_match = False

        if line_match:
            matching_lines.append(line)

    return matching_lines


def work_out_difference_attempted_syncs_and_successful_syncs(attempted_syncs, successful_syncs):

    differences  = {}

    #need to filter the succesful syncs due to the data structure

    for product in attempted_syncs:
        actual_syncs = [list(successful_syncs[i]['uids'].values()) for i in successful_syncs.keys() if
                        product in successful_syncs[i]['products']][-1]

        differences[product] = list(set(attempted_syncs[product]) - set(actual_syncs))

    return differences

def output_successful_distribution_summary(successful_syncs, successful_sync_distrib, bad_cnt, repeat_syncs, product_retries, differences):
    '''
    Method to generate report
    :return:
    '''
    total_of_totals = 0
    total_download_attempts = 0

    for sync in successful_syncs.keys():
        for product in [j for j in successful_syncs[sync]['products']]:
            available_dates = [i for i in successful_sync_distrib[sync][product]]
            available_dates.sort()

            print(f"********* {product} *********")
            print(f"\nProduct sensing date distribution")
            total_scenes = 0
            for datek in available_dates:
                number_scenes = successful_sync_distrib[sync][product][datek]
                print(f"{datek.strftime('%d/%m/%Y')}:{number_scenes}")
                total_scenes += number_scenes

            print(f"\nTotal SUCCESSFUL synchronisations: {total_scenes}\n")
            total_of_totals += total_scenes

            #
            #product_retries
            if product in product_retries.keys():
                for i in repeat_syncs[product].keys():
                    num = repeat_syncs[product][i]
                    print (f"{num} Products with {i} synchronisation initiation attempts ")

            #total = 0
            #for i in product_retries[product]:
            #sometimes there cabn be a disparity in product keys
            if product in product_retries.keys():
                print (f"\nTotal number of synchronisation attempts attempts: {product_retries[product]}")
                    #total += num
                #print (f"Total: {total}")


            if product in product_retries.keys():
                total_download_attempts += product_retries[product]

            if product in differences.keys():
                print (f"Number of products attempted to sync that did NOT finally download at all: {len(differences[product])}")
                print("\n")

    print(f"Absolute total: {total_of_totals}\n")
    print(f"Total number of synchronisations started: {total_download_attempts}")

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

    #get information on repeat attempted downloads
    repeat_syncs, product_retries, products_sync_attempted,bad_cnt = get_repeat_downloads(lines)

    #analyse successful downloads for number of files per days retrieved.
    # i.e. are we only getting data from last few days or are there older reprocessed data in there?
    successful_sync_distrib = get_date_distribution(successful_syncs)

    differences = work_out_difference_attempted_syncs_and_successful_syncs(products_sync_attempted, successful_syncs)

    #print to stdcout/report what we've found
    output_successful_distribution_summary(successful_syncs, successful_sync_distrib, bad_cnt, repeat_syncs, product_retries, differences)

    #look for failed downloads
    #successful_syncs, bad_cnt = analyse_log(lines, ['[ERROR] PRODUCT SKIPPED', 'failed to download'])



    #todo: summarise by acq date etc and run so can get publication delay using report publication delay.

if __name__ == '__main__':
    main()
