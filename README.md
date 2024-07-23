![XALT Logo](https://github.com/xalt/xalt/raw/main/logos/XALT_Sticker.png)

[![Documentation Status](https://readthedocs.org/projects/xalt/badge/?version=latest)](https://xalt.readthedocs.io/en/latest/?badge=latest)
## Synopsis

XALT is a lightweight software tool for any Linux cluster,
workstation, or high-end supercomputer to track executable information
and linkage of static shared and dynamically linked libraries. When
the code is executed, wrappers intercept both GNU linker (ld) to capture
linkage information and environmental variables.

## Creators

Dr. Mark Fahey  
Dr. Robert McLay

## Motivation

We wanted to be able to answer the questions: what software do
researchers actually use on high-end computers, and how successful are
they in their efforts to use it?  With the information that xalt
collects, high-end computer administrators can answer our questions by
tracking continuous job-level information to learn what products
researchers do and do not need.  Drilling down to data driven usage
statistics helps stakeholders conduct business in a more efficient,
effective, and systematic way.


## Original Documentation

Installation and Use of XALT is provided at https://xalt.readthedocs.io website.


# NCSA SPIN Summer 2024 Documentation
This is a fork of XALT for the NCSA. This was developed as a project in the SPIN Summer 2024 cohort by Prakhar Gupta.

## For Users

The XALT modulefile is available in the `/sw/workload/xalt2/module/xalt/3.0.2.lua/`. You can enable XALT on a node by running the following commands on the shell

```
[user@node ~]$ export MODULEPATH=$MODULEPATH:/sw/workload/xalt2/module
[user@node ~]$ module load xalt/3.0.2
```
XALT is deployed as a **sticky** module! So, commands like `module purge` or `module unload xalt` will not get rid of it, unless you use the `--force` flag.  To unload:
```
[user@node ~]$ module --force unload xalt/3.0.2
```
If you want the XALT module to be always available, simply include the changes to modulepath in your `.bashrc`

## For Administrators

### Current Configuration on Delta

XALT is located in `/sw/workload/` on Delta. The source (this repository) is in `/sw/workload/xalt2/xalt_src` and the executables are in `/sw/workload/xalt2/xalt`.

Each build of XALT requires a configuration file. The configuration file is in [Delta_config.py](https://github.com/ScreamingPigeon/xalt/blob/main/Config/Delta_Config.py).

Relevant information on configuring XALT can be found here
- [Downloading XALT and Configuring it for your site](https://xalt.readthedocs.io/en/latest/020_site_configuration.html)
- [Running Configure and building XALT for your site](https://xalt.readthedocs.io/en/latest/050_install_and_test.html) 
- [XALT's Environment Variables](https://xalt.readthedocs.io/en/latest/095_xalt_env_vars.html)

The script used to build xalt on Delta can be found at [`ncsa_build/build_xalt.sh`](https://github.com/ScreamingPigeon/xalt/blob/main/ncsa_build/build_xalt.sh). Running the script to build XALT automatically updates `xalt_src/` from this repository, updates the module file, and finally copies itself into `/sw/workload/xalt2`. 


The important bit is that XALT is configured to dump files into `/sw/workload/delta/json`. The LMOD reverse map it uses to match paths to modules is in `/sw/workload/delta/process_xalt`.

The modulefile further supplements this configuration of XALT in use. On Delta, this modulefile can be found in [`/sw/workload/xalt2/module/`](https://github.com/ScreamingPigeon/xalt/blob/main/ncsa_build/3.0.2.lua).
This modulefile enables XALT to collect information inside containers, track Python imports, etc. Notably, it also overrides the config's file-prefix flag to dump out records in a YYYYMM directory.
So if XALT was used to track an executable in July 2024, relevant records would be dumped out in `/sw/workload/delta/json/202407/`. 

Note: Ensure that the modulefile directory is added to `$MODULEPATH` if you wish to use XALT.

### Record Description

An in-depth explanation on XALT's Record description can be found [here](https://xalt.readthedocs.io/en/latest/120_xalt_json.html).

#### RUN
These records are generated for all ELF executables that get through the filters in our [Delta_config.py](https://github.com/ScreamingPigeon/xalt/blob/main/Config/Delta_Config.py). So tracking does not work on Login nodes.
These RUN records are generated in the following format

> run.<site_name>.<date_time>.<user_name>.<aaa_zzz>.<xalt_run_uuid>.json

The presence of the `aaa` in a record file name indicates that it is a START record, generated during `xalt_initialize()` before `main()` in the user code is called. If there is `zzz` in the record name, then it is an end record -
generated in `myfini()` after a program calls `exit()`. The presence of a start record but no end record for the same `xalt_run_uuid` usually indicates an abnormal exit, possibly due to issues like  job timeouts and segfaults.


#### LINK
These records are generated when a compiler is used on a non-login node. XALT injects a watermark and UUID into the program's ELF header. This allows LINK records to be connected to RUN records through a common UUID - 
granting additional telemetry on the system.

> link.<site_name>.<date_time>.<user_name>.<xalt_run_uuid>.json

These records include information on the compiler used, the location of the built executable, and the static (`.a`) and shared (`.so`) libraries used in compilation. It also contains information about the arguments/flags used for compilation.


#### PKG
These records are generated for Python imports. Each import leads to a separate package record, usually named something like

> pkg.<site_name>.<date_time>.<user_name>.<xalt_run_uuid>.json

These records are generated due to `$PYTHONPATH`, which injects `/sw/workload/xalt2/xalt/xalt/site_packages/sitecustomize.py` into the interpreter. This program, in turn, generates the list of imports and calls one of the XALT executables which
stores this record in `/dev/shm`. These records are then moved to the specified file prefix when `myfini()` is invoked to avoid slowing down user code while it executes. 
However, this leads to issues with evicting these records in the case of a program not exiting normally. This can potentially be bypassed by putting [`epilog/xalt.sh`](https://github.com/ScreamingPigeon/xalt/blob/main/epilog/xalt.sh) in the slurm epilog (epilog functionality not yet verified).
Ensure that this is run BEFORE `/dev/shm` is cleared at the end of the job. Since these incomplete records still have the run_uuid, they can be connected to the start record of a job.

### Debugging
You can turn on debugging statements by exporting `XALT_TRACING=yes` in your shell. Note: XALT will not create debugging statements for `myfini()` when tracking the `lsof` program.


### Python Utilities
XALT can be used to help debug user issues. Once the user loads the XALT module, logs will begin generating in the file-prefix directory (`/sw/workload/delta/json/<YYYYMM>`).

XALT's build comes with a few Python utilities, which can be found in `/sw/workload/xalt2/xalt/xalt/sbin/`. For our purposes, here are the useful python utilities:
- conf_create.py
- createDB.py
- xalt_file_to_db.py
- xalt_scalar_bins_usage_report.py
- xalt_library_usage.py
- xalt_usage_report.py

The rest of the files are either helpers or are relevant to the syslog transmission method. These utilities integrate with a MySQL Database that needs to be configured and running somewhere on the cluster. XALT Documentation recommends setting up a VM with XALT and access to the filesystem to run the Database. XALT Documentation on Database setup can be found [here](https://xalt.readthedocs.io/en/latest/060_setup_db.html). For more information on loading JSON records into the database, please refer to the [docs](https://xalt.readthedocs.io/en/latest/070_loading_json_by_file.html)

The python packages needed to run these utilities are 
- `mysqlclient`
- `getent` / `pygetent`

Note: `pygetent` utilizes the same functionality as `getent`, it is an updated version of the package, made to be compatible with Python3. `getent`'s PyPI package had not been updated since 2013, and `pygetent` has been republished to provide ease of access for installs through pip.

Alternatively, a Python CLI tool was developed to pull relevant records given any of the following information
- USER
- xalt_run_uuid
- slurm job id
- DateTime range

This is available in ['cli_tools/xalt_find_records.py'](https://github.com/ScreamingPigeon/xalt/blob/main/cli_tools/xalt_find_records.py) and works by recursively traversing `/sw/workload/json` looking for records that match the filter, and printing a report as `xalt_report.txt` in the directory it was run. This should be able to help administrators pull information from user jobs. Performance will degrade if there are a large number of records in the directory.

### How does XALT work

A condensed explanation of the key idea behind XALT is available [here](https://github.com/ScreamingPigeon/xalt/blob/main/how_it_works.pdf)

`myinit()`, `myfini()` and the preemptive signal handler are all in [`src/libxalt/xalt_initialize.c`](https://github.com/ScreamingPigeon/xalt/blob/main/src/libxalt/xalt_initialize.c).

### Major Changes

The main changes in this fork are
1. XALT was segfaulting when wrapped around `lsof` with debugging on. This was fixed in XALT 3.0.3, but this was forked from 3.0.2 and had a near-identical fix.
2. This fork of XALT supports creating start records for ALL PROCESSES as opposed to just MPI jobs. This can be achieved by setting `XALT_ALWAYS_CREATE_START=yes` in your environment. This has been included in the modulefile
3. Comments around signal handling in [`src/libxalt/xalt_initialize.c`](https://github.com/ScreamingPigeon/xalt/blob/main/src/libxalt/xalt_initialize.c). 
4. Inclusion of a custom config, build script, modulefile, epilog script, and a python cli-tool


### Miscellaneous Notes

#### Symlinks
##### Pre-Execution Filtering

The XALT filters uses the path of the target used to build the symlink, as opposed to the path of the link itself. For example, if you have the rules
  - KEEP, `/usr/bin/gcc`
  - SKIP, `/sw/*`

and the following file in `/sw/workload/xalt/`
```
lrwxrwxrwx  1 prakhar7      root   12 Jul 23 11:38 gcc -> /usr/bin/gcc

```
XALT uses the `/usr/bin/gcc` path while filtering. 

##### Record Generation
Run Records contain references to the symlink's path
```
  "cmdlineA": ["/sw/workload/xalt2/gcc"],
```

However, in the `UserT` key, we see
```
    "exec_path": "/usr/bin/gcc",
```
Therefore run records capture both paths

#### Profiling

XALT comes with a special build flag `--with-tmpdir=` which allows the user to specify the directory for intermediate logs, as opposed to the default which is `/dev/shm`. Attempting to use $HOME in this flag leads to signifcant slowdowns

Runtime information
- `/dev/shm`: 0.03-0.04ms for a PKG record
- `$HOME`: 0.2-0.3ms for a PKG record

While these seem like small numbers, minimizing the transmission time is important.
Given that, a simple task of activating a conda environment leads to about 300 PKG records, and starting up a jupyter notebook creates 800 PKG records, it is evident that complicated scripts will lead to a lot more records.
These savings scale with thousands of jobs.



#### Signals and SLURM
On the non-preemptible queues, the slurm configuration specifies a gracetime of 30s. This means that slurmd sends a SIGTERM and SIGCONT to the job, waits 30s and then sends a SIGKILL.
This would imply that jobs could take advantage of XALT's signal handling capabilities, and indeed this was the initial motivation for disabling signal forwarding on USR2. However,
it turns out that slurm will send these signals out to ONLY job steps, and not child/forked processes. This, in combination with guaranteed start record creation, led to reverting to the original
signal handling implementation.

If needed, preemptive signal handling can be turned on by setting `XALT_SIGNAL_HANDLER=yes` in your environment


#### Open-OnDemand

Debugging issues for OOD was what revealed the main problem with improper exits(). However, since the SBATCH scripts used on OOD are controlled by Admin, we can ensure
that XALT works the way we want it to here. 

##### Option 1 - Handle Signals?
Assuming that the sbatch script used to launch an OOD service, say Jupyter is something like this 
```
#! /bin/bash
...
#SBATCH --param=xyz

# Get port information 
srun jupyter-server
# OR
jupyter-server
```
if Jupyter is executed as a job step, turning on signal handling in XALT by setting the environment variable `XALT_SIGNAL_HANDLER=yes` should be sufficient.
If Jupyter is not a JOB step, then a trap on the batch shell should be good enough. Using the `#SBATCH --signal=B:signum@time_before_timeout` on the script and setting up a trap to send a TERM to the jupyter job using some bash scripting is good.

Here is an example from when we were using USR2 to preempt XALT.

```
...
#SBATCH --signal=B:12@60
usrhandler(){
    jupyter_process=$(ps xf | grep jupyter-server)
    jupyter_pid="${jupyter_process:0:8}"
    kill -s 12 $jupyter_pid
}
trap usrhandler 12

jupyter-server
...

```



##### Option 2 - Move everything to file-prefix!

If signal management seems too invasive, the trap installed on the bash can simply trigger a copy from `/dev/shm` to the file-prefix. For example, this is very similar to the sample epilog script:
```
#! /bin/bash
#SBATCH --time=00:03:00         # Wall time limit (hh:mm:ss)
#SBATCH --ntasks=1              # Number of tasks (processes)
....
#SBATCH --cpus-per-task=1       # Number of CPU cores per task
#SBATCH --mem=4G                # Total memory for the job (4GB)
#SBATCH --partition=cpu		    # Partition



sighandler(){
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
}

trap sighandler TERM

...

```




### Existing Issues
- The generation of link records is not consistent among different compilers. Possibly due to the order in which $PATH is set. Seems to work with the  `/bin/gcc` and the aocc module. Link records do not generate with the gcc module
- Need to turn on tracking for compilers on login nodes.
- The `$APPTAINER_BINDPATH` variable set in the modulefile interferes with building containers. Builds fail due to lack of a mount point for these directories.
