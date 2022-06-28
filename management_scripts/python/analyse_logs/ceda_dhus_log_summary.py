from operator import eq

__author__ = 'sjdd53'
import sys, os, re

sys.path.append("..")

from datetime import datetime
from copy import deepcopy
from optparse import OptionParser, OptionGroup

#from analyse_logs.Sentinel import Sentinel_Product
#from .Sentinel import Sentinel_Product
from Sentinel import Sentinel_Product

#from extract_detail_info import get_successful_downloads

class Line_Error(Exception):
    pass

SYNC_ENTRY_LINE_TEMPLATE = {'entry_time':None, 'log_level':None, 'synchronizer_id':None, 'product':None, 'size':None, 'status':None, \
                            'source':None, 'product_type':None, 'product_sens_time':None, 'transfer_rate':None}

SYNC_SUCCESS_TEXT_SNIPPET = 'successfully synchronized from'

SYNC_FAIL_TEXT_SNIPPET = 'failed to download'

DOWNLOAD_ENTRY_LINE_TEMPLATE = {'entry_time':None, 'user_id':None, 'product':None, 'size':None, 'download_time':None, 'transfer_rate':None }

EVICT_ENTRY_LINE_TEMPLATE = {'entry_time':None, 'log_level':None, 'product':None, 'size':None,'size_compressed':None, 'product_type':None}


#Sample SUCCESSFUL log line for a synchronizer
# [0.10.3-4][2016-09-21 11:22:54,935][INFO ] Synchronizer#7 Product S2A_OPER_PRD_MSIL1C_PDMC_20160904T230042_R136_V20160904T093032_20160904T094122 (5781473778 bytes compressed) \
# successfully synchronized from https://colhub.esa.int/dhus/odata/v1 (ODataProductSynchronizer.java:694 - SyncExecutor)


def find_log_files(logfiledir, extension):

    logs = []

    if not os.path.isdir(logfiledir):
        raise Exception (f"Not a directory: {logfiledir}")

    for (logfilepath, logfiledir, logfilename) in os.walk(logfiledir):
        for filename in logfilename:

            full_filename = os.path.join(logfilepath, filename)

            if os.path.splitext(full_filename)[-1] == extension:
                logs.append(full_filename)

    return logs

def set_options(parser):
    '''
    Method to properly parse args in the linux style
    :param parser:
    :return: options & args
    '''
    dhuslog = OptionGroup(parser, "CEDA Sentinel Data Hub Log Analyser", "Use these options to extract useful information from DHUS logfiles " )

    dhuslog.add_option('-l', '--logfile', dest='logfilename', type='str',action='store', help='Identify single log file')
    dhuslog.add_option('-o', '--output-csv', dest='outputfiledir', type='str',action='store', help='Write report output to csv file')
    dhuslog.add_option('-P', '--output-products', dest='output_product_list', type='str',action='store', help='Create list of products SYNCHRONISED in log')
    dhuslog.add_option('-E', '--evicted-products', dest='evicted_product_list', type='str',action='store', help='Create list of products EVICTED in log')
    dhuslog.add_option('-d', '--directory', dest='logfiledir', type='str',action='store', help='Directory where log file resides')
    dhuslog.add_option('-x', '--extension', dest='extension', type='str',action='store', help='logfile extension.  Will try and analyse all files with this extension (include the ".")')
    #dhuslog.add_option('-s', '--start-date', dest='start_date', type='str', action='store', help='Start date from which to analyse. Format= YYYY-MM-DDThh:mm:ss')
    #dhuslog.add_option('-e', '--end-date', dest='end_date', type='str', action='store', help='End date which to analyse to. Format= YYYY-MM-DDThh:mm:ss')

    parser.add_option_group(dhuslog)

    (options,args) = parser.parse_args()

    return (options,args)


#Method to check options
def check_options(options):
    '''
    Method to check selected options.  If any bad will stop script with message
    :param options:
    :return:
    '''
    if options.logfilename is None and options.logfiledir is None:
        print ("\nError: Please supply either an explicit logfile (-l option) or the directory where logfiles are to be found (-d option)")
        parser.print_help()
        sys.exit()

    if options.logfiledir is not None and options.extension is None:
        print ("\nError: If using a directory with logfiles please supply the extension (-x option)")
        parser.print_help()
        sys.exit()


