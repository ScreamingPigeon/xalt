import os
import json
import mysql.connector
from mysql.connector import Error

# Database credentials
db_host = 'localhost'
db_user = 'xalt'
db_password = 'xalt'
db_name = 'xalt'


root_directory = '/sw/workload/delta/json'



# Function to process JSON files and collect data

def process_files(root_dir):
    pkg_data_list = []
    run_start_data_list = []
    run_end_data_list = []

    for subdir, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            if file.startswith('pkg.') and file.endswith('.json'):
                with open(file_path, 'r') as f:
                    try:
                        data = json.load(f)
                        pkg_data_list.append(data)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for file {file_path}: {e}")
            
            elif file.startswith('run.') and file.endswith('.json'):
                if '.aaa.' in file:
                    with open(file_path, 'r') as f:
                        try:
                            data = json.load(f)
                            run_start_data_list.append(data)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON for file {file_path}: {e}")
                elif '.zzz.' in file:
                    with open(file_path, 'r') as f:
                        try:
                            data = json.load(f)
                            run_end_data_list.append(data)
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON for file {file_path}: {e}")
    
    return pkg_data_list, run_start_data_list, run_end_data_list


# Function to insert data into MySQL database
def insert_into_db(connection, cursor, table, data):
    if table == 'pkg':
        insert_query = '''
        INSERT INTO pkg (crc, program, xalt_run_uuid, package_version, package_name, package_path ) 
        VALUES (%s, %s, %s, %s, %s, %s )
        '''
    elif table == 'run_start':
        insert_query = '''
        INSERT INTO run_start (run_uuid, syshost, exec_path, exec_type, cwd, currentEpoch, start_date, user, execModify, scheduler, account, job_id, queue, submit_host, start_time, end_time, run_time, probability, num_tasks, num_gpus, exec_epoch, num_threads, num_cores, num_nodes, xaltLinkT, XALT_measureT, XALT_qaT) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
    elif table == 'run_end':
        insert_query = '''
        INSERT INTO run_end (run_uuid, syshost, exec_path, exec_type, cwd, currentEpoch, start_date, user, execModify, scheduler, account, job_id, queue, submit_host, start_time, end_time, run_time, probability, num_tasks, num_gpus, exec_epoch, num_threads, num_cores, num_nodes, xaltLinkT, XALT_measureT, XALT_qaT) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
    
    for record in data:
        if table == 'pkg':
            values = (
                record.get('crc'),
                record.get('program'),
                record.get('xalt_run_uuid'),
                record.get('package_version'),
                record.get('package_name'),
                record.get('package_path'),
            )
        elif table == 'run_start':
            values = (
                record['userT'].get('run_uuid'),
                record['userT'].get('syshost'),
                record['userT'].get('exec_path'),
                record['userT'].get('exec_type'),
                record['userT'].get('cwd'),
                record['userT'].get('currentEpoch'),
                record['userT'].get('start_date'),
                record['userT'].get('user'),
                record['userT'].get('execModify'),
                record['userT'].get('scheduler'),
                record['userT'].get('account'),
                record['userT'].get('job_id'),
                record['userT'].get('queue'),
                record['userT'].get('submit_host'),
                record['userDT'].get('start_time'),
                record['userDT'].get('end_time'),
                record['userDT'].get('run_time'),
                record['userDT'].get('probability'),
                record['userDT'].get('num_tasks'),
                record['userDT'].get('num_gpus'),
                record['userDT'].get('exec_epoch'),
                record['userDT'].get('num_threads'),
                record['userDT'].get('num_cores'),
                record['userDT'].get('num_nodes'),
                json.dumps(record.get('xaltLinkT', {})),
                json.dumps(record.get('XALT_measureT', {})),
                json.dumps(record.get('XALT_qaT', {}))
            )
        elif table == 'run_end':
            values = (
                record['userT'].get('run_uuid'),
                record['userT'].get('syshost'),
                record['userT'].get('exec_path'),
                record['userT'].get('exec_type'),
                record['userT'].get('cwd'),
                record['userT'].get('currentEpoch'),
                record['userT'].get('start_date'),
                record['userT'].get('user'),
                record['userT'].get('execModify'),
                record['userT'].get('scheduler'),
                record['userT'].get('account'),
                record['userT'].get('job_id'),
                record['userT'].get('queue'),
                record['userT'].get('submit_host'),
                record['userDT'].get('start_time'),
                record['userDT'].get('end_time'),
                record['userDT'].get('run_time'),
                record['userDT'].get('probability'),
                record['userDT'].get('num_tasks'),
                record['userDT'].get('num_gpus'),
                record['userDT'].get('exec_epoch'),
                record['userDT'].get('num_threads'),
                record['userDT'].get('num_cores'),
                record['userDT'].get('num_nodes'),
                json.dumps(record.get('xaltLinkT', {})),
                json.dumps(record.get('XALT_measureT', {})),
                json.dumps(record.get('XALT_qaT', {}))
            )


        cursor.execute(insert_query, values)

    connection.commit()

# Main function
if __name__ == '__main__':

    # Process JSON files and collect data
    pkg_data_list, run_start_data_list, run_end_data_list  = process_files(root_directory)

    try:
        # Connect to the database
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )

        if connection.is_connected():
            cursor = connection.cursor()

            insert_into_db(connection, cursor, 'run_start', run_start_data_list)
            insert_into_db(connection, cursor, 'run_end', run_end_data_list) 
            insert_into_db(connection, cursor, 'pkg', pkg_data_list)


            print("Data has been inserted successfully")

    except Error as e:
        print(f"Error: {e}")

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

