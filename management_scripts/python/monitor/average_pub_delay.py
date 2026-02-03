#Script to analyse concatenated output from get_all_LCD.py and calculate average delay for each string
#will also output csv list ready to be put into tracking spreadsheet.  Just needs lists of weekly LCD files
#that were output from cron generated with get_all_LCD.py and concatened.

#SJD February 2026

import sys
import os

import pandas as pd
import click
#from datetime.datetime import timedelta

class MutuallyExclusiveOption(click.Option):
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
            raise click.UsageError(
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


def get_average_delay(lcd_file, filter_month=None):
    '''
    Method to extract information from raw LCD file and check against required time and date and prepare for merging
    and final output
    '''

    with open(lcd_file.rstrip().lstrip(), 'r') as f:
        lines = [i.rstrip() for i in f.readlines()]

    #automatically detect synchroniser names
    streams = {}
    for line in lines:

        #only select data with a TS that matches the filter - get TS from the current line
        datapoint_ts = pd.Timestamp(line.split(',')[0].split(' ')[1])

        #add timestamp for graphing
        if 'timestamp' not in streams.keys():
            streams['timestamp'] = []

        if not filter_month:
            streams['timestamp'].append(datapoint_ts)

        else:
            if pd.Period(filter_month).start_time < datapoint_ts and datapoint_ts < pd.Period(filter_month).end_time:
                (streams['timestamp']).append(datapoint_ts)
        
        for i in line.split(','):

            #get producers
            if 'producer' in i:
                producer = i.lstrip().split(' ')[0]   

                #add producer data
                if producer not in streams.keys():
                    streams[producer] = []             
                    
                if not filter_month:
                    (streams[producer]).append(i.lstrip().split(' ')[1])

                else:
                    if pd.Period(filter_month).start_time < datapoint_ts and datapoint_ts < pd.Period(filter_month).end_time:
                        (streams[producer]).append(i.lstrip().split(' ')[1])

    return streams


def merge_data(averages):
    '''method to merge similar info streams'''
    merged_data = {}

    for i in averages.keys():        
        for j in averages[i].keys(): #this level is the keys we need to keep == streams
            if j not in merged_data.keys(): # first time encountering key, add it to merged
                merged_data[j] = averages[i][j]

            else: #already encountered key, so just add this extra data to existing data
                merged_data[j] = merged_data[j]+averages[i][j]

    return merged_data


def average_data_streams(streams):
    
    #calculate average for each stream
    #use pandas: https://stackoverflow.com/questions/3617170/average-timedelta-in-list
    averages = {}
    for stream in streams.keys():

        #filter out timestamp column
        if not 'timestamp' in stream:
            averages[stream] = pd.to_timedelta(pd.Series(streams[stream])).mean()

    return averages


def show_average_delay(averages):
    for stream in averages.keys():
        print (f"Average for stream: {stream}: {averages[stream]}")


def output_to_csv(data_streams, output_file, averaged_data):
    '''Write to a csv'''

    #heading = [f"{i}" for i in data_streams.keys()]
    heading = ['timestamp']+[f"{i}({averaged_data[i]})" for i in data_streams.keys() if 'producer' in i]#include average values

    with open(output_file, 'w') as fp:
        #f.writelines(*[f"{i}," for i in data_streams.keys()])
        #fp.writelines("\n".join(str(item) for item in [f"{i}," for i in data_streams.keys()]))
        #[f"{i}," for i in data_streams.keys()]
        #fp.write(",".join(str(item) for item in heading))
        fp.write(f'{",".join(str(item) for item in heading)}\n')

        #now loop through the data
        for entry in range(0,len(data_streams['timestamp'])):
            line = [data_streams[i][entry] for i in data_streams.keys()]
            #fp.writelines(",".join(str(item) for item in line))
            fp.writelines(f'{",".join(str(item) for item in line)}\n')
    
    
@click.command()
@click.option('-r', '--report_list', 'report_list', type=str, required=True, help='Comman delimited list of input weekly LCD reports')
@click.option('-a', '--average_report', 'output_average', cls=MutuallyExclusiveOption, mutually_exclusive=["cat_into_csv"],  \
              is_flag=True, default=False, help='Will calculate average of all values from input docs')
@click.option('-p', '--pretty_print_vals', 'cat_into_csv', cls=MutuallyExclusiveOption, mutually_exclusive=["output_average"],\
               type=str, help='Will generate csv output of all reports ready for spreadsheet')
@click.option('-D', '--filter_by_Year_and_Month', 'filter_by_month', type=str, required=False, help='Filter by Year and Month to aid in monthly reporting. i.e. 02-2025 (MM-YYYY)')
def main(report_list, output_average, cat_into_csv, filter_by_month):

    averages = {}

    #parse reports and calculate average for each
    for report in report_list.split(","):        
        averages[report] = get_average_delay(report, filter_month=filter_by_month)

    #check there is data - base on timestamp
    if len(averages[report]['timestamp']) == 0:
        print (f"No data found matching {filter_by_month}")
        sys.exit()

    #merge extracted info
    merged_data = merge_data(averages)

    if output_average:
        show_average_delay(average_data_streams(merged_data))

    if cat_into_csv:
        output_to_csv(merged_data, cat_into_csv, average_data_streams(merged_data))


if __name__ == '__main__':
    main()
    