def filter_resultset(extracted_details,  keyname, equivalent, unique=False, cross_keyname=None, cross_equivalent = None):
    '''
    Method to apply list comprehension to summarise info scraped from log and held in list of dictionaries.  If equivalent supplied will return only values of
    dict keyname with that value.  If cross_keyname and cross_equivalent are supplied then will provide an intersection set where all values are met.
    :rtype : List
    :param extracted_details: list of dictionaries returned from repeated calls to extract_synchronizer_details
    :param keyname: key which will be summarised
    :param unique: return a list woth only unique values in
    :param equivalent: value to be compared against
    :param cross_keyname: second key which will be checked
    :param cross_equivalent: value to be compared against second key
    :return: resulting list of dictionary items from the comprehension satisfying the supplied conditions
    '''

    results = None

    #check values
    if (equivalent is None and keyname is not None) or (equivalent is not None and keyname is None):
        raise Exception ("Please supply both a keyname and the value for its equivalent")

    if (cross_equivalent is None and cross_keyname is not None) or (cross_equivalent is not None and cross_keyname is None):
        raise Exception ("Both intersect values must be provided (only one found!")

    #first instance, performing an intersection...
    if cross_keyname is not None and cross_equivalent is not None:

        try:
            results = [x for x in extracted_details if x[keyname] == equivalent and x[cross_keyname] == cross_equivalent]

        except Exception as ex:
            raise Exception ("ERROR: unable to extract information for key: %s (%s)" %(keyname, ex))

    #not performing an intersection
    else:
        try:
            results = [x for x in extracted_details if x[keyname] == equivalent]

        except Exception as ex:
            raise Exception ("ERROR: unable to extract information for key: %s (%s)" %(keyname, ex))

    if results is None:
        raise Exception ("ERROR: Unable to return a list of items")

    else:
        return results


def summarise(extracted_details, keyname, unique = False, equivalent = None):
    '''
    summarise a filtered list of dicts on the provided key
    :param extracted_details: list of dictionaries.
    :param keyname: key which will be summarised
    :param unique: return a list with only unique values in
    :param equivalent: value to be compared against.  If not supplied all values of keyname will be returned

    '''

    try:
        if equivalent is not None:
            results = [x[keyname] for x in extracted_details if x[keyname] == equivalent]

        else:
            results = [x[keyname] for x in extracted_details]

    except Exception as ex:
        raise Exception ("ERROR: unable to extract information for key: %s (%s)" %(keyname, ex))

    if unique:
        return list(set(results))

    else:
        return results


def convert_byte_nums(bytes, dp=None):
    '''
    Method to simply convert bytes to Gb or Tb
    :param bytes: byte  value to convert
    :param dp: decimal points to round to - default is 2
    :return: gb,tb
    '''

    if dp is None:
        dp = 2

    try:
        gb = bytes / (1024 ** 3)
        tb = bytes / (1024 ** 4)

        return round(gb,dp), round(tb,dp)

    except Exception as ex:
        raise Exception ("Unable to convert %s to gb & tb! (%s)" %(bytes, ex))


def extract_synchronizer_details(line, start_date= None, end_date=None ):
    '''
    Method to extract information from a log line identified as containing synchroniser text.
    :param line: line extracted from log file
    :param start_date: only consider lines with datestamp after this
    :param end_date: only consider lines with datestamp before this
    :return:
    '''

    linesplt = line.split()

    entry = deepcopy(SYNC_ENTRY_LINE_TEMPLATE)

    #strip out the log entry datetime
    try:
        entry_time_str = linesplt[0].split('][')[-1] + 'T' + linesplt[1].split('][')[0]

        entry['entry_time'] = datetime.strptime( entry_time_str, "%Y-%m-%dT%H:%M:%S,%f")

    except Exception as ex:
        raise Exception("ERROR: cannot parse entry time (%s)" %ex)

    #successful synchronisation - how we parse the line depends on whether successful or not

    if SYNC_SUCCESS_TEXT_SNIPPET in line:

        entry['status'] = True
        entry['source'] = line.split(SYNC_SUCCESS_TEXT_SNIPPET)[1].split()[0]

        try:
            entry['log_level'] = linesplt[1].split('][')[1]
            entry['synchronizer_id'] = linesplt[3].split('#')[-1]
            entry['size'] = linesplt[6].replace('(','').replace(')','')

        except Exception as ex:
            raise Exception("ERROR: cannot parse log line (%s)" %ex)

        try:
            sentinel_product = Sentinel_Product(linesplt[5])

            entry['product'] = sentinel_product.product_name
            entry['product_type'] = sentinel_product.product_type
            entry['product_sens_time'] = sentinel_product.get_product_date()

        except Exception as ex:
            raise Exception(ex)

    elif SYNC_FAIL_TEXT_SNIPPET in line:
        #note no "source" in this message..(cannot work it out from synchroniser id anyway)
        entry['status'] = False

        try:
            entry['log_level'] = linesplt[1].split('][')[1]
            #entry['synchronizer'] = linesplt[3].split('#')[-1]
            entry['synchronizer_id'] = linesplt[2].split('#')[-1] #updated 30/01/2017 SJD

        except Exception as ex:
            raise Exception("ERROR: cannot parse log line (%s)" %ex)

        try:
            sentinel_product = Sentinel_Product(linesplt[4])

            entry['product'] = sentinel_product.product_name
            entry['product_type'] = sentinel_product.product_type
            entry['product_sens_time'] = sentinel_product.get_product_date()

        except Exception as ex:
            raise Exception( "ERROR: Unable to convert product sensing date! (%s)" %ex)



    return entry


