#!/bin/sh

if [ $# -ne 6 ]
then
	echo "Script to grep hourly occurnces of a string in the dhus log file"
	echo "Usage: <logfile> <year> <month> <day> <string to grep> <second string to grep>"
	exit
fi
	

logfile=$1
year=$2
month=$3
day=$4
stringtogrep=$5
stringtogrep2=$6

for i in {00..23};
do 

	number=`grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $logfile | grep "${stringtogrep}" | grep -c "${stringtogrep2}"`

	echo "Hour ${i}: ${number}"
done
