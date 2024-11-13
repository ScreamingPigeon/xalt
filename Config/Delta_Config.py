# This is the config file for specifying tables necessary to configure XALT:

# The patterns listed here are the hosts that can track executable with XALT.
# Typical usage is that compute nodes track executable with XALT while login
# nodes do not.

import sys

# Note that linking an executable is everywhere and is independent of
# hostname_patterns

hostname_patterns = [
  ['KEEP', r'cn[0-1][0-9][0-9]\..*'], # compute nodes
  ['KEEP', r'gpu[a-b][0-1][0-9][0-9]\..*'], # gpu nodes type a and b
  ['KEEP', r'gpuc0[0-6]\..*'], # gpu nodes type c
  ['KEEP', r'gpud0[0-6]\..*'], # gpu nodes type d 
  ['SKIP', r'dt-login0[0-5]\..*'], #track login nodes for debugging
  ]

#------------------------------------------------------------
# This "table" is use to filter executables by their path
# The value on the left is either KEEP or SKIP.  If the value
# is KEEP then if the path matches the regular expression then
# the executable is acceptable as far as the path test goes.
# If the value on the left is SKIP then if the path matches
# the regular expression then executable is not acceptable so
# no XALT tracking is done for that path.

# This "table" is used to generate a flex routine that processes
# the paths. So the regular express must follow flex rules.
# In particular, in order to match the pattern must match the whole path
# No partial matches allowed.  Also do not use $ to match the
# end of the string.  Finally slash is a special character and must
# be quoted with a backslash.

# The path are conceptionally matched from the first regular
# expression to the last.  Once a match is found no other later
# matches are checked. The upshot of this is that if you want to
# track say /usr/bin/ddt, but ignore everything in /usr, then keep
# /usr/bin/ddt first and skip /usr/.* after.

# If a path does not match any patterns it is marked as KEEP.

# Programs like R, MATLAB and python* are marked as PKGS.  These programs
# can optionally track the internal "import" that are used.

path_patterns = [
    # mark anything with R, matlab, or python/conda in path for PKG tracking
    ['SKIP',  r'.*\/bin\/pip[0-9]'],
    ['PKGS',  r'.*\/r*'],
    ['PKGS',  r'.*\/matlab*'],
    ['PKGS',  r'.*\/anaconda*'],
    ['PKGS',  r'.*\/python[0-9.]*'],
    ['PKGS',  r'.*\/python-*'],
    ['PKGS',  r'\/usr\/libexec\/.*-python[0-9.]*'],
    # track programs run in user directories
    ['KEEP',  r'^\/u\/*'],
    # track module usage
    ['KEEP',  r'^\/sw\/spack\/.*'],
    ['KEEP',  r'^\/sw\/external\/.*'],
    # track default programs in /usr/bin
    ['KEEP',  r'^\/usr\/bin\/apptainer*'],
    ['KEEP',  r'^\/usr\/bin\/c?make*'],
    ['KEEP',  r'^\/usr\/bin\/gcc*'],
    ['KEEP',  r'^\/usr\/bin\/gfortran*'],
    ['KEEP',  r'^\/usr\/bin\/go*'],
    ['KEEP',  r'^\/usr\/bin\/g++*'],
    ['KEEP',  r'^\/usr\/bin\/pip*'],
    ['KEEP',  r'^\/usr\/local\/*'],
    ['KEEP',  r'^\/usr\/bin\/srun'],
    ['KEEP',  r'^\/usr\/bin\/salloc'],
    # other user spaces that might hold executables
    ['KEEP', r'^\/scratch\/*'],
    ['KEEP', r'^\/delta\/scratch\/*'],
    ['KEEP', r'^\/projects\/*'],
    # root directories that do not need to be tracked
    ['SKIP', r'^\/usr\/.*'],
    ['SKIP', r'^\/boot\/.*'], 
    ['SKIP', r'^\/dev\/.*'],
    ['SKIP', r'^\/delta\/.*'],
    ['SKIP', r'^\/etc\/.*'],
    ['SKIP', r'^\/ime\/.*'],
    ['SKIP', r'^\/install\/.*'],
    ['SKIP', r'^\/lib\/.*'],
    ['SKIP', r'^\/lib64\/.*'],
    ['SKIP', r'^\/media\/.*'],
    ['SKIP', r'^\/mnt\/.*'],
    ['SKIP', r'^\/opt\/.*'], # double check this!
    ['SKIP', r'^\/proc\/.*'],
    ['SKIP', r'^\/root\/.*'],
    ['SKIP', r'^\/run\/.*'],
    ['SKIP', r'^\/sbin\/.*'],
    ['SKIP', r'^\/srv\/.*'],
    ['SKIP', r'^\/sw\/.*'],
    ['SKIP', r'^\/sys\/.*'],
    ['SKIP', r'^\/taiga\/.*'], # double check here
    ['SKIP', r'^\/tmp\/.*'],
    ['SKIP', r'^\/var\/.*'],
    ['SKIP', r'^\/xcatpost\/.*'],
    ['SKIP', r'^\/bin\/.*']
   ]

#------------------------------------------------------------
# XALT samples almost all  executions (both MPI and scalar) 
# based on this table below.  Note that an MPI execution is where
# the number of tasks is greater than 1.  There is no check to
# see if there are MPI libraries in the executable.  Note that
# the number of tasks are MPI tasks not threads.

