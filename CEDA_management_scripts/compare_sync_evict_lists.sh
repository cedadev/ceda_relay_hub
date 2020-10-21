#!/bin/sh

#wrapper script to just output common lines between two file lists

if [ $# != 2 ]
then
	echo "Usage: <sync list> <evicted list>"
	exit
fi

cat $1 | xargs -i grep {} $2 | sort -u
