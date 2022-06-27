#!/bin/sh

#Script 23/06/2022 SJD: Script to move and/backup SRH reports to new location

if [ $# != 3 ]
then
        echo "Usage: <top level www report dir> < dir to move to> <file age>"
        exit
fi
echo "test edit on github direct"
www_dirs=$1
op_dir="$2/$HOSTNAME" #op should ALWAYS be sorted by host to avoid confusion with other hubs in the backup dir
age=$3

good_cnt=0
bad_cnt=0

for dir in `find $www_dirs -maxdepth 1 -mindepth 1 -type d`
do
        for log in `find $dir -mtime +$age -name '*.txt' -print`
        do
                #will omit daily report
                filename=`basename $log`
                dr=`echo $filename | grep -c "daily_report"`
                if [ $dr = 0 ]
                then

                        datestr=`echo $log | sed 's/.*\([0-9]\{2\}\)-\([0-9]\{2\}\)-\([0-9]\{4\}\).*/\3\2\1/'`
                        week=`date -d $datestr +%W`
                        year=`date -d $datestr +%Y`
                        report_type=`basename $dir`
                        target_folder="${op_dir}/${report_type}/${year}/${week}"
                        target_filename="${target_folder}/${filename}"

                        if [ ! -f $target_filename ]
                        then
                                if [ ! -d $target_folder ]
                                then
                                        echo "Creating directory: $target_folder"
                                        mkdir -p $target_folder
                                fi

                                echo "Moving $log to $target_folder"
                                cp $log $target_folder #NOTE - change this to MV once we are satisfied it works properly


                                #check moved file is the same before clearing the original
                                a=`md5sum $log | awk '{print $1}'`
                                b=`md5sum $target_filename | awk '{print $1}'`

                                if [ $a == $b ]
                                then
                                        #rm -f $logfilename
                                        echo "$log md5sums match.  can remove"
                                else
                                        echo "ERROR: Could not remove ${log} as problem with transfer! (md5sums do not match)"
                                fi


                                good_cnt=`expr $good_cnt + 1`

                        else
                                echo "ERROR: Cannot move $log to $target_folder as it already exists!"
                                bad_cnt=`expr $bad_cnt + 1`

                        fi

                        target_folder=""
                        target_filename=""
                fi
        done
done

echo "Moved $good_cnt files and errors with $bad_cnt files"
