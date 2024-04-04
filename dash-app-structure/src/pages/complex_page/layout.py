# notes
'''
This directory is meant to be for a specific page.
We will define the page and import any page specific components that we define in this directory.
This file should serve the layouts and callbacks.
The callbacks could be in their own file, but you'll need to make sure to import the file so they load.
'''


# package imports
import os
import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc
from flask import Flask
import pandas as pd
from components import create_profile_image_card
from utils.dataTableFromCSV import process_csv_files
from utils.dataTableFromCSV import sensor_data_conditional


dash.register_page(
    __name__,
    path='/complex',
    title='Process Monitoring'
)
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    # use_pages=True,    # turn on Dash pages
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME
    ],  # fetch the proper css items we want
    meta_tags=[
        {   # check if device is a mobile device. This is a must if you do any mobile styling
            'name': 'viewport',
            'content': 'width=device-width, initial-scale=1'
        }
    ],
    suppress_callback_exceptions=True,
    title='Dash app structure'
)

### generate dummy data for order
cwd = os.getcwd()
order_data_path = os.path.join(cwd,'dash-app-structure', 'data', 'RPS_Example_Data_1.csv')
order_data = pd.read_csv(order_data_path)
order_data = order_data[order_data['workorder']==25512169]
df_orderdata = dash_table.DataTable(
        data=order_data.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in order_data.columns])


columns = [{'name': col, 'id': col} for col in ['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp']]
# Create an empty DataTable
empty_df = pd.DataFrame(columns=['ID', 'Value', 'Decision', 'FeatureName', 'TimeStamp'])
data_table = dash_table.DataTable(
    id='FeatureName',
    columns=columns,
    style_data_conditional= sensor_data_conditional,
    data=empty_df.to_dict('records')
)

input_dir_path = os.path.join(cwd,'dash-app-structure', 'data', 'measurmentDataCSV')
archived_dir_path = os.path.join(cwd,'dash-app-structure', 'data', 'archive')
process_csv_files(input_dir_path, archived_dir_path, data_table )
layout = html.Div([
        # html.H3('Random component'),
        # random_component,
        html.H3('Garage Door Profiles'),
        dbc.Row(
            [
                create_profile_image_card('70E100', 'left'), # DEBUGGING - function results in broken images
                create_profile_image_card('70E100', 'right')
            ]
        ),
        html.H3('Measurement Data'),
        dbc.Row(
            [
                html.Div(
                    [
                        data_table
                    ]
                )#data_table
            ]
        ),
        html.H3('Order Data'),
        dbc.Row(
            [
                html.Div(
                    [
                        df_orderdata
                    ]
                )#data_table
            ]
        ), 
    ])
