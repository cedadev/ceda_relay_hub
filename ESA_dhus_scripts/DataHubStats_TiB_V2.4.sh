#!/bin/bash
#******************************************************************************
#* PROCEDURE : DataHubStats
#*
#* ROLE :
#*     Compute Statistics on DHR
#*
#* USAGE:
#*     ./DataHubStats.sh <start_date> <end_date> <output_directory>
#*
#*
#* PROJECT  :     DHR - FR Relay
#* SOCIETE  :     CLS - France
#* CREATION :     02/03/2017 - C. NGOLET
#*
#******************************************************************************
# HISTORY :
#
# 1.0 10/09/2017 C. NGolet
#     Creation
# 1.1 22/09/2017 B. Pirrotta
#     Adaptation of the script - refactoring
# 1.2 19/10/2017 CLS/E. Berton
#     Correction of Byte Unit (TB to TiB)
# 1.3 04/12/2017 B. Pirrotta
#     Replacement of find by date by a loop on filename
# 2.0 05/12/2017 B. Pirrotta
#     Generation of raw CSV files - 1 data per line
# 2.1 26/01/2018 B. Pirrotta
#     Change Key of raw CSV files : key is now hostname-datatype
# 2.2 24/05/2018 A. Scremin
#     Added new data_type (S3) and modified some of them (S1 and S2)
# 2.4 26/03/2021 A. Zavras
#     Applied DataHubStats_TiB.patch, added new data_type (S5P), fixed metrics
#     (log metrics where overwriting the last value inserted into the array instead of appending it).
#******************************************************************************

###############################################
# CONFIGURATION SECTION                       #
###############################################

log_dir='/srh_data/srh_logs/srh-services4.ceda.ac.uk/2021/32'
data_type=(S1A_.._RAW_ S1B_.._RAW_ S1A_.._SLC_ S1B_.._SLC_ S1A_.._GRDM S1B_.._GRDM S1A_.._GRDH S1B_.._GRDH S1A_.._GRDF S1B_.._GRDF S1A_.._OCN_ S1B_.._OCN_ S2A_MSIL1C_ S2B_MSIL1C_ S2A_MSIL2A_ S2B_MSIL2A_ S3A_SR_ S3A_OL_ S3A_SL_ S3B_SR_ S3B_OL_ S3B_SL_ S2B_ S2A_ S1B_ S1A_ S3A_.._ S3B_.._ S5P_NRTI_L2 S5P_OFFL_L1B S5P_OFFL_L2 .*_AUX_)
header="key;from;to;product type;nb products;size;reporting period"
header2="key;from;to;product type;Bandwith (Mbps);reporting period"
log_file_prefix=$log_dir"/dhus-"
log_file_suffix=".log"

#to be changed accordingly to DHR executing the script

DHRNAME="collaborative_uk_ops"

####################################################

DATE=$(date +"%Y%m%d")
Hour=$(date +"%H%M%S")

