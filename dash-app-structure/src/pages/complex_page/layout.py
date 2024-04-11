import os
import dash
from dash import html, dash_table, Input, Output, callback, dash_table, dcc
import dash_bootstrap_components as dbc
from flask import Flask
import pandas as pd
import logging
import threading  # Import threading module for multi-threading
from components import create_profile_image_card
from utils.loadConfig import load_config

import os
import shutil
import time
import pandas as pd
import logging

def monitor_input_directory(input_dir, archived_dir):
    global empty_df
    while True:
        
        file_list = os.listdir(input_dir)
        # Sort the file list based on modification time (oldest first)
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join(input_dir, x)))


        

        for file_name in file_list:
            file_path = os.path.join(input_dir, file_name)
            archived_path = os.path.join(archived_dir, file_name)
            retries = 3

            while retries > 0:
                try:
                    # Check if the file is empty or not
                    if os.path.getsize(file_path) == 0:
                        # If the file is empty, log a warning and continue to the next file
                        logging.warning(f"\033[33mFile '{file_name}' is empty. Skipping...")
                        break

                    # Get the modification time of the file
                    file_mtime = os.path.getmtime(file_path)
                    current_time = time.time()

                    # Check if the file is older than 100 ms
                    if current_time - file_mtime > 0.1:
                        # If the file is older than 100 ms, process it
                        with open(file_path, 'r') as file:
                            # Perform data processing here
                            logging.info(f"\033[32mProcessing file: {file_name}")
                            df = pd.read_csv(file)
                            # Update the DataTable with the file's content
                            # updated_data = df.to_dict('records')
                            # # Append data to the DataTable
                            # data_table.data = data_table.data + updated_data
                            empty_df = pd.concat([empty_df, df])

                            # Once processing is complete, move the file to the archive directory
                        shutil.move(file_path, archived_path)
                        logging.info(f"\033[36mFile processed and moved to archive: {file_name}")
                        break  # Exit the loop if processing succeeds
                    else:
                        # If the file is not older than 100 ms, add it to the list of too recent files
                        logging.warning(f"\033[33mFile '{file_name}' is too recent. Adding to list for later processing.")
                        #too_recent_files.append(file_name)
                        break

                except Exception as e:
                    logging.error(f"Error processing file '{file_name}': {str(e)}")
                    time.sleep(0.001)
                    retries -= 1  # Decrement the retry counter

            else:
                # Log an error if all retries fail
                logging.error(f"Failed to process file '{file_name}' after multiple retries")


# Get the current working directory
cwd = os.getcwd()

# Load configuration from JSON file
config_file_path = os.path.join(cwd, 'dash-app-structure', 'config.json')
config = load_config(config_file_path)

# Configure logging settings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='app.log')

# Register the page with Dash
dash.register_page(
    __name__,
    path='/complex',
    title='Process Monitoring'
)

# Create Flask server
server = Flask(__name__)

# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME
    ],
    meta_tags=[
        {'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}
    ],
    suppress_callback_exceptions=True,
    title='Dash app structure'
)

# Load dummy data for order
order_data_path = os.path.join(cwd, 'dash-app-structure', 'data', 'RPS_Example_Data_1.csv')
order_data = pd.read_csv(order_data_path)
order_data = order_data[order_data['workorder'] == 25512169]
df_orderdata = dash_table.DataTable(
    data=order_data.to_dict('records'),
    columns=[{'name': col, 'id': col} for col in order_data.columns]
)

# Define columns for DataTable
columns = [{'name': col, 'id': col} for col in
           ['doorID', 'measurementID', 'FeatureName', 'percent_pass', 'average_value', 'standard_deviation', 'variance']]

# Create empty DataTables

empty_df = pd.DataFrame(columns=['doorID', 'measurementID', 'FeatureName', 'percent_pass', 'average_value', 'standard_deviation', 'variance'])


# Define input and archived directories for CSV data
#input_dir_path_CSV = config.get('data_directory_CSV')
input_dir_path_CSV = config.get('grouped_data_directory_CSV')
archived_dir_path_CSV = config.get('data_directory_archiveCSV')

# Check if the directory exists for CSV data and create if not
if not os.path.exists(archived_dir_path_CSV):
    os.makedirs(archived_dir_path_CSV)
# Start monitoring input directory for new files in a separate thread
thread = threading.Thread(target=monitor_input_directory, args=(input_dir_path_CSV, archived_dir_path_CSV))
thread.daemon = True  # Set the thread as a daemon to stop when the main thread stops
thread.start()

# Define layout
layout = html.Div([
    dcc.Interval(id="interval-component", interval=2 * 1000, n_intervals=0),
    html.H3('Garage Door Profiles'),
    dbc.Row([
        create_profile_image_card('70E100', 'left'),
        create_profile_image_card('70E100', 'right')
    ]),
    html.H3('Measurement Data'),
    dash_table.DataTable(empty_df.to_dict('records'),[{"name": i, "id": i} for i in empty_df.columns], id='tbl'),
    # html.H3('Order data'),
    # dbc.Row([
    #     html.Div([df_orderdata])
    # ])
])

@callback(Output('tbl', 'data'), [Input('interval-component', 'n_intervals')])
def update_datatable(n_intervals):
    global empty_df
    return empty_df.to_dict('records')




