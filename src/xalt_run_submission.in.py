# -*- python -*-
#
# Git Version: @git@

#-----------------------------------------------------------------------
# XALT: A tool that tracks users jobs and environments on a cluster.
# Copyright (C) 2013-2014 University of Texas at Austin
# Copyright (C) 2013-2014 University of Tennessee
# 
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation; either version 2.1 of 
# the License, or (at your option) any later version. 
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser  General Public License for more details. 
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free
# Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307 USA
#-----------------------------------------------------------------------

from __future__ import print_function
import os, re, sys

dirNm, execName = os.path.split(sys.argv[0])
sys.path.insert(1,os.path.abspath(os.path.join(dirNm, "../libexec")))
sys.path.insert(1,os.path.realpath(os.path.join(dirNm, "../site")))

from xalt_util                 import capture, which, config_logger
from xalt_transmission_factory import XALT_transmission_factory
from xalt_global               import *

import subprocess, time, socket, json, argparse, platform

logger = config_logger()

def syshost():
  """
  Find a default system host name.  Return 2nd name after the dot, unless there is only one, then return first name.
  """
  hostA = platform.node().split('.')
  idx = 1 
  if (len(hostA) < 2):
    idx = 0
  return hostA[idx]

class CmdLineOptions(object):
  """ Command line Options class """

  def __init__(self):
    """ Empty Ctor """
    pass
  
  def execute(self):
    """ Specify command line arguments and parse the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--start",   dest='startTime', action="store", type=float, default="0.0", help="start time")
    parser.add_argument("--end",     dest='endTime',   action="store", type=float, default="0.0", help="end time")
    parser.add_argument("--fn",      dest='resultFn',  action="store", default = "/dev/null",     help="resultFn")
    parser.add_argument("--ntasks",  dest='ntasks',    action="store", default = "-1",            help="number of mpi tasks")
    parser.add_argument("--syshost", dest='syshost',   action="store", default = syshost(),       help="system host name")
    parser.add_argument("--run_uuid",dest='run_uuid',  action="store", default = None,            help="run uuid")
    parser.add_argument("exec_prog", nargs='+',        help="user program")

    args = parser.parse_args()
    
    return args
    
keyPat    = re.compile(r'.*<(.*)>.*')
shFuncPat = re.compile(r'^\(\) *{')

class ExtractXALT(object):
  """
  This class extracts the XALT scribe placed in the program or shared library.
  """
  def __init__(self, cmd):
    """
    Parse the input path for the xalt record.  If it exists extract the
    key value pairs and store in a table.

    @param cmd: the path to the program or shared library that has (or could have) an XALT record.
    """
    outStr  = capture(["objdump", "-s", "-j", ".xalt", cmd])
    self.__fieldT = {}
    if (not outStr.find("Contents of section .xalt:") != -1):
      return 
    
    outputA = outStr.split('\n')
    outputA.pop(0)
    outputA.pop(0)
    outputA.pop(0)
    outputA.pop(0)
  
    sA = []
    for line in outputA:
      split = line.split()
      if (len(split) > 0):
        sA.append(split[-1])
    s = "".join(sA)
  
    xaltA   = re.split('%%', s)
  
    fieldT = {}

    N = len(xaltA)
    idx = -1
    while (True):
      idx  = idx + 1
      line = xaltA[idx]
      if (line.find("XALT_Link_Info_End") != -1):
        break
      m = keyPat.search(line)
      if (m):
        key   = m.group(1)
        idx   = idx + 1
        value = xaltA[idx].replace("_%_%_"," ")
        fieldT[key] = value
    
    self.__fieldT = fieldT 

  def xaltRecordT(self):
    """ Return the XALT values found in cmd. """
    return self.__fieldT


class UserEnvT(object):
  """ Class to extract important values from the environment """
  def __init__(self, args, userExec):
    """
    Ctor to construct the important user env values and store them in userT.

    @param args:     The parsed command line arguments.
    @param userExec: the path to the user executable.
    """
    ltime                 = time.time()
    userT                 = {}
    userT['cwd']          = os.getcwd()
    userT['syshost']      = args.syshost
    userT['run_uuid']     = args.run_uuid
    userT['num_threads']  = int(os.environ.get("OMP_NUM_THREADS","0"))
    userT['user']         = os.environ.get("USER","unknown")
    userT['num_tasks']    = args.ntasks
    userT['start_date']   = time.strftime("%c",time.localtime(args.startTime))
    userT['start_time']   = args.startTime
    userT['currentEpoch'] = ltime
    userT['end_time']     = args.endTime
    userT['run_time']     = max(0, args.endTime - args.startTime)
    userT['exec_path']    = userExec.execName()
    userT['exec_type']    = userExec.execType()
    userT['exec_epoch']   = userExec.execEpoch()
    userT['execModify']   = userExec.execModify()

    self.__userT = userT
    
  def userT(self):
    """ return the constructed user table. """
    return self.__userT

class UserExec(object):
  """
  Find all about the user's executable.
  """
  def __init__(self, exec_progA):
    """
    Find the user's executable by walking the command line
    and skipping the executables name in ignoreT.  Then find
    the full path to the executable.  Finally find the shared
    libraries if there and get the hash time.

    @param exec_progA: the command line after the mpirun type
    arguments have been removed.
    """
    ignoreT = {
      'env'              : True,
      'time'             : True,
    }
    cmd = None
    for prog in exec_progA:
      bare = os.path.basename(prog)
      if (not (bare in ignoreT)):
        cmd = prog
        break

    self.__execType = None
    self.__execName = which(cmd)
    self.__libA     = []
    if (self.__execName):
      outStr = capture(["file", self.__execName])
      if (outStr.find("script") > 0 or outStr.find("text") > 0):
        self.__execType = "script"
      else:
        self.__execType = "binary"
        ldd             = capture(["ldd", self.__execName])
        self.__libA     = self.__parseLDD(ldd)

      info = os.stat(self.__execName)
      self.__modify = info.st_mtime
      self.__hash   = self.__computeHash(self.__execName)


  def execName(self):
    """ Return the name of the executable """
    return self.__execName

  def execType(self):
    """ Return the executable type: binary or script. """
    return self.__execType

  def execEpoch(self):
    """ Return the executables modify time in epoch time."""
    return self.__modify

  def execModify(self):
    """ Return the modify date time string. """
    return time.strftime("%c",time.localtime(self.__modify))

  def libA(self):
    """ Return the array of shared libraries for this executable. """
    return self.__libA

  def hash(self):
    """ Return the sha1sum of the executable. """
    return self.__hash

  def __computeHash(self, cmd):
    """ Compute the sha1sum of the executable. """
    fieldA = capture(["sha1sum", cmd]).split()
    return fieldA[0]

  def __parseLDD(self,ldd):
    """ Return the list of shared libraries with their sha1sum. """
    if (not ldd or ldd.find("not a dynamic executable") > 0):
      return []

    lineA = ldd.split('\n')

    libA = []
    d    = {}
    for line in lineA:
      fieldA = line.split()
      N      = len(fieldA)
      
      if (N < 1):
        break
      elif (N == 4):
        lib = fieldA[2]
      else:
        lib = fieldA[0]
      lib = os.path.realpath(lib)
      d[lib] = True
    
    libA = d.keys()
    libA = sorted(libA)
    
    libB = []
    for lib in libA:
      hash_line = capture(['sha1sum', lib])
      if (hash_line.find("No such file or directory") != -1):
        v = "unknown"
      else:
        v = hash_line.split()[0]

      libB.append([lib, v])
      

    return libB
    
class EnvT(object):
  """ Capture the user's environment.  Remove some variables."""
  def __init__(self):
    """ Save the users environment. """
    self.__envT = self.__reportUserEnv()
  def envT(self):
    """ Return the user environment. """
    return self.__envT
  def __reportUserEnv(self):
    """
    Walk the users environment and save every thing except for a few env. vars.
    Also remove any exported shell functions.
    """

    # blacklist of env vars not to track
    ignoreKeyA = [
      re.compile(r'^HIST.*$'),
      re.compile(r'^LESS_TERMCAP_.*$'),
      re.compile(r'^COLORTERM$'),
      re.compile(r'^LS_.*$'),
      re.compile(r'^LANG$'),
      re.compile(r'^LESS.*$'),
      re.compile(r'^MORE$'),
      re.compile(r'^PAGER$'),
      re.compile(r'^NNTPSERVER$'),
      re.compile(r'^NLSPATH$'),
      re.compile(r'^MAIL$'),
      re.compile(r'^_ModuleTable.*$'),
      re.compile(r'^_SettargTable.*$'),
      re.compile(r'^SSH_.*$'),
      re.compile(r'^XDG_.*$'),
      re.compile(r'^PS1$'),
    ]

    envT = {}
    for k in os.environ:
      v = os.environ[k]
      keep = True
      for pat in ignoreKeyA:
        m = pat.search(k)
        if (m):
          keep = False
          break
      m = shFuncPat.search(v)
      if (m):
        keep = False
      if (keep):
        envT[k] = v
    return envT
  

def main():
  """
  Write the environment, XALT info from executable and use the
  transmission factory to save it.
  """

  try:
    # parse command line options:
    args = CmdLineOptions().execute()

    userExec = UserExec(args.exec_prog)
    if (not userExec.execName()):
      return

    userT    = UserEnvT(args, userExec).userT()
  
    submitT              = {}
    submitT['userT']     = userT
    submitT['xaltLinkT'] = ExtractXALT(userExec.execName()).xaltRecordT()
    submitT['libA']      = userExec.libA()
    submitT['envT']      = EnvT().envT()
    submitT['hash_id']   = userExec.hash()
  
    xfer  = XALT_transmission_factory.build(XALT_TRANSMISSION_STYLE,
                                            args.syshost, "run", args.resultFn)
    xfer.save(submitT)
  except Exception as e:
    print("XALT_EXCEPTION(xalt_run_submission.py): ",e)
    logger.exception("XALT_EXCEPTION:xalt_run_submission.py")


if ( __name__ == '__main__'): main()
