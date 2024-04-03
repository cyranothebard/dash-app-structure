# notes
'''
This directory is meant to be for a specific page.
We will define the page and import any page specific components that we define in this directory.
This file should serve the layouts and callbacks.
The callbacks could be in their own file, but you'll need to make sure to import the file so they load.
'''


# package imports
import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc
from flask import Flask
from utils.data_sensorarray import getVersionStr
from components import create_profile_image_card
from utils.dataFrameFromCSV import read_csv_files_and_move_to_archive

def generate_table(dataframe):
    """
    Generate a Dash DataTable from a DataFrame.

    Args:
        dataframe (pd.DataFrame): DataFrame to be displayed.

    Returns:
        dash_table.DataTable: Dash DataTable component.
    """
    return dash_table.DataTable(
        data=dataframe,
        columns=[{'name': col, 'id': col} for col in dataframe.columns],
        style_data_conditional=sensor_data_conditional
    )

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
    #  {
    #     'if': {
    #         'filter_query': '{'Work Order'} == 10264754',
    #         'column_id': 'Work Order'
    #            },
    #     'backgroundColor': 'red',
    #     'color': 'white',
    # },
]

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
getVersionStr()
input_dir_path = r'F:\Gitea\dashboard\src\assets\data'
archived_dir_path = r'F:\Gitea\dashboard\src\assets\data\archive'
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
        generate_table(read_csv_files_and_move_to_archive(input_dir_path, archived_dir_path)),
        html.H3('Order Data'),
    ])