def extract_eviction_details(line, start_date= None, end_date=None ):
    '''
    Method to extract information from a log line identified as containing synchroniser text.
    :param line: line extracted from log file
    :param start_date: only consider lines with datestamp after this
    :param end_date: only consider lines with datestamp before this
    :return:
    '''

    linesplt = line.split()

    #[0.10.3-4][2016-10-13 21:06:24,672][INFO ] Evicted S1A_EW_GRDM_1SSH_20160824T210738_20160824T210838_012747_014110_A0BF (221154655 bytes                   , 143259210 bytes compressed) (EvictionManager.java:258 - doEvictionTread)
    entry = deepcopy(EVICT_ENTRY_LINE_TEMPLATE)

    entry_time_str = linesplt[0].split('][')[-1] + 'T' + linesplt[1].split('][')[0]

    try:
        entry['entry_time'] = datetime.strptime( entry_time_str, "%Y-%m-%dT%H:%M:%S,%f")

    except Exception as ex:
        raise Exception("ERROR: cannot parse entry time (%s)" %ex)

    try:
        entry['log_level'] = linesplt[1].split('][')[1]
        #entry['product'] = linesplt[4]
        entry['size'] = linesplt[5].replace('(','')
        entry['size_compressed'] = linesplt[7]

    except Exception as ex:
        raise Exception("ERROR: cannot parse log line (%s)" %ex)

    try:
        sentinel_product = Sentinel_Product(linesplt[4])

        entry['product'] = sentinel_product.product_name
        entry['product_type'] = sentinel_product.product_type
        entry['product_sens_time'] = sentinel_product.get_product_date()

    except Exception as ex:
        raise Exception( "ERROR: Unable to convert product sensing date! (%s)" %ex)

    return entry


def logfile(logfilename):
    '''
    Method to wrap opening a log file and return the content

    :param logfilename: full name and path of logfile
    :return list of lines within logfile:
    '''

    log = None

    try:
        logfileob = open(logfilename,'r')

    except Exception as ex:
        print ("ERROR: Could not open file %s" %ex)
        sys.exit()

    try:
        log = logfileob.readlines()

    except Exception as ex:
        raise Exception("ERROR: Could not extract log lines %s" %ex)

    logfileob.close()

    if log is not None:
        return log

    else:
        raise Exception ("Encountered problem opening log file: Nothing extracted")


def analyse_evicted_products(evicted_products):
    '''
    Method to analyse evicted products on a per product_type basis

    :param evicted_products: list of dictionaries to be analysed pulled from the log
    :return:
    '''

    #identify how much downloaded per synchroniser - SUCCESSFUL

    #products
    products_evict = summarise(evicted_products,'product_type',unique=True)

    evicted_products_summary = {}

    for prod in products_evict:

        #summarise per product
        per_prod_summary = {}

        source = None

        #make sure there are products to summarise
        products = filter_resultset(evicted_products, 'product_type', prod)

        if len(products) > 0:

            sizes = summarise(products,'size')

            #get total volume
            tot_size=0.
            for size in sizes:
                tot_size +=float(size)

            #tot_size = tot_size/(1024*1024*1024) # bytes converted to GB
            tot_size/=(1024*1024*1024) # bytes converted to GB

            per_prod_summary['tot_size'] = tot_size

            #number of files for this product
            per_prod_summary['num'] = len(sizes) #will equate to number of files for this product type

            times = summarise(products,'entry_time')

            sens_times = summarise(products,'product_sens_time')

            per_prod_summary['start'] = min(times).strftime("%Y-%m-%d %H:%M")
            per_prod_summary['end'] = max(times).strftime("%Y-%m-%d %H:%M")

            per_prod_summary['sens_start'] = min(sens_times).strftime("%Y-%m-%d %H:%M")
            per_prod_summary['sens_end'] = max(sens_times).strftime("%Y-%m-%d %H:%M")


        #add to the per product level
        evicted_products_summary[prod] = deepcopy(per_prod_summary)

    return evicted_products_summary


