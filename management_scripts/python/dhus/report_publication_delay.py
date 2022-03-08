'''
Wrapper script to take a simple list iof UID's culled from a log file and recursivelt report on each of these

will use uid extractor that couples with hub info from extract_detail_info.py so can look up correct source hub credentials from the specified config dir

grep  'successfully downloaded from' /srh/data/logs/dhus.log | awk '{print $12}'
 | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}'
  | sort -u  > list.txt
'''
"""Extracting useful information from a DHuS Log and calculate Publication Delay for KPI reporting for CEDA Relay Hub
"""
__author__ = "@SteveDonegan"
__date__ = "08/03/22"
__copyright__ = "(C) 2015 Science and Technology Facilities Council"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "steve.donegan@stfc.ac.uk"
__revision__ = '$Id$'

#PUBLICATION DELAY FOR INTERESTS OF CEDA SRH CAN BE DEFINED AS THE LAG BETWEEN THE CREATION DATE ON THE SOURCE HUB AND THE CREATION DATE ON THE LOCAL HUB

import sys, os

sys.path.append("..")

import click
from click import command, option, Option, UsageError
from collections import defaultdict
import random
import datetime

from dhus.get_product_details import get_product_details, report_line, average_delay_hours, analyse_delay, get_delay, UIDnotOnHubError
from analyse_logs.extract_detail_info import get_successful_downloads, get_date_from_logline
from analyse_logs.ceda_dhus_log_summary import find_log_files

#from dhus.synchroniser import get_hub_creds
from dhus_odata_api import *

#SOURCE_SAMPLE_LIMIT = 10 #for the moment sample size to take from the uids retrieved.  If we do all, could swamp the local and remote hubs

#todo: why do some records get missed out - even on a sample of 20?

