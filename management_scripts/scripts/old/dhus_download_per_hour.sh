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
total_volume=0

for i in {00..23};
do

    #calculate volume for this hour
    hour_volume=0
    hour_volume_gb=0
    for j in `grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $log | grep "${stringtogrep}" | grep -o '(.*)' | awk '{print $1}'  | sed 's/[(,)]//g'`;
    do
        #hour_volume=`expr $j + $hour_volume`
        hour_volume=`python -c "print ${j} + ${hour_volume}"`
	hour_volume_gb=`python -c "print ${hour_volume} / 1024 / 1024 / 1024"`
    done

    number=`grep "\[0\.13\.4\-22\]\[${year}\-${month}\-${day} ${i}\:" $log | grep -c "${stringtogrep}"`

    #echo -e "Hour ${i}: ${number}\t Volume downloaded: ${hour_volume_gb}"
    #echo -e "${day}/${month}/${year} ${i}:00:00, ${number},${hour_volume_gb}"
    echo -e "${year}-${month}-${day}T${i}:00:00, ${number},${hour_volume_gb}"

    total=`expr $number + $total`
    total_volume=`python -c "print ${total_volume} + ${hour_volume_gb}"`
done

#echo -e "\nTotal files: ${total}"
#echo -e "\nTotal download (Gb): ${total_volume}"
