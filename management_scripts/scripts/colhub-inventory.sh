#!/bin/bash
export TZ=UTC

hostUrl=https://colhub.esa.int/dhus
# keep account a bit secret
export WGETRC=$(dirname $0)/.colhubrc

queryDate=${1:-2016-01-01}
condition="ContentDate/Start gt datetime'${queryDate}T00:00:00.000' and ContentDate/Start lt datetime'${queryDate}T23:59:59.999'"
#echo "Searching for product $condition"

# query for new data
for ((pos=0; ; pos+=100))
do
  page=$(/usr/bin/wget -q -O - "$hostUrl/odata/v1/Products/?\$skip=$pos&\$top=100&\$filter=$condition")
  if [ $(echo $page |grep -c entry) == 0 ]; then
    break
  fi
  echo $page \
  | xmllint --format --nowrap - \
  | egrep 'd:Id|d:Name|d:IngestionDate|        <d:Value>|d:ContentLength|</m:s1b_iw_grdh_UKonly>' | sed -e 's^</m:s1b_iw_grdh_UKonly>^#^' \
  | cut -d'>' -f2| cut -d'<' -f1 | tr -s '\n' ';' |tr -d ' ' |sed -e 's/;#;/#/g' | tr '#' '\n' \
  | sort -t';' -k5
#the following is not supported by all versions of xmllint: 
#  | xmllint --xpath '//*[local-name()="Id" or local-name()="Name" or (local-name(..)="Checksum" and local-name()="Value") or local-name()="ContentLength" or local-name()="IngestionDate"]' - \
#  | sed -e 's^</d:Value>^#^g' -e 's/></;/g' -e 's^<*/*d:[a-zA-Z]*>*^^g' \
#  | tr '#' '\n'
done
