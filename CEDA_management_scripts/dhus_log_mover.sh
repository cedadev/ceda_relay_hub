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
	mvd_logfilename="$logdir/$(basename $logfilename)"

	if [ -f $mvd_logfilename ]; then

		#check moved file is the same before clearing the original
		a=`md5sum $logfilename | awk '{print $1}'`
		b=`md5sum $mvd_logfilename | awk '{print $1}'`

		if [ $a == $b ]
		then
        		rm -f $logfilename	
		else
        		echo "ERROR: Could not remove ${logfilename} as problem with transfer!"
		fi
	fi

done
