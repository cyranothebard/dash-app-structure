import os
import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc
from flask import Flask
import pandas as pd
import logging
import threading  # Import threading module for multi-threading
from components import create_profile_image_card
from utils.loadConfig import load_config
from utils.processFiles import  monitor_input_directory

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
           ['sensorID', 'frameIndex', 'timeStamp', 'measurementID', 'Value', 'Decision', 'FeatureName']]

# Create empty DataTables
empty_df = pd.DataFrame(columns=['sensorID', 'frameIndex', 'timeStamp', 'measurementID', 'Value', 'Decision', 'FeatureName'])
global data_table_csv
data_table_csv = dash_table.DataTable(
    id='FeatureName',
    columns=columns,
    data=empty_df.to_dict('records')
)

# Define input and archived directories for CSV data
input_dir_path_CSV = config.get('data_directory_CSV')
archived_dir_path_CSV = config.get('data_directory_archiveCSV')

# Check if the directory exists for CSV data and create if not
if not os.path.exists(archived_dir_path_CSV):
    os.makedirs(archived_dir_path_CSV)

# Start monitoring input directory for new files in a separate thread
thread = threading.Thread(target=monitor_input_directory, args=(input_dir_path_CSV, archived_dir_path_CSV, data_table_csv))
thread.daemon = True  # Set the thread as a daemon to stop when the main thread stops
thread.start()

# Define layout
layout = html.Div([
    html.H3('Garage Door Profiles'),
    dbc.Row([
        create_profile_image_card('70E100', 'left'),
        create_profile_image_card('70E100', 'right')
    ]),
    html.H3('Measurement Data'),
    dbc.Row([
        html.Div(
            [data_table_csv]
            )
    ]),
    html.H3('Order data'),
    dbc.Row([
        html.Div([df_orderdata])
    ])
])
