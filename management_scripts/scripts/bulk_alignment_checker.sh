#!/bin/sh

#Script to wrap Find_Sentinel_Data.py alignment reports in the :
# Primary (srh with top level reference hub)
# Secondary (srh with actual source hub)
# Source-to-Primary (alignment of source hub with primary hub).
# BE-FE (alignment of backend and frontend SRH hubs).
if [ $# != 6 ]
then
        echo "Usage: <days back to check i.e. 5> <product string i.e. S1A> <primary order config i.e. colhub> <secondary order config i.e. greek> <src-primary config> <BE-FE c
onfig>"
        echo "Note: configs must be the alignment reporting configs that check use at least TWO hubs with reference usually colhub and another hub i.e SRH or airbus etc"
        exit
fi

days_back=$1
prod_string=$2
primary=$3
secondary=$4
sourceTOprimary=$5
be_to_fe=$6

script_loc="/usr/local/srh_install//sentinel/python/Find_Sentinel_Data.py"

#primary="/usr/local/srh_install/reporting//config//alignment_reporting_PRIMARY.cfg"
#secondary="/usr/local/srh_install/reporting//config//alignment_reporting_SECONDARY.cfg"
#sourceTOprimary="/usr/local/srh_install/reporting//config//alignment_reporting_SRC-PRIMARY.cfg"

echo -e "Hub alignment report: `date +\%d-\%m-\%Y" "\%H:\%M:\%S` \n"

for ((i=$days_back;i>0;i-=1)) ;
do
        days_ago=`date --date="${i} day ago" +\%d-\%m-\%Y`

        echo "Report for ${days_ago} (${i} days ago):"

        cnt=1
        for j in "${primary}" "${secondary}" "${sourceTOprimary}" "${be_to_fe}" ;do

                #get some summary info so can see which hubs are synchronising
                which_hubs=`grep "target:" $j | awk '{print $2}' | tr '\n' ' ' | awk '{print $1" => "$2}'`
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
                elif [ $cnt -eq 4 ]
                then
                        msg="BE-FE"
                fi

                echo "${msg} (${which_hubs}) product: ${prod_string}  ${aligned}%"

                cnt=`expr $cnt + 1`

                aligned=""
        done
        echo -e "\n"
done