#!/bin/bash
export TZ=UTC

if [ $# != 3 ]
then
	echo "Usage: <1: hostUrl i.e https://colhub.esa.int/dhus> <2: outputdir> <3: product [GRD, SLC, OCN]>"
	exit
fi


outDir=$2
#outDir=/datacentre/processing/sentinel/relay_hub_testing/ingest/colhub
archiveDir=/datacentre/processing/sentinel/relay_hub_testing/archive
hostUrl=$1

product=$3

#hostUrl=https://colhub.esa.int/dhus
# keep account a bit secret
export WGETRC=$(dirname $0)/.colhubrc

WD=$HOME/.dhusget
PIDFILE=$WD/pid
LOCK=$WD/lock

# create working directory
test -d $WD || mkdir -p $WD 

# check for existing lock (directory) 
mkdir ${LOCK}
if [ ! $? == 0 ]; then 
  echo -e "$(date +%Y-%m-%dT%H:%M:%SZ) ERROR: an istance of \"dhusget\" retriever is running with Pid=$(cat ${PIDFILE}) (if it isn't running delete the lockdir ${LOCK} )"
  exit 
else
  echo $$ > $PIDFILE
fi

# ensure lock is removed when exiting
trap "rm -fr ${LOCK}" EXIT
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

# keeps the latest ingestionDate of previous retrieval
lastDateHolder=$WD/lastFileDate

echo $lastDateHolder

# repeat until no more files are found
#while : ; do

if [ -r $lastDateHolder ]; then
  lastIngestionDate="$(cat $lastDateHolder)"
else
  lastIngestionDate="NOW-1DAY"
fi
condition="${product} AND ingestionDate:[${lastIngestionDate} TO NOW]"
log "Searching for new files with $condition"

searchstring=`echo "$hostUrl/search?q=$condition"'&rows=10000'`

echo $searchstring

# query for new data
uuids=$( /usr/bin/wget -q -O - "$hostUrl/search?q=$condition"'&rows=10000' \
      | egrep '<id>|"filename"|"ingestiondate"' |cut -d'>' -f2| cut -d'<' -f1 | grep -v http \
      | paste -d';' - - - |sort -t';' -k3)
# --xpath '//*[local-name()="Id" or local-name()="Name" or (local-name(..)="Checksum" and local-name()="Value") or local-name()="ContentLength" or local-name()="IngestionDate"]' -
# | sed -e 's/></;/g' -e 's^<*/*d:[a-zA-Z]*>*^^g'

count=$(echo $uuids | wc -w)
if [ $count == 0 ]; then
  log "Found nothing."
  exit 0;
fi

log "Found $count products..."

# now retrieve the files via their uuids
index=0
for f in ${uuids[@]} 
do
  uuid=$(echo $f | cut -d';' -f1)
  safe=$(echo $f | cut -d';' -f2)
  ingestionDate=$(echo $f | cut -d';' -f3)
  file=$outDir/${safe}.zip
  index=$((index+1))

  # check if already retrieved
  if [ -r $file ]; then
    log "[$index/$count] Skipping $file"
    continue
  elif [[ ($ingestionDate == $lastIngestionDate) && ( $($(dirname $0)/colhub-query-product.sh $safe |grep -c '<d:Name>') == 1 ) ]]; then
    log "[$index/$count] Skipping archived $f"
    continue
  else
    # retreive file
    log "[$index/$count] Reading $f"
    /usr/bin/wget -q -O ${file}_tmp "${hostUrl}/odata/v1/Products('${uuid}')/\$value"
    mv ${file}_tmp ${file}
    log "[$index/$count] Transferred $file $(stat --format '%s' $file) bytes"
  fi

  # remember date of last file
  echo -n $ingestionDate > $lastDateHolder
  touch -t $(echo $ingestionDate | tr -d -- '-: .TZ' |cut -c1-12) $lastDateHolder
done

log "Done."

