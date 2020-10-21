#!/bin/bash
export TZ=UTC
set -e

function usage() {
  echo "USAGE: $0 [-d|--date YYYY-MM-DD] [-r|--reload] [-l|--list] [-k|--keep] [-w|--workingDir]"
  echo ""
  exit 1
}

#defaults
queryDate="2016-01-01"
reloadMisingFiles=false
listMisingFiles=false
keepFiles=false
workingDir=/tmp
# parse commandline
while [[ $# > 0 ]]
do
  key="$1"
  case $key in
    -d|--date)
      queryDate="$2"
      shift
    ;;
    -r|--reload)
      reloadMisingFiles=true
    ;;
    -l|--list)
      listMisingFiles=true
    ;;
    -k|--keep)
      keepFiles=true
    ;;
    -w|--workingDir)
      workingDir="$2"
      shift
    ;;
    *)
      echo "ERROR - unknown option: $key"
      echo ""
      usage
    ;;
  esac
  shift
done

echo "Checking colhub and CRH inventrory for date: $queryDate"

cd $(dirname $0)

# working files
colhubList=$workingDir/colhub-list_${queryDate}_$$.txt
dhrdeList=$workingDir/dhr-list_${queryDate}_$$.txt
missingList=$workingDir/missing-list_${queryDate}_$$.txt
extraList=$workingDir/extra-list_${queryDate}_$$.txt

# cleanup on exit
trap "if [[ "$keepFiles" == "false" ]]; then rm $colhubList $dhrdeList $missingList $extraList; fi" EXIT

# retreive remote and local inventory
./colhub-inventory.sh $queryDate | sort -t _ -k 5 > $colhubList
echo "Count in colhub: $(wc -l $colhubList)"
./crh-inventory.sh $queryDate | sort -t _ -k 5 > $dhrdeList
echo "Count in crh: $(wc -l $dhrdeList)"

# check local extras
diff <(cut -d';' -f2 $colhubList | sort -u -t _ -k 5) <(cut -d';' -f2 $dhrdeList | sort -u -t _ -k 5) |egrep '> S' |cut -c3- > $extraList
if [[ $(wc -l $extraList | cut -d' ' -f1) > 0 ]]; then
  echo "WARNING: ignoring $(wc -l $extraList) extra products in crh"
fi

# check for remote ones that are missing locally
diff <(cut -d';' -f2 $colhubList | sort -u -t _ -k 5) <(cut -d';' -f2 $dhrdeList | sort -u -t _ -k 5) |egrep '< S' |cut -c3- > $missingList
missingCount=$(wc -l $missingList | cut -d' ' -f1)
if [[ $missingCount > 0 ]]; then
  echo "Missing files count: $missingCount"

  if [[ "$listMisingFiles" == "true" ]]; then
    echo "Missing files:"
    cat $missingList
  fi

  if [[ "$reloadMisingFiles" == "true" ]]; then
    echo "Starting to reload missing files..."
    for f in $(cat $missingList); do ./colhub-get-product.sh $f; done
  fi

  if [[ "$keepFiles" == "true" ]]; then
    echo "List in: $missingList"
  fi
fi

