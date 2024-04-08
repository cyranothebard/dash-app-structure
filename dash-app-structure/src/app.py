import logging
import os
import threading

import dash
import dash_bootstrap_components as dbc
from dash import html
from flask import Flask
from flask_login import LoginManager

from components.login import User, login_location
from components import navbar, footer
from utils.settings import APP_DEBUG, DEV_TOOLS_PROPS_CHECK
from utils.getdataFromLMI_sensorarray import run_measurement_data_collection
from utils.configureLogging import configure_logging



# Flask server configuration
server = Flask(__name__)
server.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))

# Initialize Dash app
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
    suppress_callback_exceptions=True,
    title='Dash app structure'
)

# Login manager object for user authentication
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(username):
    """Load user by username."""
    return User(username)

# Define layout function
app.layout = lambda: html.Div(
    [   
        login_location,
        navbar,
        dbc.Container(
            dash.page_container,
            class_name='my-2'
        ),
        footer
    ]
)

# Call the function to configure logging
configure_logging()

def main_thread():
    """Start the Flask app."""
    configure_logging()  # Configure logging
    logging.info("Starting the Flask app...")
    server.run(host=os.getenv('HOST'), port=os.getenv('PORT'), debug=os.getenv('APP_DEBUG'))

def data_collection_thread():
    """Start data collection in a separate thread."""
    logging.info("Starting data collection...")
    thread = threading.Thread(target=run_measurement_data_collection)
    thread.start()

# Run the app locally for development
if __name__ == "__main__":
    data_collection_thread()
    main_thread()
