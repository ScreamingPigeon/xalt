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


## NCSA SPIN Summer 2024 Documentation
This is a fork of XALT for the NCSA. This was developed as a project in the SPIN Summer 2024 cohort by Prakhar Gupta.

### Current Configuration on Delta

XALT is currently located in `/sw/workload/` on Delta. The source (this repository) is in `/sw/workload/xalt2/xalt_src` and the executables are in `/sw/workload/xalt2/xalt`.

Each build of XALT requires a configuration file. The configuration file is [Delta_config.py](https://github.com/ScreamingPigeon/xalt/blob/main/Config/Delta_Config.py).

Relevant information on configuring XALT can be found 
- [Downloading XALT and Configuring it for your site](https://xalt.readthedocs.io/en/latest/020_site_configuration.html)
- [Running Configure and building XALT for your site](https://xalt.readthedocs.io/en/latest/050_install_and_test.html) 
- [XALT's Environment Variables](https://xalt.readthedocs.io/en/latest/095_xalt_env_vars.html)

The script used to build xalt on Delta can be found at [`ncsa_build/build_xalt.sh`](https://github.com/ScreamingPigeon/xalt/blob/main/ncsa_build/build_xalt.sh).
The important bit is that XALT is configured to dump files into `/sw/workload/delta/json`. The LMOD reverse map it uses to match paths to modules is in `/sw/workload/delta/process_xalt`.

This configuration of XALT is further supplemented by the modulefile in use. On Delta, this modulefile can be found in [`/sw/workload/xalt2/module/`](https://github.com/ScreamingPigeon/xalt/blob/main/ncsa_build/3.0.2.lua).
This modulefile enables XALT to collect information inside containers, track python imports, etc. Notably, it also overrides the config's file-prefix flag to dump out records in a YYYYMM directory.
So if XALT was used to track an executable in July 2024, relevant records will be dumped out in `/sw/workload/delta/json/202407/`. 

Note: Ensure that the modulefile direcory is added to `$MODULEPATH` if you wish to use XALT.

#### Record Description

##### RUN
These records are generated for all ELF executables that get through the filters in our [Delta_config.py](https://github.com/ScreamingPigeon/xalt/blob/main/Config/Delta_Config.py). So tracking does not work on Login nodes.
These RUN records are generated in the followin format
    run.<hostname>.<YYYY>_<MM>_<DD>_<HH>_<mm>_<ssss>_<msmsmsms>.<user>.<aaa_zzz>.<xalt_run_uuid>.json
The presence of the aaa in a record file name indicates that it is a START record, generated during `xalt_initialize()` before `main()` in user code is called. If there is `zzz` in the record name, then it is an end record -
generated in `myfini()` after a program calls `exit()`. The presence of a start record but no end record for the same `xalt_run_uuid` usually indicates abnormal exit, possibly due to issues like  job-timeouts and segfaults.


##### LINK
These records are generated when a compiler is used on a non-login node. XALT injects a watermark and UUID in the ELF header for the program. This allows LINK records to be connected to RUN records through a common UUID - 
granting additional telemetry on the system.

##### PKG
These records are generated for python imports. Each import leads to a seperate package record, usually named something like
    pkg.<hostname>.<datetime>.<user>.<xalt_run_uuid>.<*>.json
These records are generated due to the presence of `$PYTHONPATH`, which injects `/sw/workload/xalt2/xalt/xalt/site_packages/sitecustomize.py` into the interpreter. This program in turn generates the list of imports and calls one of the XALT executables which
stores this record in `/dev/shm`. These records are then moved to the specified file-prefix when `myfini()` is invoked in order to avoid slowing down user code while it executes. 
However, this leads to issues with evicting these records in the case of a program not exiting normally. This can be bypassed by putting [`epilog/xalt.sh`](https://github.com/ScreamingPigeon/xalt/blob/main/epilog/xalt.sh) in the slurm epilog.
Ensure that this is run BEFORE `/dev/shm` is cleared at the end of the job. Since these incomplete records still have the run_uuid, they can be connected to the start record of a job.

#### Debugging
You can turn on debugging statements by exporting `XALT_TRACING=yes` in the shell you're using.


### Python CLI Tool
XALT can be used to help debug user issues. Once the user loads the XALT module, logs will begin generating in the file-prefix directory. A python CLI tool was developed to pull relevant records given any of the following information
- USER
- xalt_run_uuid
- slurm job id
- datetime range

The python tool also requires the path of the file-prefix directory where these records are available. The user running this program must have read access to the file-prefix directory and all records in there.

### How does XALT work

A condensed explanation of the key idea behind XALT s available [here](https://github.com/ScreamingPigeon/xalt/blob/main/how_it_works.pdf)

`myinit()`, `myfini()` and the preemptive signal handler are all in [`src/libxalt/xalt_initialize.c`](https://github.com/ScreamingPigeon/xalt/blob/main/src/libxalt/xalt_initialize.c).

### Major Changes

The main changes in this fork are
1. XALT was segfaulting when wrapped around `lsof` with debugging on. This was fixed in XALT 3.0.3, but this was forked from 3.0.2 and has a near-identical fix.
2. This fork of XALT supports creating start records for ALL PROCESSES as opposed to just MPI jobs. This can be achieved by setting `XALT_ALWAYS_CREATE_START=yes` in your environment. This has been included in the modulefile
3. Comments around signal handling in [`src/libxalt/xalt_initialize.c`](https://github.com/ScreamingPigeon/xalt/blob/main/src/libxalt/xalt_initialize.c). 
4. Inclusion of a custom config, build script, modulefile, epilog script, and a python cli-tool


### Miscellaneous Notes

#### Profiling

XALT comes with a special build flag `--with-tmpdir=` which allows the user to specify the directory for intermediate logs, as opposed to the default which is `/dev/shm`. Attempting to use $HOME in this flag leads to signifcant slowdowns

Runtime information
- `/dev/shm`: 0.03-0.04ms for a PKG record
- `$HOME`: 0.2-0.3ms for a PKG record

While these seem like small numbers, minimizing the transmission time is important.
Given that a simple task of activating a conda environment leads to about 300 PKG records, and starting up a jupyter notebook creates 800 PKG records.
These are fairly simple 'toy' examples, but even with just a 1000 PKG records, the savings scale when using /dev/shm



#### Signals and SLURM
On the non-preemptible queueus the slurm configuration specifies a gracetime of 30s. This means that slurmd sends a SIGTERM and SIGCONT to the job, waits 30s and then sends a SIGKILL.
This would imply that jobs could take advantage of XALT's signal handling capabilities, and indeed this was the initial motivation for disabling signal forwarding on USR2. However,
it turns out that slurm will send these signals out to ONLY job steps, and not child/forked processes. This, in combinatino with guaranteed start record creation led to reverting to the original
signal handling implementation. Running something in the SLURM epilog is almost a certainly better alternative.












