#!/bin/bash
export TZ=UTC

hostUrl=https://colhub.esa.int/dhus
# keep account a bit secret
export WGETRC=$(dirname $0)/.colhubrc

condition="Name eq '$(echo $1 |cut -d. -f1)'"
echo "Searching for product $condition"

# query for new data
/usr/bin/wget -q -O - "$hostUrl/odata/v1/Products/?\$top=1&\$filter=$condition" |xmllint --format --nowrap -