def analyse_synchronizer(subset, synchronizers_used, status =None):
    '''
    Method to analyse reports from synchronizers

    :param subset: list of dictionaries to be analysed pulled from the log
    :param synchronizers_used: synchronizer ids
    :param status: 'success' = will pull more info out 'fail', onnlu info "lite"
    :return:
    '''

    more_info = None

    if status == 'success':
        more_info = True

    elif status == 'fail':
        more_info = False

    else:
        raise Exception ("ERROR: Please supply either 'success' or 'fail' for scan status!")


    #identify how much downloaded per synchroniser - SUCCESSFUL
    per_sync = {}
    for synchronizer in synchronizers_used:

        sync = {}

        sync_results = filter_resultset(subset, 'synchronizer_id', synchronizer)

        #products
        products_sync = summarise(sync_results,'product_type',unique=True)

        #summarise per product
        per_prod_summary = {}
        for prod in products_sync:

            source = None

            #make sure there are products to summarise
            products = filter_resultset(sync_results, 'product_type', prod)

            #check source (& that they are not getting mixed up)
            try:
                source = summarise(sync_results,'source',unique=True)

            except:
                #problem - no source in error downloads
                source = None

            source_sync = ''
            if source is not None and len(source) > 1:

                cnt=0

                for sourcen in source:
                    if cnt == 0:
                        source_sync ='[%s]: %s' %(cnt+1,sourcen)
                    else:
                        source_sync = '%s\t [%s]: %s' %(source_sync,cnt+1,sourcen)
                    cnt+=1
            else:
                source_sync = source[0]


                #raise Exception ("WARNING: More than one synchronisation source detected for synchronizer %s!" %synchronizer)

            if len(products) > 0:

                if more_info:

                    sizes = summarise(products,'size')

                    #failed reports will not have size in there
                    if sizes[0]:

                        #get total volume
                        tot_size=0.
                        for size in sizes:
                            tot_size +=float(size)

                        tot_size = tot_size/(1024*1024*1024) # bytes converted to GB

                        per_prod_summary['tot_size'] = tot_size

                    else:
                         per_prod_summary['tot_size'] = 0

                #number of files for this product
                per_prod_summary['num'] = len(sizes) #will equate to number of files for this product type

                if more_info:
                    times = summarise(products,'entry_time')

                    sens_times = summarise(products,'product_sens_time')

                    per_prod_summary['start'] = min(times).strftime("%Y-%m-%d %H:%M")
                    per_prod_summary['end'] = max(times).strftime("%Y-%m-%d %H:%M")

                    per_prod_summary['sens_start'] = min(sens_times).strftime("%Y-%m-%d %H:%M")
                    per_prod_summary['sens_end'] = max(sens_times).strftime("%Y-%m-%d %H:%M")

                if source:
                    per_prod_summary['source'] = source_sync

                else:
                    per_prod_summary['source'] = 'N/A'

            #add to the per product level
            sync[prod] = deepcopy(per_prod_summary)

        #add to the per-synchroniser report level
        per_sync[synchronizer] = deepcopy(sync)

    return per_sync


def log_filter(logfile, filters, butnot=None):
    '''
    Method to extract lines of log files that match all filters supplied in *filters
    :param log: logfile as a list (extracted using readlines)
    :param filters: list of filters to find in logfile
    :param butnot: list of text strings that if present will cause match to fail
    :return: list of lines extracted based on the filter
    '''

    pre_filtered_text = filtered_text = []

    #summarise log info we're looking for into separate lists
    for line in logfile:

        match = True

        #find lines containing the text we want first...
        for filter in filters:
            if filter not in line:
                match = False

        if match:
            pre_filtered_text.append(deepcopy(line))

    if butnot:
        #NOW check if any NOT text is present, in which case ignore
        filtered_text = deepcopy(pre_filtered_text)

        for line in pre_filtered_text:
            for notfilter in butnot:
                if notfilter in line:
                    filtered_text.remove(line)

        return filtered_text

    else:
        return pre_filtered_text


def download_report_success(logfiles):
    '''
    Wrap download report for failed downloads by user
    :param logfiles:
    :return:
    '''
    filter_list= ["download by user","completed"]

    title  ="\n************************ User Download Overview: SUCCESSFUL downloads ****************************\n"

    report = download_report(logfiles, filter_list, title)

    return report

def download_report_fail(logfiles):
    '''
        Wrap download report for successful downloads by user
        :param logfiles:
        :return:
        '''
    filter_list = ["download by user", "failed"]

    title = "\n************************ User Download Overview: FAILED downloads ****************************\n"

    report = download_report(logfiles, filter_list, title)

    return report