# Any time there are a number of short rapid executions these
# have to be sampled. However, there are MPI executions with large
# number of tasks that are always recorded.  This is to allow the
# tracking of long running MPI tasks that never produce an end
# record. By default MPI_ALWAYS_RECORD = 1.  Namely that all MPI 
# tasks are recorded.

MPI_ALWAYS_RECORD = 128

#------------------------------------------------------------
# The array of array used by interval_array has the following
# structure:
#
#   interval_array = [
#                     [ t_0,     probability_0],
#                     [ t_1,     probability_1],
#                     ...
#                     [ t_n,     probability_n],
#                     [ 1.0e308, 1.0],
#
#
# The first number is the left edge of the time range.  The
# second number is the probability of being sampled. Where a
# probability of 1.0 means a 100% chance of being recorded and a
# value of 0.01 means a 1% chance of being recorded.
#
# So a table that looks like this:
#     interval_array = [
#                       [ 0.0,                0.0001 ],
#                       [ 300.0,              0.01   ],
#                       [ 600.0,              1.0    ],
#                       [ sys.float_info.max, 1.0    ]
#     ]
#
# would say that program with execution time that is between
# 0.0 and 300.0 seconds has a 0.01% chance of being recorded.
# Execution times between 300.0 and 600.0 seconds have a 1%
# chance of being recorded and and programs that take longer
# than 600 seconds will always be recorded.
#
# The absolute minimum table would look like:
#
#     interval_array = [
#                       [ 0.0,                1.0 ],
#                       [ sys.float_info.max, 1.0 ]
#     ]
#
# which says to record every scalar (non-mpi) program no matter
# the execution time.
#
# Note that scalar execution only uses this table IFF
# $XALT_SAMPLING equals yes


interval_array = [
    [ 0.0,                    1.0   ],
    [ 600.0,                  0.05  ],                      # 10 min 
    [ 1800.0,                 0.1   ],                      # 30 min
    [ 7200.0,                 1.0   ],                      # 2 hours
    [ sys.float_info.max,     1.0   ]                       # End of time
]


#------------------------------------------------------------
# Sites can also define a different sampling specification
# for mpi programs different from interval_array.  If no
# mpi_interval_array is given then the interval_array is used
# for both scalar and mpi programs.

mpi_interval_array = [
    [    0.0,              1.0    ],
    [  600.0,              0.10   ],                        # 10 min
    [  900.0,              0.2    ],                        # 15 min
    [ 1800.0,              1.0    ],                        # 2 hours
    [ sys.float_info.max,  1.0    ]                         # End of time
]



#------------------------------------------------------------
# XALT filter environment variables.  Those variables
# which pass through the filter are save in an SQL table that is
# searchable via sql commands.  The environment variables are passed
# to this filter routine as:
#
#      env_key=env_value
#
# So the regular expression patterns must match the whole string.


# The value on the left is either KEEP or SKIP.  If the value
# is KEEP then if the environment string matches the regular
# expression then the variable is stored. If the value on the left
# is SKIP then if the variable matches it is not stored.

# Order of the list matters.  The first match is used even if a
# later pattern would also match.  The upshot is that special pattern
# matches should appear first and general ones later.

# If the environment string does not match any pattern then it is
# marked as SKIP.

# TODO - modify these
env_patterns = [
    [ 'KEEP', r'.*' ], # keep all environment variables
  ]

#------------------------------------------------------------
# Python pattern for python package tracking

# Note that sys, os, re, and subprocess can not be tracked due to the way that python tracking works.
# TODO modify these paths
python_pkg_patterns = [
  { 'k_s' : 'SKIP', 'kind' : 'name', 'patt' : r"^_"                  },  # SKIP names that start with a underscore
  { 'k_s' : 'SKIP', 'kind' : 'name', 'patt' : r".*\."                },  # SKIP all names that are divided with periods: a.b.
  { 'k_s' : 'SKIP', 'kind' : 'name', 'patt' : r"^\/sw\/external\/python\/anaconda3_.*"}, # Skip anaconda3 builtins 
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r".*conda\/.*"          },  # KEEP all packages installed by users
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r".*\/site-packages\/.*" },  # KEEP all site-packages 
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r"^\/delta/scratch\/.*"  },  # KEEP all packages the system project directories
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r"^\/scratch\/.*"        },  # KEEP all packages the system scratch directories
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r"^\/projects\/.*"       },  # KEEP all packages the system project directories
  { 'k_s' : 'KEEP', 'kind' : 'path', 'patt' : r"^\/u\/.*"            },  # KEEP all packages installed by users
  { 'k_s' : 'SKIP', 'kind' : 'path', 'patt' : r"^\/opt"               },  # SKIP all python packages in /opt except for ones in .*/site-packages/
  { 'k_s' : 'SKIP', 'kind' : 'path', 'patt' : r"^\/home"              },  # SKIP all other packages in user locations
  { 'k_s' : 'SKIP', 'kind' : 'path', 'patt' : r"^\/work"              },  # SKIP all other packages in user locations
  { 'k_s' : 'SKIP', 'kind' : 'path', 'patt' : r"^[^/]"               }  # SKIP all built-in packages

]
