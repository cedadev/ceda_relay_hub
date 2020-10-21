#!/bin/bash

#-------------------------------------------------------------------------------------------	#
# Serco SpA 2016
#-------------------------------------------------------------------------------------------	#

function print_usage 
{ 
 echo "Usage: reporting_statistics.sh [ -i <DHR Identifier>] [-d <DHR URL>] [-u <username> ] [ -p <password>] [ -s <starting_ingestion_date> ] [ -e <ending_ingestion_date> ]"
 echo "---------------------------------------------------------------------------------------------------------------------------"
 echo "-i <DHR Identifier>              : insert the Data Hub Relay identifier"
 echo "-d <DHR URL>                     : specify the URL of the Data Hub Relay ;"
 echo "-u <username>                    : data hub username provided after registration on <DHR URL> ;"
 echo "-p <password>                    : data hub password provided after registration on <DHR URL> ;"
 echo "-s <starting_ingestion_date>	    : Search every product ingested after the <starting_ingestion_date>. The date format shall be in ISO 8601 format (YYYY-MM-DDThh:mm:ss.cccZ) ;"
 echo "-e <ending_ingestion_date>		: Search every product ingested before the <ending_ingestion_date>. The date format shall be in ISO 8601 format (YYYY-MM-DDThh:mm:ss.cccZ) ;"
 exit -1
}

while getopts ":i:d:u:p:s:e:h:" opt; do
 case $opt in
        i)
                export DHR_ID="$OPTARG"
                ;;
	d)
		export DHUS_DEST="$OPTARG"
		;;
	u)
		export USERNAME="$OPTARG"
		;;
	p)
		export PASSWORD="$OPTARG"
		;;
        s)
		export INGESTION_TIME_FROM="$OPTARG"
                ;;
        e)
                export INGESTION_TIME_TO="$OPTARG"
                ;;
        h)	
		print_usage $0
		;;
	esac
done

printf "\n"

PRODUCT_TYPE[0]="SLC" #   'SLC' 'GRD' 'RAW' 'OCN' 'MSI1C' 'DO_0_DOP' 'OL_0_EFR'
PRODUCT_TYPE[1]="GRD"
PRODUCT_TYPE[2]="RAW"
PRODUCT_TYPE[3]="OCN"
PRODUCT_TYPE[4]="S2MSI1C"
PRODUCT_TYPE[5]="DO_0_DOP"
PRODUCT_TYPE[6]="OL_0_EFR"

if [ -z $DHR_ID ];then
        read -p "Enter DHR identifier: " VAL
        printf "\n\n"
        export DHR_ID=${VAL}
fi

if [ -z $DHUS_DEST ];then
        read -p "Enter URL link: " VAL
        printf "\n\n"
        export DHUS_DEST=${VAL}
fi

if [ -z $USERNAME ];then
        read -p "Enter username: " VAL
        printf "\n\n"
        export USERNAME=${VAL}
fi

if [ -z $PASSWORD ];then
	read -s -p "Enter password: " VAL
        printf "\n\n"
	export PASSWORD=${VAL}
fi


echo "format ingestion time: YYYY-MM-DDThh:mm:ss.cccZ"
echo ""

if [ -z $INGESTION_TIME_FROM ];then
	read -p "Enter reporting period start date: " VAL
        printf "\n\n"
        export INGESTION_TIME_FROM=${VAL}
fi

if [ -z $INGESTION_TIME_TO ];then
	read -p  "Enter reporting period end date: " VAL
        printf "\n\n"
        export INGESTION_TIME_TO=${VAL}
fi

NAMEFILE="${DHR_ID}_${INGESTION_TIME_FROM}_${INGESTION_TIME_TO}"

rm ${NAMEFILE}.csv

touch ${NAMEFILE}.csv

rm .OSproduct-type-final.txt

rm .OSproduct-type-ingestion-date-final.txt

wget --no-check-certificate --user=${USERNAME} --password=${PASSWORD} "${DHUS_DEST}/odata/v1/Users/\$count" -O .query1.txt
VAL=`cat .query1.txt`
echo "Number of registered users from first start;"$VAL > .query1_final.txt

wget --no-check-certificate --user=${USERNAME} --password=${PASSWORD} "${DHUS_DEST}/odata/v1/Products/\$count" -O .query2.txt
VAL=`cat .query2.txt`
echo "Number of uploaded products from first start;"$VAL > .query2_final.txt

wget --no-check-certificate --user=${USERNAME} --password=${PASSWORD} -O .OSproducts.txt "${DHUS_DEST}/search?q=ingestionDate:[${INGESTION_TIME_FROM}%20TO%20${INGESTION_TIME_TO}]"
VAL=`grep '<opensearch:totalResults>' .OSproducts.txt | cut -d'>' -f2 | cut -d'<' -f1`
echo "Number of uploaded products in reporting period;"$VAL > .OSproducts-final.txt

echo "" >> .OSproduct-type-final.txt
echo "Uploaded products from first start" >> .OSproduct-type-final.txt
echo "" >> .OSproduct-type-final.txt

for i in "${PRODUCT_TYPE[@]}" 
do
rm .OSproduct-type.txt
wget --no-check-certificate --user=${USERNAME} --password=${PASSWORD} -O .OSproduct-type.txt  "${DHUS_DEST}/search?q=producttype:${i}"
VAL=`grep '<opensearch:totalResults>' .OSproduct-type.txt | cut -d'>' -f2 | cut -d'<' -f1` 
echo "${i};"$VAL >> .OSproduct-type-final.txt
done

echo "" >> .OSproduct-type-ingestion-date-final.txt
echo "Uploaded products in reporting period $INGESTION_TIME_FROM TO $INGESTION_TIME_TO" >> .OSproduct-type-ingestion-date-final.txt
echo "" >> .OSproduct-type-ingestion-date-final.txt

for i in "${PRODUCT_TYPE[@]}"
do
rm .OSproduct-type-ingestion-date.txt
wget --no-check-certificate --user=${USERNAME} --password=${PASSWORD} -O .OSproduct-type-ingestion-date.txt  "${DHUS_DEST}/search?q=ingestionDate:[${INGESTION_TIME_FROM}%20TO%20${INGESTION_TIME_TO}]%20AND%20producttype:${i}"
VAL=`grep '<opensearch:totalResults>' .OSproduct-type-ingestion-date.txt | cut -d'>' -f2 | cut -d'<' -f1`
echo "${i};"$VAL >> .OSproduct-type-ingestion-date-final.txt
done

cat .query1_final.txt >> ${NAMEFILE}.csv

printf  "\n" >> ${NAMEFILE}.csv

cat .query2_final.txt >> ${NAMEFILE}.csv

printf  "\n" >> ${NAMEFILE}.csv

cat .OSproducts-final.txt >> ${NAMEFILE}.csv

cat .OSproduct-type-final.txt >> ${NAMEFILE}.csv

cat .OSproduct-type-ingestion-date-final.txt >> ${NAMEFILE}.csv

echo "the end"