def download_report(logfiles, filter_list, title):
    '''
    Method to generate overview report on number of downloads per user in log files

    :param logfiles:
    :return: report
    '''

    report = ''

    downloads = []

    for logfilename in logfiles:

        try:
            log = logfile(logfilename)

        except Exception as ex:
            raise Exception("ERROR: Unable to open logile: %s (%s)" %(logfilename, ex))

        try:
            filtered_log = log_filter(log, filter_list) # this is the hook we're looking for.

        except Exception as ex:
            raise Exception( "ERROR: Unable to open logfile: %s (%s)" %(logfilename, ex))

        cnt =0
        for line in filtered_log:

             #successful downloads..
            try:

                extracted_details = download_report_details(line)

                if extracted_details is not None:
                    downloads.append(deepcopy(extracted_details))

            except Exception as ex:
                print ( f"WARNING: Unable to summarise download activity from log (line {cnt}: {logfilename} {ex}" )
                pass
                #raise Exception( "ERROR: Unable to summarise download activity from log: %s (%s)" %(logfilename, ex))
            cnt+=1
    #identify unique users
    try:
        download_users = summarise(downloads,'user', unique=True)

    except Exception as ex:
        raise Exception("ERROR: Could not extract unique synchronizers: %s"%ex)

    overview_by_user = {}

    #calculate total download times
    try:

        download_times = summarise(downloads,'download_time')

    except Exception as ex:
        raise Exception("ERROR: Could not extract unique synchronizers: %s"%ex)

    try:
        for user in download_users:
            overview_by_user[user] = filter_resultset(downloads,'user',user)

    except Exception as ex:
        raise Exception( "ERROR: Unable to summarise download activity from log: %s (%s)" %(logfilename, ex))

    #calculate total volume of data synchronised
    download_volume = {}
    download_products = {}
    download_products_volume = {}
    download_products_numbers = {}
    download_times = {}
    download_rates = {}

    for user in overview_by_user.keys():

        user_total = 0.

        download_products_volume_user = {}
        download_products_numbers_user = {}

        # 10/10/17 - summarise volume by types
        product_types_downloaded = summarise(overview_by_user[user],'product_type',unique=True)

        for product_type in product_types_downloaded:

            #need to get summary per USER and per product type

            per_product_type = filter_resultset(overview_by_user[user],'product_type',product_type)

            #summarise(overview_by_user[user],'product_type',unique=True)
            per_product_volume = 0
            prod_cnt =0

            for product in per_product_type:
            #print product['size']
                #calculate gross and individual product size - only for successful downloads (ignore fails)
                if product['size'] is not None:
                    per_product_volume += float(product['size'])
                    user_total += float(product['size'])
                prod_cnt += 1

            download_products_volume_user[product_type] = per_product_volume
            download_products_numbers_user[product_type] = prod_cnt

            # calculate absolute total from summary of products
            #for prod in download_products_volume_user.keys():
                #user_total += download_products_volume_user[prod]

        #assign at user level
        download_volume[user] = user_total
        download_products_volume[user] = download_products_volume_user
        download_products_numbers[user] = download_products_numbers_user

        #by products
        try:
            download_products[user]  = summarise(overview_by_user[user],'product')

            times  = summarise(overview_by_user[user],'download_time')

            #whats the total in seconds?
            tot_time = 0.
            for time in times:
                tot_time += float(time)

            if tot_time != 0:
                download_times[user] = tot_time/1000.

        except Exception as ex:
            raise Exception( "ERROR: Unable to summarise download activity from log: %s (%s)" %(logfilename, ex))

        #calculate transfer rates
        try:
            transfer_rates = summarise(overview_by_user[user],'transfer_rate')

            download_rates[user] = {'max':max(transfer_rates), 'min':min(transfer_rates), 'mean':sum(transfer_rates)/len(transfer_rates)}

        except Exception as ex:
            raise Exception( "ERROR: Unable to summarise transfer rates from log: %s (%s)" %(logfilename, ex))


    report += title

    total_download_secs = 0
    for user in download_volume.keys():

        total_download_secs += download_times[user]

        #volume calculation
        #gb = download_volume[user]/(1024**3)
        #tb = download_volume[user]/(1024**4)

        gb,tb = convert_byte_nums(download_volume[user])

        report += "User: %s\tProducts: %s\tVolume: %.2f(Gb)\t(%.4f Tb)\tTot duration (s): %s (%.2f hrs)\tTransfer rates (max/min/mean) : %.2f/%.2f/%.2f MBps\t\n" \
                  %(user,len(download_products[user]),gb,tb, download_times[user], download_times[user]/3600, \
                    download_rates[user]['max'],download_rates[user]['min'],download_rates[user]['mean']) #same key used in download products


    #summarise downloads by users
    report += "\nUser\t\t\tProduct\t\tNumber\tVolume (gb/tb)\n"

    for user in download_products_volume.keys():

        #now loop over on a per product basis
        for product in download_products_volume[user].keys(): #note keys are the same for both these dicts

            gb, tb = convert_byte_nums(download_products_volume[user][product])

            report += "%s\t\t%s\t%s\t\t%s/%s\n" %(user,product,download_products_numbers[user][product], \
                                                  gb,tb)

    report += "\nTotal number of users active: %s" %len(download_volume.keys())
    report +=f"\nTotal number of products: {sum([len(download_products[i]) for i in download_products.keys()])}"
    report += "\nTotal download duration (s): %s (%.2f hrs)\n\n" %(total_download_secs,total_download_secs/3600)

    return report


