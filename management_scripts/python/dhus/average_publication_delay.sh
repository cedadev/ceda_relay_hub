#!/bin/sh

# Shell script to wrap python publication delay report - needs to extract UID's from log file

if [ $# != 2 ]
then
	echo "Usage: <DHuS log file> <DHuS connection config>"
	exit
fi

log=$1
config=$2

#This list of products should match all dhus where the filter element is set so we can show publication delay per synchroniser
definitive_product_list="S3A_SL_1_RBT S3B_SL_1_RBT S1A_IW_SLC S1B_IW_SLC"
runtime=`date`
echo -e "\nLog file: ${log}"
echo -e "Report at: ${runtime}\n"

for product in ${definitive_product_list}
do
	#echo $product

	#get list of UID's from log file
	grep  'successfully downloaded from' $log  | grep $product | awk '{print $12}' | sed -n "s/.*\(Products[(]'[0-9 a-z -].*'[)]\).*/\1/p" | sed 's/Products//g' | sed "s/[(,)']//g" | tr '/' '\t' | awk '{print $1}' | sort -u  > temp.txt
 	#wc -l temp.txt
	#run analyser on it
	if [ -f temp.txt ]
	then
		results=`wc -l temp.txt | awk '{print $1}'`
		if [ $results != 0 ]
		then

			scriptdir=`dirname $0`
			#cmd="python3 ${scriptdir}/report_publication_delay.py -c ${config} -l temp.txt"
			#exec $cmd
                        result=`python3 ${scriptdir}/report_publication_delay.py -c ${config} -l temp.txt`
		else
			#echo "ERROR: Unable to generated list file"
                        result="0 Products retrieved"

		fi
	else
		result="Problem reporting for this product from this log!"
	fi

	echo "${product} ${result}"

	rm -f temp.txt
done

