#!/bin/sh

#script to extract publication delay averages from daily report.

#Looks first in backup location, then current report dir

# SJD 04/07/2022

#function to calculate delay based on source directory
scan_directory () {

        dirstr=$1

        if [ -d $dirstr ]
        then

                #is there a file report for that day (not always one if hub issues
                results=`find $dirstr -name "${datestr}*.txt" -print | wc -l`

                if [ $results != 0 ]
                then
                        #echo "result!"
                        found_file=`find $dirstr -name "${datestr}*.txt" -print | head -1`
                        #echo $found_file
                        data=`cat $found_file | grep 'Source:' $found_file | grep  $hub_str | awk '{print $(NF-1)}'`
                        datalen=`expr "$data" : '.*'`

                        if [ $datalen != 0 ] && [ $data != "source" ]
                        then
                                echo $data


                        else
                                echo ""
                        fi
                else
                        echo ""
                fi

        else
                echo ""

        fi

}

if [ $# != 3 ]
then
        echo "Usage <month> <year> <hub_string i.e. colhub>"
        exit
fi

backup_report_dir="/srh_data_incoming_4/srh_logs/${HOSTNAME}/publication_delay"
local_report_dir="/var/www/html/srh_monitoring/publication_delay/"

month=$1
year=$2
hub_str=$3

tmpfile=".report.tmp"

if [ $month -eq 01 ] || [ $month -eq 03 ] || [ $month -eq 05 ] || [ $month -eq 07 ] || [ $month -eq 08 ] || [ $month -eq 10 ] || [ $month -eq 12 ]
then
        days=31
elif [ $month -eq 02 ]
then
        days=28 # fudge not expecting a leap year during this project...
else
        days=30
fi

times=""

for day in $( eval echo {01..$days} )
do
        datestr="${day}-${month}-${year}"

        weeknum=`date -d "${year}-${month}-${day}" +%W`

        dirstr="${backup_report_dir}/${year}/$weeknum"

        #Scan archived delay reports first
        retval=$( scan_directory $dirstr )

        retlen=`expr "$retval" : '.*'`

        #note if successful string should be 17 - but some weirdness might occur so this works better than testing for 0
        if [ $retlen -gt "5" ]
        then
                echo "${year}-${month}-${day},${retval}"

                times="${times} ${retval}"
        else

                #now try the main dir for younger reports
                retvalloc=$( scan_directory $local_report_dir )

                retloclen=`expr "$retvalloc=" : '.*'`

                if [ $retloclen -gt "5" ]
                then
                        #echo $retvalloc
                        echo "${year}-${month}-${day},${retvalloc}"
                        times="${times} ${retvalloc}"

                else
                        echo "${year}-${month}-${day},NULL"
                fi
        fi

done

#Calculate average delay.  Note use awk to parse datesting - using EPOCH and date not good for delays > 24 hours.  This is simpler.
#See https://askubuntu.com/questions/407743/convert-time-stamp-to-seconds-in-bash
totsecs=0
for i in $times
do
        secs=`echo $i | awk -F: '{ print ($1 * 3600) + ($2 * 60) + $3 }'`
        totsecs=`expr $totsecs + $secs`
done

avgsecs=`expr $totsecs / $days`
average_delay=`date -ud "@$avgsecs" +' %H:%M:%S'`

echo "Average delay: ${average_delay}"