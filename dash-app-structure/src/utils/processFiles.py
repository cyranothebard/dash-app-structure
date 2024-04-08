import os
import shutil
import time
import pandas as pd
import logging

def monitor_input_directory(input_dir, archived_dir, data_table):
    while True:
        
        file_list = os.listdir(input_dir)
        # Sort the file list based on modification time (oldest first)
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)))

        too_recent_files = []

        for file_name in file_list:
            file_path = os.path.join(input_dir, file_name)
            archived_path = os.path.join(archived_dir, file_name)
            retries = 3

            while retries > 0:
                try:
                    # Check if the file is empty or not
                    if os.path.getsize(file_path) == 0:
                        # If the file is empty, log a warning and continue to the next file
                        logging.warning(f"\033[33mFile '{file_name}' is empty. Skipping...\033[0m")
                        break

                    # Get the modification time of the file
                    file_mtime = os.path.getmtime(file_path)
                    current_time = time.time()

                    # Check if the file is older than 100 ms
                    if current_time - file_mtime > 0.1:
                        # If the file is older than 100 ms, process it
                        with open(file_path, 'r') as file:
                            # Perform data processing here
                            logging.info(f"\033[32mProcessing file: {file_name}\033[0m")
                            df = pd.read_csv(file)
                            # Update the DataTable with the file's content
                            updated_data = df.to_dict('records')
                            # Append data to the DataTable
                            data_table.data = data_table.data + updated_data
                            # Once processing is complete, move the file to the archive directory
                            shutil.move(file_path, archived_path)
                            logging.info(f"\033[36mFile processed and moved to archive: {file_name}\033[0m")
                        break  # Exit the loop if processing succeeds
                    else:
                        # If the file is not older than 100 ms, add it to the list of too recent files
                        logging.warning(f"\033[33mFile '{file_name}' is too recent. Adding to list for later processing.\033[0m")
                        too_recent_files.append(file_name)
                        break

                except Exception as e:
                    logging.error(f"\033[31mError processing file '{file_name}': {str(e)}\033[0m")
                    retries -= 1  # Decrement the retry counter

            else:
                # Log an error if all retries fail
                logging.error(f"\033[31mFailed to process file '{file_name}' after multiple retries.\033[0m")
        # Assuming df is your DataFrame with a column 'timestamp' containing timestamps
        # Convert 'timestamp' column to datetime if it's not already in datetime format
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Assuming 'timestamp' column is in local time and you want to convert it to UTC
        #df['timestamp'] = df['timestamp'].dt.tz_localize('America/Los_Angeles').dt.tz_convert('UTC')

# Now 'timestamp' column contains timestamps in UTC        

        # Process the too recent files after processing the older files
        for file_name in too_recent_files:
            # Retry processing the too recent files
            process_too_recent_file(input_dir, archived_dir, file_name, data_table)
        # Add a delay before checking again
        time.sleep(0.1)

def process_too_recent_file(input_dir, archived_dir, file_name, data_table):
    # Same processing logic as before, but without checking for age
    file_path = os.path.join(input_dir, file_name)
    archived_path = os.path.join(archived_dir, file_name)
    retries = 3

    while retries > 0:
        try:
            with open(file_path, 'r') as file:
                logging.info(f"\033[32mRetrying processing for file: {file_name}\033[0m")
                df = pd.read_csv(file)
                # Update the DataTable with the file's content
                updated_data = df.to_dict('records')
                # Append data to the DataTable
                data_table.data = data_table.data + updated_data
                # Once processing is complete, move the file to the archive directory
                shutil.move(file_path, archived_path)
                logging.info(f"\033[36mFile processed and moved to archive: {file_name}\033[0m")
            break
        except Exception as e:
            logging.error(f"\033[31mError processing file '{file_name}': {str(e)}\033[0m")
            retries -= 1  # Decrement the retry counter

    else:
        # Log an error if all retries fail
        logging.error(f"\033[31mFailed to process file '{file_name}' after multiple retries.\033[0m")
