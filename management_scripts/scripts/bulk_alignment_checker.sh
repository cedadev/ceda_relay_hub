#!/bin/sh

#Script to wrap Find_Sentinel_Data.py alignment reports in the :
# Primary (srh with top level reference hub)
# Secondary (srh with actual source hub)
# Source-to-Primary (alignment of source hub with primary hub).

days_back=$1
prod_string=$2

script_loc="/usr/local/srh_install//sentinel/python/Find_Sentinel_Data.py"

primary="/usr/local/srh_install/reporting//config//alignment_reporting_PRIMARY.cfg"
secondary="/usr/local/srh_install/reporting//config//alignment_reporting_SECONDARY.cfg"
sourceTOprimary="/usr/local/srh_install/reporting//config//alignment_reporting_SRC-PRIMARY.cfg"

echo -e "Hub alignment report: `date +\%d-\%m-\%Y" "\%H:\%M:\%S` \n"

for ((i=$days_back;i>0;i-=1)) ;
do
        days_ago=`date --date="${i} day ago" +\%d-\%m-\%Y`

        echo "Report for ${days_ago} (${i} days ago):"

        cnt=1
        for j in "${primary}" "${secondary}" "${sourceTOprimary}" ;do
                aligned=`python3 $script_loc -c $j -N -S $days_ago -E $days_ago -p $prod_string | grep aligned | awk '{print $4}'`
                #aligned=`python3 $script_loc -c $j -N -S $days_ago -E \`date --date='1 day ago' +\%d-\%m-\%Y\` -p $prod_string | grep aligned | awk '{print $4}'`

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
                fi

                echo "${msg} (${prod_string}): ${aligned}%"

                cnt=`expr $cnt + 1`

                aligned=""
        done
        echo -e "\n"
done
