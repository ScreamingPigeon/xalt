#! /bin/bash
# Running XALT cleanup inside the epilog

# Get YYYYMM
date=$(date '+%Y%m');

# Directories used
dir_shm=/dev/shm/
xalt_record_dir=/sw/workload/delta/json/$date
xalt_pkg_records=$(find $dir_shm -type d -name 'XALT_pkg_*')

for pkg_record in $xalt_pkg_records
do
        # Create a YYYYMM directory if it doesn't exist 
        if [ ! -d "$xalt_record_dir" ]; then
          mkdir $xalt_record_dir
        fi
        pkg_record_base=$(basename $pkg_record)

        # Move from /dev/shm to transmission location
        cp -r $pkg_record $xalt_record_dir/$pkg_record_base
done  
