#!/bin/bash
#Script to automate wrapping of reporting_statistics.sh
year=2016
report_line=`echo "./reporting_statistics.sh -i UKDHR -d https://srh-test1.cems.rl.ac.uk/dhus -u collaborative_uk_ops -p NNNNNNN "`
#need format 2016-09-30T00:00:00.000Z
#date_fmt="+%b %d"
date_fmt="+%Y-%m-%dT%H:%M:%SZ"

week_num_of_Mon_1=$(date -d $year-01-01 +%W)
week_day_of_Mon_1=$(date -d $year-01-01 +%u)

if ((week_num_of_Mon_1)); then
   first_Mon=$year-01-01
else
   first_Mon=$year-01-$((01 + (7 - week_day_of_Mon_1 + 1) ))
fi

#for nr_of_day_of_week in 0 1 2 3 4 5 6
#for nr_of_day_of_week in 0 6 #first and last days
#do
#    day_of_week=$(date -d "$first_Mon +$((week - 1)) week + $nr_of_day_of_week day" "$date_fmt")
#    echo $day_of_week
#done
for week in 30 31 32 33 34 35 36 37 38 39 40
do
	start=`(date -d "$first_Mon +$((week - 1)) week + 0 day" "$date_fmt")`
	end=`(date -d "$first_Mon +$((week - 1)) week + 6 day" "$date_fmt")`

	cmd=`echo "${report_line} -s ${start} -e ${end}"`

	#exec $cmd
	$cmd
done