def download_report_details(line):
    '''
    Method to extract information about downloaded data

    :return:
    '''

    linesplt = line.split()

    entry = deepcopy(SYNC_ENTRY_LINE_TEMPLATE)

    #need to remember if this is a successful or failed download
    failed_entry = False

    try:
        entry_time_str = linesplt[0].split('][')[-1] + 'T' + linesplt[1].split('][')[0]

        entry['entry_time'] = datetime.strptime( entry_time_str, "%Y-%m-%dT%H:%M:%S,%f")

    except Exception as ex:
        raise Exception("ERROR: cannot parse entry time (%s)" %ex)

    try:
        entry['user'] = line.split("download by user")[1].split(" ")[1].replace("'","").replace('"','')

    except Exception as ex:
        raise Exception("ERROR: cannot parse USER details (%s)" %ex)

    try:
        sentinel_product = Sentinel_Product(linesplt[5].replace("(","").replace(")",""))

        entry['product'] = sentinel_product.product_name
        entry['product_type'] = sentinel_product.product_type
        entry['product_sens_time'] = sentinel_product.get_product_date()

    except Exception as ex:
        raise Exception( "ERROR: Unable to convert product sensing date! (%s)" %ex)

    #check we're getting a number for the size - failed downloads have different structure to successful so need to work out which is which here
    try:

        if "failed at" in line:
            failed_entry = True

            val = line.split("failed at")[1].split(" ")[1].split("/")[1]
        else:
             val = line.split("download by user")[1].split(" ")[6]

        #had line been mangled by the dhus i.e. with new line starting in the parsed value -
        #i.e. 2.7.8-osf][2021-11-15 02:07:44,195][INFO ] Product '6ab93dfb-562c-4b6e-a7d3-e7df6d03fb3a' (S1A_IW_SLC__1SDV_20211105T022118_20211105T022145_040430_04CB0D_9C67)
        # download by user 'collaborative_uk_ops' failed at 708050944/448684538[2.7.8-osf][2021-11-15 02:07:47,257][INFO ] Product '0fc4...

        if not re.search('\[', val):
            entry['size'] = float(val)

        else:
            raise Line_Error("Likely mangled logline")

    except Line_Error as ex:
        print (f"Warning: {ex}")

    except Exception as ex:
        raise Exception ("ERROR: Cannot convert size to number! (%s)" %ex)

    if not failed_entry:
        try:
            entry['download_time'] = line.split("download by user")[1].split(" ")[4].replace('ms', '')

        except Exception as ex:
            raise Exception("ERROR: cannot parse DOWNLOAD_TIME details (%s)" % ex)

        #calculate download speed (MBs)
        try:
            entry['transfer_rate'] = calculate_transfer_rate(entry['size'],entry['download_time'])

        except Exception as ex:
            raise Exception ("ERROR: %s" %ex)

    else:
        entry['download_time'] = 1
        entry['transfer_rate'] = 1

    return entry


def calculate_transfer_rate(data_size_bytes, download_duration_ms):
    '''
    Method to calculate data transfer rate in MBs (megabytes per second).
    :return: transfer rate in MBs
    '''

    try:
        product_volume_mb = float(data_size_bytes)/1024/1024
        download_in_secs = float(download_duration_ms)/1000

        return round(product_volume_mb/download_in_secs,2)

    except Exception as ex:
        raise Exception ("Cannot calculate transfer rate! (%s)" %ex)


def summarise_downloads_per_product_per_sync(per_sync,per_sync_fail):
    '''
    Method to summarise good and bad products returned
    :return:
    '''

    total_good_per_sync = {}
    total_bad_per_sync = {}

    good_and_bad = {}
    for sync in sorted(per_sync.keys()):
        good_and_bad_sync = {}

        sync_good = 0
        sync_bad = 0

        for product in per_sync[sync].keys():
            good_num = per_sync[sync][product]['num']

            if product in per_sync_fail[sync]:
                bad_num = per_sync_fail[sync][product]['num']

            else:
                bad_num = 0

            good_and_bad_sync[product] = '%s/%s' %(good_num,bad_num)

            sync_good += int(good_num)
            sync_bad += int(bad_num)

        total_good_per_sync[sync] = sync_good
        total_bad_per_sync[sync] = sync_bad

        #any products in bad downloads not in successful downloads?
        bad_prod_keys = list(set(per_sync_fail[sync].keys()) - set(per_sync[sync].keys()) )

        if len(bad_prod_keys) > 0:
            for bad_prod in bad_prod_keys:
                good_num = 0
                bad_num = per_sync_fail[sync][bad_prod]['num']

                good_and_bad_sync[bad_prod] = '%s/%s' %(good_num,bad_num)

            total_bad_per_sync[sync] += int(bad_num)

        good_and_bad[sync] = good_and_bad_sync

    return good_and_bad, total_good_per_sync, total_bad_per_sync


