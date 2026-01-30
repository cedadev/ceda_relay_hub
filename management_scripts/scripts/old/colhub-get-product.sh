#!/bin/bash
export TZ=UTC

outDir=/gpfs/DATA2/ingest/colhub
hostUrl=https://colhub.esa.int/dhus
# keep account a bit secret
export WGETRC=$(dirname $0)/.colhubrc

# error handler: print location of last error and process it further
function error_handler() {
  LASTLINE="$1" # argument 1: last line of error occurence
  LASTERR="$2"  # argument 2: error code of last command
  echo "$(date +%Y-%m-%dT%H:%M:%SZ) ERROR in ${0} (line ${LASTLINE} exit status: ${LASTERR})"
  exit $LASTERR
}
# abort and log errors
set -e
trap 'error_handler ${LINENO} $?' ERR

function log() {
  echo "$(date +%Y-%m-%dT%H:%M:%SZ) INFO: $1"
}

product=$(echo $1 |cut -d. -f1)
condition="Name eq '$product'"
log "Retrieving file with: $condition"

# now retrieve the file via their uuids
uuid=$(/usr/bin/wget -q -O - "https://colhub.esa.int/dhus/odata/v1/Products?\$filter=$condition" \
  | xmllint --xpath '//*[local-name()="Id" or local-name()="Name" or (local-name(..)="Checksum" and local-name()="Value") or local-name()="ContentLength" or local-name()="IngestionDate"]' - \
  | sed -e 's^</d:Value>^#^g' -e 's/></;/g' -e 's^<*/*d:[a-zA-Z]*>*^^g' \
  | tr '#' '\n' \
  | head -1 \
  | cut -d';' -f1
)
file=$outDir/${product}.SAFE.zip

# retreive file
log "Reading $uuid $file"
/usr/bin/wget -q --output-document=${file}_tmp "${hostUrl}/odata/v1/Products('${uuid}')/\$value"
mv ${file}_tmp ${file}
log "Transferred $file $(stat --format '%s' $file) bytes"

log "Done."

