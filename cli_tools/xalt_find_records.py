import os
import json
from datetime import datetime, timedelta
root_directory = ""
#root_directory = '/sw/workload/delta/json'

def check_xalt_loaded():
    """
    Check if the XALT module is loaded by checking for XALT_FILE_PREFIX env variable.
    """
    root_directory = os.getenv('XALT_FILE_PREFIX')
    if not root_directory:
        print("Please load the XALT module before using this utility")
        exit()
    else:
        return root_directory

def step1(username, root_dir):
    """
    Process JSON files and collect data.
    
    Args:
    username (str): The username to search for in the files.
    root_dir (str): The root directory to start the search from.
    
    Returns:
    list: List of file paths matching the criteria.
    """
    file_list = []
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file.startswith('run.') and file.endswith('.json') and username in file and (".aaa." in file or '.zzz' in file):
                file_list.append(file_path)
    return file_list

def step2(start_record_paths, start_date, end_date):
    """
    Process JSON data and file paths to incorporate datetime filters.
    
    Args:
    start_record_paths (list): List of file paths to filter.
    start_date (str): The start date for filtering records.
    end_date (str): The end date for filtering records.
    
    Returns:
    list: List of filtered file paths based on date range.
    """
    filtered_paths = []
    if start_date:
        start_date = datetime.strptime(start_date, "%m/%d/%Y") - timedelta(days=1)
    else:
        start_date = None

    if end_date:
        end_date = datetime.strptime(end_date, "%m/%d/%Y") + timedelta(days=1)
    else:
        end_date = None

    for rec_pth in start_record_paths:
        rec_name = rec_pth.split('/')[-1]
        record_date = datetime.strptime(rec_name.split('.')[2][:10], "%Y_%m_%d")

        if start_date is None and end_date is None:
            filtered_paths.append(rec_pth)
        elif start_date is None:
            if record_date <= end_date:
                filtered_paths.append(rec_pth)
        elif end_date is None:
            if start_date <= record_date:
                filtered_paths.append(rec_pth)
        else:
            if start_date <= record_date <= end_date:
                filtered_paths.append(rec_pth)

    return filtered_paths

def step3(record_paths, xalt_run_uuid):
    """
    Filter records by XALT_RUN_UUID.
    
    Args:
    record_paths (list): List of file paths to filter.
    xalt_run_uuid (str): The XALT_RUN_UUID to filter by.
    
    Returns:
    list: List of filtered file paths based on XALT_RUN_UUID.
    """
    filtered_paths = []
    for rec_pth in record_paths:
        record_name = rec_pth.split('/')[-1]
        rec_run_uuid = record_name.split('.')[-2]
        if xalt_run_uuid in rec_run_uuid:
            filtered_paths.append(rec_pth)
    return filtered_paths

def step4(record_data, record_paths, slurm_jid):
    """
    Filter records by Slurm Job ID.
    
    Args:
    record_data (list): List of JSON data to filter.
    record_paths (list): List of file paths corresponding to the JSON data.
    slurm_jid (str): The Slurm Job ID to filter by.
    
    Returns:
    tuple: Filtered JSON data and corresponding file paths.
    """
    filtered_data = []
    filtered_paths = []
    include = slurm_jid == ''

    for i, record in enumerate(record_data):
        if record is None:
            continue

        if include:
            filtered_paths.append(record_paths[i])
            filtered_data.append(record_data[i])
            continue

        userT_jid = record['userT']['job_id']
        envT_jid = record['envT']['SLURM_JOB_ID']
        
        if slurm_jid in userT_jid or slurm_jid in envT_jid:
            filtered_paths.append(record_paths[i])
            filtered_data.append(record_data[i])
            
    return filtered_data, filtered_paths

def process_files(record_paths):
    """
    Process JSON files and extract data.
    
    Args:
    record_paths (list): List of file paths to process.
    
    Returns:
    list: List of extracted JSON data.
    """
    pkg_data_list = []
    for path in record_paths:
        with open(path, 'r') as f:
            try:
                data = json.load(f)
                pkg_data_list.append(data)
            except json.JSONDecodeError as e:
                pkg_data_list.append(None)
                print(f"Failed to open {path}: {e}")
    return pkg_data_list

