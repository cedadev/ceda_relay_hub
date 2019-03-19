#!/bin/sh

if [ $# -ne 1 ]
then
	echo "Script to calculate hourly download rates for the given logfile"
	echo "Usage: <logfile>"
	exit
fi

log=$1
stringtogrep="successfully synchronized"

#work out year month day from first line of log
year=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $1}'`
month=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $2}'`
day=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $3}'`
	
total=0

for i in {00..23};
do

    #calculate volume for this hour
    hour_volume=0
    for j in `grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $log | grep stringtogrep /srh/data/logs/dhus.log | grep -o '(.*)' | awk '{print $1}'  | sed 's/[(,)]//g'`;
    do
        hour_volume=`expr $j + $hour_volume
    done

	number=`grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $log | grep -c "${stringtogrep}"`

	echo -e "Hour ${i}: ${number}\t Volume downloaded: ${hour_volume}"

	total=`expr $number + $total`
done

echo -e "\nTotal: ${total}"
