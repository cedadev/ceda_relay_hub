#!/bin/sh

#Script to wrap Find_Sentinel_Data.py alignment reports in the :
# Primary (srh with top level reference hub)
# Secondary (srh with actual source hub)
# Source-to-Primary (alignment of source hub with primary hub).
# BE-FE (alignment of backend and frontend SRH hubs).

if [ $# != 7 ]
then
        echo "Usage: <days back to check i.e. 5> <product string i.e. S1A> <primary order config i.e. colhub> <secondary order config i.e. greek> <src-primary config> <BE-FE c
onfig: main> <BE-FE config: secondary>"
        echo "Note: configs must be the alignment reporting configs that check use at least TWO hubs with reference usually colhub and another hub i.e SRH or airbus etc"
        exit
fi

days_back=$1
prod_string=$2
primary=$3
secondary=$4
sourceTOprimary=$5
be_to_fe=$6
be_to_fe2=$7

script_loc="/srh_data_incoming_6/dhus_monitor_software/sentinel/python/Find_Sentinel_Data.py"

#primary="/usr/local/srh_install/reporting//config//alignment_reporting_PRIMARY.cfg"
#secondary="/usr/local/srh_install/reporting//config//alignment_reporting_SECONDARY.cfg"
#sourceTOprimary="/usr/local/srh_install/reporting//config//alignment_reporting_SRC-PRIMARY.cfg"

echo -e "Hub alignment report: `date +\%d-\%m-\%Y" "\%H:\%M:\%S` \n"

for ((i=$days_back;i>0;i-=1)) ;
do
        days_ago=`date --date="${i} day ago" +\%d-\%m-\%Y`

        echo "Report for ${days_ago} (${i} days ago):"

        cnt=1
        for j in "${primary}" "${secondary}" "${sourceTOprimary}" "${be_to_fe}" "${be_to_fe2}";do

                #aligned=`python3 $script_loc -c $j -N -S $days_ago -E $days_ago -p $prod_string | grep aligned | awk '{print $4}'`
                scriptop_ingest=`python3 $script_loc -c $j -N -S $days_ago -E $days_ago -p $prod_string -I`
                scriptop_aqc=`python3 $script_loc -c $j -N -S $days_ago -E $days_ago -p $prod_string`

                #need double quotes to preserve script op structure https://stackoverflow.com/questions/613572/capturing-multiple-line-output-into-a-bash-variable
                firsthubnum_ingest=`echo "$scriptop_ingest" | grep Identified | head -1 | awk '{print $2}'`
                secondhubnum_ingest=`echo "$scriptop_ingest" | grep Identified | head -2 | tail -1 | awk '{print $2}'`
                aligned_ingest=`echo "$scriptop_ingest" | grep aligned | awk '{print $4}'`

                firsthubnum_aqc=`echo "$scriptop_aqc" | grep Identified | head -1 | awk '{print $2}'`
                secondhubnum_aqc=`echo "$scriptop_aqc" | grep Identified | head -2 | tail -1 | awk '{print $2}'`
                aligned_aqc=`echo "$scriptop_aqc" | grep aligned | awk '{print $4}'`

                #should always follow this sequence if stick to this convention in the config files.
                if [ $cnt -eq 1 ]
                then
                        msg="PRIMARY"
                elif [ $cnt -eq 2 ]
                then
                        msg="SECONDARY"
                elif [ $cnt -eq 3 ]
                then
                        msg="SOURCE-REFERENCE"
                elif [ $cnt -eq 4 ]
                then
                        msg="BE-FE (Main)"
                elif [ $cnt -eq 5 ]
                then
                        msg="BE-FE (Secondary)"
                fi

                #get some summary info so can see which hubs are synchronising
                #which_hubs=`grep "target:" $j | awk '{print $2}' | tr '\n' ' ' | awk '{print $1" => "$2}'`
                ref_hub=`grep "target:" $j | awk '{print $2}' | tr '\n' ' ' | awk '{print $1}'`
                target_hub=`grep "target:" $j | awk '{print $2}' | tr '\n' ' ' | awk '{print $2}'`

                #echo "${msg} IngestDate [${which_hubs} ${firsthubnum_ingest}/${secondhubnum_ingest}] product: ${prod_string}  ${aligned_ingest}%"
                #echo "${msg} AqcuisitionDate [${which_hubs} ${firsthubnum_aqc}/${secondhubnum_aqc}] product: ${prod_string}  ${aligned_aqc}%"

                echo "${msg} IngestDate [${ref_hub} (${firsthubnum_ingest})  => ${target_hub} (${secondhubnum_ingest})] product: ${prod_string}  ${aligned_ingest}%"
                echo "${msg} AqcuisitionDate [${ref_hub} (${firsthubnum_aqc})  => ${target_hub} (${secondhubnum_aqc})] product: ${prod_string}  ${aligned_aqc}%"
                echo " "

                cnt=`expr $cnt + 1`

                firsthubnum_ingest=""
                secondhubnum_ingest=""
                firsthubnum_aqc=""
                secondhubnum_aqc=""
                aligned_ingest=""
                aligned_aqc=""
        done
        echo -e "\n"
done
