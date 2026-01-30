#!/bin/bash
#Script to find and move all log files associated with a week number to a dedicated folder
#
if [ $# != 3 ]
then
	echo "Usage: <source directory> <destination directory> <week number (1-52)>"
	exit
fi

sourcedir=$1
destdir=$2
year=2018
week=$3
#dhus-2016-08-14.log
#report_line=`echo "./reporting_statistics.sh -i UKDHR -d https://srh-test1.cems.rl.ac.uk/dhus -u collaborative_uk_ops -p sc00byd00 "`
#need format 2016-09-30T00:00:00.000Z
#date_fmt="+%b %d"
#date_fmt="+%Y-%m-%dT%H:%M:%SZ"
date_fmt="+%Y-%m-%d"

week_num_of_Mon_1=$(date -d $year-01-01 +%W)
week_day_of_Mon_1=$(date -d $year-01-01 +%u)

if ((week_num_of_Mon_1)); then
   first_Mon=$year-01-01
else
   first_Mon=$year-01-$((01 + (7 - week_day_of_Mon_1 + 1) ))
fi

for nr_of_day_of_week in 0 1 2 3 4 5 6
do
    day_of_week=$(date -d "$first_Mon +$((week - 1)) week + $nr_of_day_of_week day" "$date_fmt")
    log_name=`echo "dhus-${day_of_week}.log"`
    sourcelog=`echo "${sourcedir}/$log_name"`
    fulldestdir=`echo "${destdir}/${year}/${week}/"`
    fulldestdir_summaries=`echo "${destdir}/${year}/${week}/summaries"`
    
    #if target directory does not exist create it
    if [ ! -d $fulldestdir ]
    then
	echo "Creating target directory: ${fulldestdir}"
	mkdir -p $fulldestdir
    fi

   #create dir now for reports to go into
   if [ ! -d $fulldestdir_summaries ]
   then
        echo "Creating target directory: ${fulldestdir_summaries}"
        mkdir -p $fulldestdir_summaries
    fi

    if [ -f $sourcelog ]
    then
	echo "moving ${sourcelog} to ${fulldestdir}"
	#cp -r $sourcelog $fulldestdir
	mv $sourcelog $fulldestdir
    fi
done