#see https://gist.github.com/stanchan/bce1c2d030c76fe9223b5ff6ad0f03db - for mutually exclusive options
class MutuallyExclusiveOption(Option):
    def __init__(self, *args, **kwargs):
        self.mutually_exclusive = set(kwargs.pop('mutually_exclusive', []))
        help = kwargs.get('help', '')
        if self.mutually_exclusive:
            ex_str = ', '.join(self.mutually_exclusive)
            kwargs['help'] = help + (
                ' NOTE: This argument is mutually exclusive with '
                ' arguments: [' + ex_str + '].'
            )
        super(MutuallyExclusiveOption, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        if self.mutually_exclusive.intersection(opts) and self.name in opts:
            raise UsageError(
                "Illegal usage: `{}` is mutually exclusive with "
                "arguments `{}`.".format(
                    self.name,
                    ', '.join(self.mutually_exclusive)
                )
            )

        return super(MutuallyExclusiveOption, self).handle_parse_result(
            ctx,
            opts,
            args
        )


def build_config_map(source_hub_config_dir, successful_syncs):
    # build a map of the configs so we can match the hub keys in successful_sync to these
    config_map = {}
    if os.path.exists(source_hub_config_dir):
        for source_hub in successful_syncs.keys():
            for root, dirs, files in os.walk(source_hub_config_dir):
                for name in files:
                    if '.cfg' in name:
                        try:
                            hub, u, pwd = get_hub_creds(os.path.join(root, name))

                            if source_hub in hub:
                                config_map[source_hub] = os.path.join(root, name)

                        except:
                            pass

    else:
        print(f"Source hub directory: {source_hub_config_dir} does not exist!")
        sys.exit()

    if len(config_map.keys()) != len(successful_syncs.keys()):
        #find which one is missing (https://stackoverflow.com/questions/3462143/get-difference-between-two-lists)
        for missing_sync in list(set(successful_syncs.keys()) - set(config_map.keys())):
            print (f"WARNING: unable to find config file for {missing_sync}")

    return config_map


def choose_random_uid(all_available_ids, sample_size):
    '''
    Method to aid choosing of random sample uids from larger set
    :param previous_selections:
    :param nnn:
    :return:
    '''

    uids = []

    #just keep guessing until we find one that hasn't been used before
    while len(uids) < sample_size:

        uid_sample_indx = random.randrange(0, len(all_available_ids))

        if uid_sample_indx not in uids:
            uids.append(all_available_ids[uid_sample_indx])

    if len(uids) != sample_size:
        print ("here")

    return uids


def generate_report(source_configs, local_hub_config, verbose, successful_syncs, sample_number, report_format, line, log_date, specific_uid):
    # group by hub and product- if using primary UID's from log file method, there may be multiple source hubs
    uids_by_product_type = {}
    for source in source_configs.keys():

        source_hub_config = source_configs[source]

        # slice uid list of retrieved data products by product type
        uids_by_product = {}
        for product in successful_syncs[source]['products']:
            uid_list = []
            for scene in [successful_syncs[source]['uids'][i] for i in successful_syncs[source]['uids']]:
                if scene:
                    if product in scene:
                        for ascene in successful_syncs[source]['uids'].keys():
                            if successful_syncs[source]['uids'][ascene] == scene:
                                uid_list.append(ascene)

                else:
                    uid_list.append()

            uids_by_product[product] = uid_list

        uids_by_product_type[source] = uids_by_product

    # Now that uids are grouped by product type and source hub, go and get the actual details from both hubs
    delays_by_product_type = {}
    problems_by_product_type = defaultdict(dict)

    for source in uids_by_product_type:

        random_uids_by_product = {}

        for product in uids_by_product_type[source]:

            if verbose:
                print(f"Assessing delay for {source} {product}")

            # uids = uids_by_product_type[source][product]

            delays = {}

            if not sample_number:
                # use ALL products identified
                uids = uids_by_product_type[source][product]

            else:
                # use random selection based on sample number from the set of uid's identified
                uids = choose_random_uid(uids_by_product_type[source][product], sample_number)

            dcnt = 0
            # previous_selections = []

            for uid in uids:

                # get pub time on source hub
                try:
                    src_hub_domain, src_creation_date, src_ingestion_date = get_product_details(source_hub_config, uid)

                    loc_hub_domain, loc_creation_date, loc_ingestion_date  = get_product_details(local_hub_config, uid)

                    # todo need to make sure that the delays are properly indexed by source and prodduct and to make sure that the correct source config is picked up.
                    delays[uid] = get_delay(loc_creation_date, src_creation_date)

                    dcnt += 1

                except UIDnotOnHubError as ex:
                    # print (f"here {ex}")
                    # Product removed or not actually on hub anymore - record it in similar data structure
                    # if len(problems_by_product_type[source].keys()) == 0:
                    if product not in problems_by_product_type[source].keys():
                        problems_by_product_type[source].update({product: [uid]})

                    else:
                        problems_by_product_type[source][product].append(uid)

                except Exception as ex:
                    # todo: how to report/catch this?
                    print(f"here normal excp {ex}")

            # print (f"count: {dcnt}")

            # sort the completed set of datetime samples for this source/product combination
            # https://stackoverflow.com/questions/20944483/python-3-sort-a-dict-by-its-values
            sorted_uids = {}
            for p in sorted(delays, key=delays.get):
                sorted_uids[p] = delays[p]

            random_uids_by_product[product] = sorted_uids

        delays_by_product_type[source] = random_uids_by_product

    print("\n")

    # output more detailed info if asked to.
    if line:
        for source in delays_by_product_type.keys():
            print(f"********** Report for source: {source} **********")

            for product in delays_by_product_type[source].keys():
                print(f"Report for data product: {product}")
                cnt = 1
                if sample_number:
                    print(f"(Sampling {sample_number} of {len(uids_by_product_type[source][product])})")

                for sorted_dt_uid in delays_by_product_type[source][product].keys():
                    days, hrs, mins, secs = analyse_delay(delays_by_product_type[source][product][sorted_dt_uid])
                    report_line(sorted_dt_uid, src_hub_domain, loc_hub_domain, days, hrs, mins, secs, linenum=cnt)
                    cnt += 1
                print("\n")

            # print ("\n")

    # average needs to be based on the sampled set - whether full or a random selection

    # average per product....
    for source in delays_by_product_type.keys():
        if verbose:
            print(f"********** Publication delay for source: {source} **********")

        for product in delays_by_product_type[source].keys():
            if verbose:
                print(f"Product {product}")
            if len(delays_by_product_type[source][product]) != 0:
                avg_hrs, avg_mins = average_delay_hours([delays_by_product_type[source][product][i] for i in
                                                         delays_by_product_type[source][product].keys()])

                if verbose:
                    print(f"Average publication delay: {avg_hrs} hrs {avg_mins} mins for\
                     {len(delays_by_product_type[source][product])} records from  source: {source} to: {loc_hub_domain}")

                # any errors?
                try:
                    if verbose:
                        if len(problems_by_product_type[product][source]) != 0:
                            print(
                                f"Found {len(problems_by_product_type[product][source])} problems for {source}/{product}.  (Likely removed from source hub)")
                except:
                    # only have these keys etc if errors actually reported on..
                    pass

            else:
                if verbose:
                    print(f"Could not calculate publication delay as no products found!")
            if verbose:
                print("\n")

    # average per source....
    if verbose:
        print(f"********** Publication delay report BY source **********")

    delays_by_source = {}

    for source in delays_by_product_type.keys():

        filtered_uids_by_source = {}

        for uid in [j for j in [delays_by_product_type[source][i] for i in delays_by_product_type[source]]]:
            # filtered_uids_by_source.extend(uid.keys())
            # merge dicts - see https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression-taking-union-of-dictiona
            filtered_uids_by_source = {**filtered_uids_by_source, **uid}

        if len(filtered_uids_by_source.keys()) != 0:
            avg_hrs, avg_mins = average_delay_hours([i for i in filtered_uids_by_source.values()])

            # print(f"Average publication delay: {avg_hrs} hrs {avg_mins} mins for\
            # {len(filtered_uids_by_source.keys())} records from  source: {source} to: {loc_hub_domain}")

            if report_format:
                delays_by_source[source] = (f"{str(avg_hrs).zfill(2)}:{str(avg_mins).zfill(2)}")
                # print (f"{log_date},{str(avg_hrs).zfill(2)}:{str(avg_mins).zfill(2)}")

            else:
                print(
                    f"Date: {log_date} Source: {source} to: {loc_hub_domain}: {str(avg_hrs).zfill(2)}:{str(avg_mins).zfill(2)} (HH:MM)")

        else:
            if report_format:
                delays_by_source[source] = (f"None")

            else:
                print(
                    f"Date: {log_date} Source: {source}: No data available (not on source hub")

    return delays_by_source

def merge_two_dicts(x, y): #https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression
    z = x.copy()   # start with x's keys and values
    #z.update(y)    # modifies z with y's keys and values & returns None

    #updates to work better with how this code works with lists as dict values
    for k,v in list(y.items()):

        if k not in z:
            z[k] = v

        else:
            #deal with merge depending on what's in the value
            if type(v) is list:
                z[k] = sorted(list(set(v).union(set(z[k]))))

            elif type(v) is str:
                #just add it in
                z[k] = v

    return z


#todo: how does average delay change based on increasing sample size?  What sample size gives a reasonable idea of actual delay?
'''
TODO: how does a
'''

#see https://click.palletsprojects.com/en/7.x/options/  !!
@click.command()
@click.option('-c', '--local-hub-config', 'local_hub_config', type=str, required=True, help='Location of LOCAL hub admin credos')
@click.option('-s', '--source-hub-config', 'source_hub_config', type=str,  help='Location of SOURCE hub admin credenntials FILE', \
              cls=MutuallyExclusiveOption, mutually_exclusive=["source_hub_config_dir"])
@click.option('-S', '--source-hub-configs-dir', 'source_hub_config_dir', type=str,  help='DIRECTORY with all SOURCE hub admin credentials', \
              cls=MutuallyExclusiveOption, mutually_exclusive=["source_hub_config"])
@click.option('-U', '--specific-uid', 'specific_uid', type=str,  help='Specific uid to identify from log')
@click.option('-i', '--id', 'id', type=str, help='Single UID to submit to hub to extract publication delay info on', cls=MutuallyExclusiveOption, mutually_exclusive=["hub_log_file"])
@click.option('-n', '--sample-number', 'sample_number', type=int, help='Just sample N UIDs rather than retrieve info on ALL in log  Use TODO.py to work out number')
@click.option('-l', '--log-file', 'hub_log_file', type=str, help='DHuS logfile to extract successful sychronised UIDS from to assess latency', \
              cls=MutuallyExclusiveOption, mutually_exclusive=["id", "source_hub_config"])
@click.option('-D', '--log-file-dir', 'hub_log_dir', type=str, help='DHuS logfile directory for bulk reports', \
              cls=MutuallyExclusiveOption, mutually_exclusive=["id", "source_hub_config", "hub_log_file"])
@click.option('--line', is_flag=True, help="Will print out in ASCENDING ingestion time order the list of uid's and associated publication delay")
@click.option('-v', '--verbose', 'verbose', is_flag=True, help='Print extra output')
@click.option('-R', '--reporting-format', 'report_format', is_flag=True, help='ONLY Output a set of csv formatted lines for use with wrapper scripts to generate bulk info for reporting')
def main(local_hub_config, source_hub_config, source_hub_config_dir, hub_log_file, line, id, verbose, sample_number, report_format, hub_log_dir, specific_uid):

    tstamp=datetime.datetime.now().strftime("%d-%m-%yT%H:%M:%S")

    if verbose:
        print (f"\n\nReport timestamp: {tstamp}\n\n")

    if hub_log_file:
        log_files = [hub_log_file]

    elif  hub_log_dir:
        #todo make sure this is an exclusive option.
        if not report_format:
            print ("please only use this in report format mode")
        log_files = find_log_files(hub_log_dir, '.log')

    elif id:
        #todo: Test that ID option still works
        # for consistency with primary -from-log method.
        hub, u, pwd = get_hub_creds(source_hub_config)
        source_key = hub.replace('https://', '').replace('http://', '').split('/')[0]
        source_configs = {source_key: source_hub_config}

        # todo: update so consistent data structure sourced from definition in extract_detail_info
        # should be consistent with data structure in extract_detail_info.get_successful_downloads)
        successful_syncs = {source_key: {'uids': {id: None}}}

    else:
        raise Exception ("Please choose either log file or log file dir options")

    #get it to loop through logs of -D option.
    final_report = {}
    for hub_log_file in log_files:

        with open(hub_log_file) as r:
            lines = [i.rstrip() for i in r.readlines()]

        #get date from logfile.  As this tool should be used on logs covering only 1 day (as per dhus convention/ceda config) check that this is so...
        if get_date_from_logline(lines[0]) != get_date_from_logline(lines[-1]):
            raise Exception ("Log appears to cover more than one day!  Please supply logs of 1 per day as per convention")

        else:
            log_date = get_date_from_logline(lines[0])

        # get successful synchroniser structure
        successful_syncs, bad_cnt = get_successful_downloads(lines)

        #test = [i for i in successful_syncs['colhub.copernicus.eu']['uids'].keys()][0:9]
        source_configs = build_config_map(source_hub_config_dir, successful_syncs)

        #generate report
        delays_by_source = generate_report(source_configs, local_hub_config, verbose, successful_syncs, sample_number, report_format, line, log_date, specific_uid)

        #final_report = merge_two_dicts(final_report, delays_by_source)
        final_report[log_date] = delays_by_source

    #work out unique columns (producrs
    '''
    columns = []
    for h in [[j for j in final_report[i].keys()] for i in final_report.keys()]:
        columns += h

    columns = list(set(columns))
    columns_str = str([i for i in columns]).replace('[', '').replace(']', '').replace("'", "")

    print(f"date, {columns_str}")

    for date in final_report.keys():
        times = str([final_report[date][i] for i in final_report[date].keys()]).replace('[', '').replace(']', '').replace("'", "")
        print(f"{date}, {times}")
    '''

if __name__ == '__main__':
    main()

