#!/bin/sh

# Shell script to wrap python publication delay report - needs to extract UID's from log file

log=$1
config=$2

#get list of UID's from log file
grep  'successfully downloaded from' $log  | awk '{print $12}' | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u  > temp.txt

#run analyser on it
if [ -f temp.txt ]
then
	scriptdir=`dirname $0`
	cmd="python3 ${scriptdir}/report_publication_delay.py ${config} temp.txt"
	exec $cmd
	rm temp.txt
else
	echo "ERROR: Unable to generated list file"
fi

