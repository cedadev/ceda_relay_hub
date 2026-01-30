#!/bin/sh

logfile=$1
year=$2
month=$3
day=$4

for i in {00..23};
do 

	number=`grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $logfile | grep -c 'already exists'`

	echo "Hour ${i}: ${number}"
done