if [ $# -eq 0 ]; then

  echo "No arguments supplied"
  echo "usage :"
  echo "./DataHubStats.sh <start_date> <end_date> [<output_directory>] "
  exit 1
fi

if [ -z "$1" ]; then

  echo "No start date supplied"
  exit 1

fi

if [ -z "$2" ]; then

  echo "No end date supplied"
  exit 1

fi

if [ ! -z "$3" ]; then
  outputfolder="$3"
else
  outputfolder="."
fi

date_format="^[0-9]{4}\-[0-9]{2}\-[0-9]{2}$"

if [[ ! $1 =~ $date_format ]]; then

  echo "the start date format is not correct "
  exit 1
fi

if [[ ! $2 =~ $date_format ]]; then

  echo "the end date format is not correct "
  exit 1
fi

#******************************************************************************
#  FUNCTION: Remote_client_Volume_Count
#  ROLE:
#       Display volume count per product per client
#  PARAMETERS:
#       1. Product
#       2. Client
#       3. Log file to grep
#  OUTPUT:
#       1. Display volume count
#******************************************************************************
Remote_site_Volume_Count() {

  while read line; do
    volume+=("$line")
  done <<<$(egrep -o 'Synchronizer.*'$1'.*bytes.*compressed.*successfully.*synchronized.*from.*'$2'.*' $3 | cut -d' ' -f4 | cut -d'(' -f2)
  #done <<<$(egrep -o 'Product.*'$1'.*bytes.*compressed.*successfully.*synchronized.*from.*'$2'.*' $3 | cut -d' ' -f4 | cut -d'(' -f2)

  volume_total=0
  i=0
  while [ -n "${volume[$i]}" ]; do
    volume_total=$(($volume_total + ${volume[$i]}))
    i=$(($i + 1))
  done

  #conversion from bits to TiB
  volume_total=$(bc <<<"scale=4;($volume_total/1024/1024/1024/1024)")

  #echo ${volume_total//./,}
  echo ${volume_total}

}

#******************************************************************************
#  FUNCTION: Remote_client_Volume_Count
#  ROLE:
#       Dysplay volume count per product per client
#  PARAMETERS:
#       1. Product
#       2. Client
#       3. Logfile to grep
#  OUTPUT:
#       1. Display volume count
#******************************************************************************

Remote_client_Volume_Count() {

  while read line; do
    volume+=("$line")
  done <<<$(egrep -o 'Product.*'$1'.*download.*by.*user.*'$2'.*completed.*in.*' $3 | cut -d'>' -f2 | cut -d'(' -f1)

  volume_total=0
  i=0
  while [ -n "${volume[$i]}" ]; do
    volume_total=$(($volume_total + ${volume[$i]}))
    i=$(($i + 1))
  done

  #conversion from bits to TiB
  volume_total=$(bc <<<"scale=4;($volume_total/1024/1024/1024/1024)")

  #echo ${volume_total//./,}
  echo ${volume_total}

}

#******************************************************************************
#  FUNCTION: Bandwith_client_Count
#  ROLE:
#       Dysplay average bandwith per product per client
#  PARAMETERS:
#       1. Product
#       2. Client
#       3. Logfile to grep
#  OUTPUT:
#       1. Display average bandwidth
#******************************************************************************
Bandwith_client_Count() {

  while read line; do
    download+=("$line")
  done <<<$(egrep -o 'Product.*'$1'.*download.*by.*user.*'$2'.*completed.*in.*' $3 | awk '{print $10$12}' | awk -F '[ms]' '{print $1";"$3}')

  bandwith=0
  total_bandwith=0
  average_bandwith=0
  j=0
  i=0

  if [ -n "${download[0]}" ]; then

    for line in ${download[@]}; do
      while IFS=";" read -a calc; do
        bandwith=$((${calc[$(($j + 1))]} / ${calc[$j]}))
        total_bandwith=$(($total_bandwith + $bandwith))
        j=0
        i=$(($i + 1))
      done <<<$(echo $line)
    done

    average_bandwith=$(($total_bandwith / $i))

  else
    average_bandwith=0

  fi

  #conversion from bits/ms to Mbps
  average_bandwith=$(bc <<<"scale=4;($average_bandwith*8/1000)")

  #echo ${average_bandwith//./,}
  echo ${average_bandwith}

}

#******************************************************************************
#  MAIN PROGRAM
#******************************************************************************

d1=$(date +%s -d $1)
d2=$(date +%s -d $2)
diff_days=$(echo $d1 $d2 | awk '{print ($2-$1)/(60*60*24)}')

for i in $(seq 0 $diff_days); do

  current_date=$(date -d "$1 + $i days" +%Y-%m-%d)
  file=${log_file_prefix}${current_date}${log_file_suffix}

  if [[ -f $file ]]; then
    egrep '(download.*by.*user.*completed)|(successfully.*synchronized.*from.*http.*)' $file >>"${outputfolder}/report_log_file_"$DATE"_"$Hour
    echo "$file took into account"
  else
    echo "$file does not exist"
  fi
done

while read line; do
  remote_site+=("$line")
done <<<$(cat "${outputfolder}/report_log_file_"$DATE"_"$Hour | egrep -o 'from.*http.*' | cut -d' ' -f2 | sort -d | uniq)

while read line; do
  remote_client+=("$line")
done <<<$(cat "${outputfolder}/report_log_file_"$DATE"_"$Hour | egrep -o 'download.*by.*user.*completed' | cut -d' ' -f4 | sort -d | uniq)

# Generation of retrieved statistics

echo "$header" >"${outputfolder}/retrieved_report_"$1"_"$2".csv"

i=0
j=0
while [ -n "${remote_site[$i]}" ]; do

  for j in $(seq 0 $((${#data_type[*]} - 1))); do

    remoteSite=$(echo ${remote_site[$i]} | cut -d"/" -f3)
    #Number_of_retrieved=$(egrep -c ${data_type[$j]}'.*successfully.*'${remote_site[$i]}'.*' "${outputfolder}/report_log_file_"$DATE"_"$Hour)
    #Volume_of_retrieved=$(Remote_site_Volume_Count ${data_type[$j]} ${remote_site[$i]} "${outputfolder}/report_log_file_"$DATE"_"$Hour)
    Number_of_retrieved=`egrep -c ${data_type[$j]}'.*successfully.*'${remote_site[$i]}'.*' "${outputfolder}/report_log_file_"$DATE"_"$Hour`
    Volume_of_retrieved=`Remote_site_Volume_Count ${data_type[$j]} ${remote_site[$i]} "${outputfolder}/report_log_file_"$DATE"_"$Hour`
    output="${remoteSite}-${data_type[$j]};${remote_site[$i]};$DHRNAME;${data_type[$j]};$Number_of_retrieved;$Volume_of_retrieved;$1 to $2"
    echo $output >>"${outputfolder}/retrieved_report_"$1"_"$2".csv"
  done

  i=$(($i + 1))
done

# Generation of distributed  statistics

echo "$header" >"${outputfolder}/distributed_report_"$1"_"$2".csv"
i=0
j=0
while [ -n "${remote_client[$i]}" ]; do
echo ${remote_client[$i]}

  for j in $(seq 0 $((${#data_type[*]} - 1))); do
    remoteClient=$(echo ${remote_client[$i]} | cut -d"/" -f3)
    Number_of_distributed=$(egrep -c 'Product.*'${data_type[$j]}'.*download.*by.*user.*'${remote_client[$i]}'.*completed.*in.*' "${outputfolder}/report_log_file_"$DATE"_"$Hour)
    Volume_of_distributed=$(Remote_client_Volume_Count ${data_type[$j]} ${remote_client[$i]} "${outputfolder}/report_log_file_"$DATE"_"$Hour)
    output="${remoteClient}-${data_type[$j]};$DHRNAME;${remote_client[$i]};${data_type[$j]};$Number_of_distributed;$Volume_of_distributed;$1 to $2"
    echo $output >>"${outputfolder}/distributed_report_"$1"_"$2".csv"
  done
  i=$(($i + 1))

done

# Generation of bandwith client statistics

echo "$header2" >"${outputfolder}/client_Bandwith_usage_report_"$1"_"$2".csv"
i=0
j=0
while [ -n "${remote_client[$i]}" ]; do

  for j in $(seq 0 $((${#data_type[*]} - 1))); do
    remoteClient=$(echo ${remote_client[$i]} | cut -d"/" -f3)
    Bandwith_of_distributed=$(Bandwith_client_Count ${data_type[$j]} ${remote_client[$i]} "${outputfolder}/report_log_file_"$DATE"_"$Hour)
    output="${remoteClient}-${data_type[$j]};$DHRNAME;${remote_client[$i]};${data_type[$j]};$Bandwith_of_distributed;$1 to $2"
    echo $output >>"${outputfolder}/client_Bandwith_usage_report_"$1"_"$2".csv"
  done

  i=$(($i + 1))
done

rm "${outputfolder}/report_log_file_"$DATE"_"$Hour
