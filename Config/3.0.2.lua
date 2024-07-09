-- XALT 3.0.2 Modfile

-- Setting as sticky to bypass module purge on OOD launch script
add_property("lmod","sticky")


-- Get MMYYYY for XALT 
local currentDate = os.date("*t")
local month = string.format("%02d", currentDate.month)
local year = currentDate.year
local formattedDate = month .. year

-- Filepath used for current configuration of XALT
local base  = "/sw/workload/xalt2/xalt/xalt"  --> Change to match your site!!!
local bin   = pathJoin(base,"bin")
local pythonpath   = pathJoin(base,"site_packages")
local lib_dir = "/lib64"
local record_dir  = "/sw/workload/delta/json"


-- Comma seperated as specified by https://apptainer.org/docs/user/main/bind_paths_and_mounts.html
local apptainer_bind_dir = "/sw/workload/xalt2/xalt/xalt, /sw/workload/delta"

-- Turn on Module Tracking
setenv("XALT_EXECUTABLE_TRACKING",       "yes")

-- Environment variables for XALT to run on a Compute Node
prepend_path{"PATH",          bin, priority="100"}
prepend_path("XALT_DIR",      base)
prepend_path("LD_PRELOAD",    pathJoin(base, "$LIB/libxalt_init.so"))
prepend_path("COMPILER_PATH", bin)

-- XAlT_DATE_TIME creation
setenv("XALT_FILE_PREFIX", pathJoin(record_dir,formattedDate))



-- Variable needed for Python tracking outside a container 
prepend_path("PYTHONPATH",  pythonpath)


-- Variables needed for XALT to get included into containers
prepend_path("APPTAINER_BINDPATH", apptainer_bind_dir)
setenv("APPTAINERENV_LD_PRELOAD", pathJoin(base, lib_dir, "libxalt_init.so"))
setenv("APPTAINERENV_PYTHONPATH", pythonpath)


------------------------------------------------------------
-- Only set this in production not for testing!!!
-- setenv("XALT_SAMPLING",  "yes")

-- Uncomment this to track GPU usage
-- setenv("XALT_GPU_TRACKING",              "yes")

