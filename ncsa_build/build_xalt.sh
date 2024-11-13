#!/usr/bin/bash

# Variables for build. Change as needed
orig_dir=$PWD
base_dir=/sw/workload
src_dir=$base_dir/xalt2/xalt_src
build_dir=$base_dir/xalt2
rmap_dir=$base_dir/delta/process_xalt
json_dir=$base_dir/delta/json
config_file=Config/Delta_Config.py
git_repo=https://github.com/ncsa/xalt
module_name=xalt
module_ver=3.1.1


# Unloading module
echo Unloading XALT module
module --force unload $module_name


# Getting Latest Source
echo "Verifying Directory"
if [ -d "$src_dir" ]; then
        echo Directory exists. Updating now.
        cd $src_dir
        git pull
        cd $orig_dir

else
        echo Directory does not exist
        git clone $git_repo xalt_src

fi

# Setting Source to read and execute
chmod -R a+rx $src_dir

# Configuring XALT now
echo "Configuring XALT"
cd $src_dir
./configure --prefix=$build_dir                 \
--with-config=$config_file                      \
--with-syshostConfig=nth_name:2                 \
--with-transmission=file                        \
--with-xaltFilePrefix=$json_dir                 \
--with-MySQL=no                                 \
--with-cmdlineRecord=no                         \
--with-functionTracking=yes                     \
--with-etcDir=$rmap_dir

# Install
echo "Configuration Complete. Starting Install now"
make install

if [ $? -eq 0 ]; then
        echo "Installation Complete." 
        chmod -R a+rx $build_dir/xalt
        echo "Updating Modulefile from source"
        cp $src_dir/ncsa_build/$module_ver.lua $build_dir/module/xalt/$module_ver.lua
        echo "Add ${base_dir}/module to MODULEPATH to begin using ${module_name}"
        cp $src_dir/ncsa_build/build_xalt.sh $build_dir/build_xalt.sh
        echo "Updating record directory permissions"
        chmod -R a+wx $json_dir

else
    echo "Install Failed"
fi

cd $orig_dir