def synchronizer_report(logfiles, write_products = None):
    '''
    Method to handle extraction of synchronizer activity in the given logfile and summarise it.
    :param logfiles: list of logfiles to analyse
    :return:
    '''

    #extract syncinfo
    successful_sync = []
    products_downloaded = None
    #cnt = 0

    #work our way through all logfiles identified.
    for logfilename in logfiles:

        try:
            log = logfile(logfilename)

        except Exception as ex:
            raise Exception("ERROR: Unable to open logile: %s (%s)" %(logfilename, ex))

        try:
            filtered_log = log_filter(log, ["Synchronizer#"])

        except Exception as ex:
            raise Exception( "ERROR: Unable to open logfile: %s (%s)" %(logfilename, ex))

        #now run the filtered log file and extract details as required
        bad_line_count = 0
        line_count = 0
        errors = {}
        for line in filtered_log:

            #successful dhus..
            try:
                extracted_details = extract_synchronizer_details(line)

                if extracted_details is not None:
                    successful_sync.append(deepcopy(extracted_details))

            except Exception as ex:
                bad_line_count +=1
                errors[line_count] = ex
                #raise Exception( "ERROR: Unable to summarise synchroniser activity from log line %s: %s (%s)" %(line_count-1,logfilename, ex))

            line_count += 1
            #something added to test new git pat...S
        if bad_line_count > 0:
            print ("WARNING!  Found %s bad lines in log %s.  Possible Java system errors in log.  Please investigate!" %(bad_line_count, logfilename))
            for error in errors.keys():
                print ("Line %s: %s" %(error, errors[error]))

    #report on values
    try:
        success = filter_resultset(successful_sync,'status',True)
        fail = filter_resultset(successful_sync,'status',False)

    except Exception as ex:
        print ("ERROR: problem: %s "%ex)

    #identify unique synchronizers
    try:
        synchronizers_used = summarise(success,'synchronizer_id', unique=True)

    except Exception as ex:
        raise Exception("ERROR: Could not extract unique synchronizers: %s"%ex)

    #success summary for all log files submitted
    try:
        per_sync = analyse_synchronizer(success, synchronizers_used, status ='success')

    except Exception as ex:
        raise Exception ("ERROR: Unable to extract information from sync log (%s)" %ex)

    #failure summary for all log files submitted
    try:
        per_sync_fail = analyse_synchronizer(fail, synchronizers_used, status ='success')

    except Exception as  ex:
        raise Exception ("ERROR: Unable to extract information from sync log (%s)" %ex)

    sync_volume = {} #calculate total volume of data synchronised
    sync_prods = {} #calculate total number of products per synchroniser
    sync_url = {}

    for sync in per_sync.keys():
        sync_total = 0.
        sync_total_prods = 0.

        for product in per_sync[sync].keys():
            sync_total += float(per_sync[sync][product]['tot_size'])
            sync_total_prods += float(per_sync[sync][product]['num'])

            sync_url[sync] = per_sync[sync][product]['source']

        sync_volume[sync] = sync_total
        sync_prods[sync] = sync_total_prods

    if write_products is not None:
        products_downloaded = summarise(success,'product')

    #need to link success with failed (success/bad) - run through successful products and workout what if any are bad
    good_and_bad, total_good, total_bad = summarise_downloads_per_product_per_sync(per_sync,per_sync_fail)


    #now summarise success report
    report_line=''

    report_line += "\n*********************** Synchronizer Report ************************\n"

    report_line += "Report timestamp; %s\n\n" %datetime.now().strftime("%d-%m-%yT%H:%M:%S")

    report_line += "Total number of products attempted to be synchronised; %s\n" %(sum(total_good.values()) + sum(total_bad.values()))
    report_line += "Number of products successfully synchronised; %s\n" %sum(total_good.values()) #updated based on actual analysis of logs
    report_line += "Number of products that failed to synchronize; %s\n" %sum(total_bad.values()) # ''''''

    report_line += "Number of dhus active; %s\n" %(len(sync_volume.keys()))

    report_line +=  "\nSynchronizer\tProduct\tNum success/failed\tTot Size(Gb)\tTime Start\tTime End\tSens Date Start\tSens Date End\n"

    total_number_of_products = 0.


    for sync in sorted(per_sync.keys()):
        for product in per_sync[sync].keys():
            report_line +=  "%s\t%s\t%s\t%.4f\t%s\t%s\t%s\t%s\n" %(sync,product, good_and_bad[sync][product],per_sync[sync][product]['tot_size'], per_sync[sync][product]['start'], \
                per_sync[sync][product]['end'], per_sync[sync][product]['sens_start'], per_sync[sync][product]['sens_end'])

            total_number_of_products += int(per_sync[sync][product]['num'])

    report_line += "\n"

    total_downloaded_gb = 0.
    for sync in sorted(sync_volume.keys()):
        report_line +=  "Synchroniser '%s' total, %.2f Gb (%.4f Tb), %s/%s (success/fail downloaded), DHR: %s\n" \
                        %(sync,sync_volume[sync], sync_volume[sync]/1024, total_good[sync],total_bad[sync], sync_url[sync])

        total_downloaded_gb += sync_volume[sync]

    report_line += "\nTotal synchronized data volume: %.2f Gb (%.4f Tb) in %.0f products\n"%(total_downloaded_gb,total_downloaded_gb/1024,total_number_of_products)

    return report_line, products_downloaded

    '''
    print "\n************** Failed Synchronizer runs ******************* \n"
     #success
    try:
        per_sync = analyse_synchronizer(fail, synchronizers_used, status ='fail')

    except Exception as ex:
        raise Exception ("ERROR: Unable to extract information from sync log (%s)" %ex)

    print "Synchronizer\tProduct\tTot downloaded\tTot Size(Gb)\tTime Start\tTime End\tSource"
'''


