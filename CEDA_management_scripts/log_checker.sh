#!/bin/sh

if [ $# -ne 2 ]
then
	echo "Script to grep hourly occurnces of a string in the dhus log file"
	echo "Usage: <logfile> <string to grep>"
	exit
fi

log=$1
stringtogrep=$2

#work out year month day from first line of log
year=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $1}'`
month=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $2}'`
day=`head -1 $log | awk '{print $1}' | sed 's/\]\[/\t/g' | awk '{print $2}' | tr '-' '\t' | awk '{print $3}'`
	
total=0

for i in {00..23};
do 

	number=`grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $log | grep -c "${stringtogrep}"`

	echo "Hour ${i}: ${number}"

	total=`expr $number + $total`
done

echo -e "\nTotal: ${total}"
