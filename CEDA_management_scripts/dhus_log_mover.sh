#!/bin/sh

#simplfied log mover, calculates week number from log filename

#logfilename=$1
logdir=$1
opdir=$2

for logfilename in `find $logdir -maxdepth 1 -name 'dhus-*.log' -print`
do

	logdate=`basename $logfilename | cut -c 6-15`
	year=`date -d $logdate +%Y`
	weeknum=`date -d $logdate +%V`

	#will create dir tree needed for reports etc
	opdirname="${opdir}/${year}/${weeknum}"
	opsummary="${opdirname}/summaries"

	echo "Moving $logfilename to $opdirname"
	#make the week directory
	if [ ! -d $opsummary ]
	then
        	mkdir -p $opsummary
	fi

	#mv $logfilename $opdirname
	cp $logfilename $opdirname

done