def eviction_report(logfiles, write_products = None):
    '''
    Method to handle extraction of synchronizer activity in the given logfile and summarise it.
    :param logfiles: list of logfiles to analyse
    :return:
    '''

    evicted_products = []
    evicted_product_list = None
    #cnt = 0

    #work our way through all logfiles identified.
    for logfilename in logfiles:

        try:
            log = logfile(logfilename)

        except Exception as ex:
            raise Exception("ERROR: Unable to open logile: %s (%s)" %(logfilename, ex))

        try:
            filtered_log = log_filter(log, ["Evicted"], butnot=['No product'])

        except Exception as ex:
            raise Exception( "ERROR: Unable to open logfile: %s (%s)" %(logfilename, ex))

        #now run the filtered log file and extract details as required
        for line in filtered_log:

            #successful evictors..
            try:

                extracted_details = extract_eviction_details(line)

                if extracted_details is not None:
                    evicted_products.append(deepcopy(extracted_details))

            except Exception as ex:
                raise Exception( "ERROR: Unable to summarise synchroniser activity from log: %s (%s)" %(logfilename, ex))

    eviction_overview = analyse_evicted_products(evicted_products)

    #calculate total volume of data evicted
    evicted_total = 0.
    for product in eviction_overview.keys():
        evicted_total += float(eviction_overview[product]['tot_size'])

        #sync_url[sync] = per_sync[sync][product]['source']

    #sync_volume[sync] = sync_total

    #now summarise eviction report
    report_line = "\n*********************** Eviction Report ************************"

    #report_line +=  "\nSynchronizer\tProduct\tTot downloaded\tTot Size(Gb)\tTime Start\tTime End\tSens Date Start\tSens Date End\n"
    if len(eviction_overview.keys()) != 0:
        report_line += "\nProduct\tVolume evicted (Gb)\n"
        for product in eviction_overview.keys():
            report_line += '%s\t%.4f\n' %(product,eviction_overview[product]['tot_size'])

        #report_line += "\n"
        report_line += "\nTotal number of products evicted; %s" %len(evicted_products)
        report_line += "\nTotal evicted volume (Gb); %.f4  (%.4fTb) \n"%(evicted_total,evicted_total/1024)

    else:
        report_line += "\nNo products evicted in this reporting period!\n"

    #if required to, generate list of products evicted to a list object
    if write_products:
        evicted_product_list = summarise(evicted_products,'product')

    return report_line, evicted_product_list


def create_file(filename, content):
    '''
    Method to write a file.  Returns True if successful
    :return:
    '''

    try:
        outputfile = open(filename, "w")
        outputfile.writelines(content)
        outputfile.close()

    except Exception as ex:
        raise Exception ("ERROR: Unable to write file: %s (%s)" %(filename, ex))

    if os.path.exists(filename):
        return True

    else:
        return False


if __name__ == '__main__':

    #Handle args passed.  Best way is to use linux style notation to handle differing log options
    parser = OptionParser()

    options,args = set_options(parser)

    check_options(options)

    output_product_list = None
    evicted_product_list = None

    #one or many logs?
    if options.logfiledir is not None:
        logs = find_log_files(options.logfiledir, options.extension)

    #just point at specific file
    elif options.logfilename is not None:
        logs = [options.logfilename]

    #any log files?
    if len(logs) == 0:
        print ("Cannot generate report as no log files!")
        sys.exit()

    #do we need to create an output list of all products synchronised (useful for checking)
    if options.output_product_list:
        output_product_list = options.output_product_list

    if options.evicted_product_list:
        evicted_product_list = options.evicted_product_list

    #extract and summarise log details
    final_report = ''

    try:

       #synchronizer
       report, products_synchronised = synchronizer_report(logs, write_products=output_product_list)

       final_report += report

       #downloads - success
       final_report += download_report_success(logs)

       # downloads - success
       final_report +=  download_report_fail(logs)

       #evicted products
       report, products_evicted = eviction_report(logs, write_products= evicted_product_list)

       final_report += report

       print (final_report)

       if options.outputfiledir:

           csv_report = report.replace("\t",",").replace(";",",")

           reportfilename = os.path.join(options.outputfiledir,"SYNCHRONIZER_report_%s.csv" %datetime.now().strftime("%d_%m_%yT%H%M%S"))

           if create_file(reportfilename, csv_report):
               print ("Report created at: %s" %reportfilename)



    except IOError as ex:
        print ("IO Error encountered generating reports: %s" %ex)
        sys.exit()

    except Exception as ex:
        print ("Failed generating reports: %s" %ex)
        sys.exit()


    #create an output file listing products synchronised
    if products_synchronised and output_product_list:

        try:

            formatted_list = ["%s\n" % l for l in products_synchronised]

            if create_file(output_product_list, formatted_list):
                print ("List of products successfully synchronised: %s" %output_product_list)

            else:
                print ("Problem creating %s" %output_product_list)

        except Exception as ex:
            print ("Problem creating %s (%s)" %(output_product_list, ex))

    #create an output file listing evicted products
    if evicted_product_list and products_evicted:

        try:

            formatted_list = ["%s\n" % l for l in products_evicted]

            if create_file(evicted_product_list, formatted_list):
                print ("List of products successfully synchronised: %s" %evicted_product_list)

            else:
                print ("Problem creating %s" %evicted_product_list)

        except Exception as ex:
            print ("Problem creating %s (%s)" %(evicted_product_list, ex))





