#!/bin/bash

#script to submit queries to two hubs using the CEDA sentinel mirror archive downloader

go_back_days=$1
list_dir=$2
hub1_conf=$3
hub2_conf=$4
hub1_pw=$5
hub2_pw=$6
hub1_stream=$7
hub2_stream=$8

retrieve_code_dir="/srh_data/operations/data_retrieval/ceda_sentinel_retriever/sentinel1/"

if [ $# != 8 ]
then
	echo "args: <number of days backwards to check> <list dir> <hub1 conf> <hub2 conf> <hub1 pw> <hub2 pw> <hub1 stream> <hub2 stream>"
	exit
fi

cnt=$go_back_days

while [ $cnt -ne 0 ]
do
	this_date=`date -d "${cnt} day ago"`

	####################### HUB1 ###################################
	echo "Looking for data from hub1 for ${this_date}"

	hub1_output_master_list=`echo "${list_dir}/HUB1_${hub1_stream}.list"`

	day=`date -d "${cnt} day ago" +%d`
	month=`date -d "${cnt} day ago" +%m`
	year=`date -d "${cnt} day ago" +%Y`

	#first hub
	find_cmd_template_hub1="python2.7 ${retrieve_code_dir}Find_Data.py -c ${hub1_conf} -s ${hub1_stream} -D ${day} -M ${month} -Y ${year} -p ${hub1_pw} -o ${hub1_output_master_list} -P"
	

	exec $find_cmd_template_hub1

	if [ -f $hub1_output_master_list ]
	then
		echo "Output: ${hub1_output_master_list}"
	fi

	cnt=`expr $cnt - 1`

done