def find_pkg_records(run_uuid, root_dir):
    """
    Find package records by XALT_RUN_UUID.
    
    Args:
    run_uuid (str): The XALT_RUN_UUID to search for.
    
    Returns:
    list: List of package names and paths.
    """
    pkg_names = []
    pkg_paths = []
    
    root_directory = root_dir 
    for subdir, _, files in os.walk(root_directory):
        for file in files:
            file_path = os.path.join(subdir, file)
            if run_uuid in file_path and file_path.split('/')[-1].startswith('pkg'):
                with open(file_path, 'r') as pkg_file:
                    try:
                        pkg_json = json.load(pkg_file)
                        pkg_names.append(pkg_json['package_name'])
                        pkg_paths.append(pkg_json['package_path'])
                    except json.JSONDecodeError as e:
                        pkg_names.append(None)
                        pkg_paths.append(None)
                        print(f"Error opening {file_path}: {e}")
    
    if not pkg_names or not pkg_paths:
        return pkg_names, pkg_paths
    
    return sorted(set(zip(pkg_names, pkg_paths)), key=lambda x: x[-1])

def display_summary(filtered_data, root_dir):
    """
    Display summary of filtered data.
    
    Args:
    filtered_data (dict): The filtered JSON data.
    filtered_path (str): The file path corresponding to the filtered data.
    """
    with open("./xalt_info.txt", 'w') as log_file:
        log_file.write(f"XALT_RUN_UUID: {filtered_data['userT']['run_uuid']} \n")
        log_file.write(f"Program  ({filtered_data['userT']['exec_type']}) Executed was: {filtered_data['userT']['exec_path']} \n")
        log_file.write(f"Loaded Modules: {filtered_data['envT']['LOADEDMODULES']} \n")
        try:
            log_file.write(f"Slurm Job Id: {filtered_data['envT']['SLURM_JOB_ID']} \n")
        except KeyError:
            pass  # Could be LINK Job?
        log_file.write(f"Job Submitted by {filtered_data['userT']['user']} using account {filtered_data['userT']['account']} \n")

        pkg_info = find_pkg_records(filtered_data['userT']['run_uuid'], root_dir)

        if pkg_info:
            log_file.write("The following packages were used: \n")
            for row in pkg_info:
                log_file.write(f"   {row[0]} : {row[1]} \n")

if __name__ == '__main__':
    
    print("Enter your search parameters. Note: this utility searches for records in the XALT_FILE_PREFIX directory. Please override by specifying search directory \n")

    root_dir = input("Search directory (leave empty to use XALT_FILE_PREFIX): ")
    if root_dir == "" or root_dir is None:
        root_dir = check_xalt_loaded();

    username = None
    while username is None:
        username = input("Enter username: ")
  
    start_date = input("Start date (inclusive - MM/DD/YYYY format): ")
    end_date = input("End date (inclusive - MM/DD/YYYY format): ")
    slurm_jid = input("Enter Slurm Job ID: ")
    xalt_run_uuid = input("Enter XALT RUN UUID: ")
   
    # Step 1: Find matching xalt_run_uuids for username start_records
    start_record_paths = step1(username, root_dir)
    
    # Step 2: Filter records between start and end date
    record_paths = step2(start_record_paths, start_date, end_date)

    # Step 3: Filter with xalt_run_uuid
    if xalt_run_uuid:
        record_paths = step3(record_paths, xalt_run_uuid)
   
    print("Records filtered. Extracting JSON now...")
    record_data = process_files(record_paths)

    # Step 4: Filter with Slurm Job ID 
    filtered_data, filtered_paths = step4(record_data, record_paths, slurm_jid)
    if not filtered_paths:
        print("No matching records found")
        exit()

    print(f"There are {len(filtered_data)} records matching your parameters.")
    for i in range(len(filtered_paths)):
        print(i, ":", filtered_paths[i])

    record_index = int(input("Select a record for a report to be generated: "))

    display_summary(filtered_data[record_index], root_dir) 

