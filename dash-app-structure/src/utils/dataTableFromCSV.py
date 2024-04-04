
import dash
from dash import html, dcc
import dash_table
import pandas as pd
import os
import shutil


columns = [{'name': col, 'id': col} for col in ['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp']]

sensor_data_conditional = [
    {
        'if': {
            'filter_query': '{tongue_hem_height} < 0.18 or {tongue_hem_height} > 0.22',
            'column_id': 'tongue_hem_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_hem_height} < 0.18 or {groove_hem_height} > 0.22',
            'column_id': 'groove_hem_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{face_dovetail_height} < 0.325 or {face_dovetail_height} > 0.365',
            'column_id': 'face_dovetail_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{back_dovetail_height} < 0.265 or {back_dovetail_height} > 0.305',
            'column_id': 'back_dovetail_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{tongue_leg_height} < 1.85 or {tongue_leg_height} > 1.90',
            'column_id': 'tongue_leg_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_leg_height} < 1.85 or {groove_leg_height} > 1.90',
            'column_id': 'groove_leg_height'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{tongue_shadow_line} < 0.045 or {tongue_shadow_line} > 0.055',
            'column_id': 'tongue_shadow_line'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{groove_shadow_line} < 0.045 or {groove_shadow_line} > 0.055',
            'column_id': 'groove_shadow_line'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{pan_width} < 18.00 or {pan_width} > 18.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
   {
        'if': {
            'filter_query': '{pan_width} < 21.00 or {pan_width} > 21.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
    {
        'if': {
            'filter_query': '{pan_width} < 24.00 or {pan_width} > 24.045',
            'column_id': 'pan_width'
               },
        'backgroundColor': 'red',
        'color': 'white',
    },
]

# Function to read CSV files from a directory, append data to the DataTable, and move files to an archive directory
def process_csv_files(input_dir, archive_dir, data_table):

   # Ensure that the archive directory exists
    os.makedirs(archive_dir, exist_ok=True)
    
    # Iterate through each file in the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.csv'):
            file_path = os.path.join(input_dir, file_name)
            
            # Read CSV data into a DataFrame
            dataframe = pd.read_csv(file_path)
            
            # Append data to the DataTable
            data_table.data = data_table.data + dataframe.to_dict('records')
            
            # Move the CSV file to the archive directory
            archived_file_path = os.path.join(archive_dir, file_name)
            shutil.move(file_path, archived_file_path)
