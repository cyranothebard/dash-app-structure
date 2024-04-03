# Standard library imports
import os

# Third-party library imports
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from flask import Flask
from flask_login import LoginManager

# Local imports
from components.login import User, login_location
from components import navbar, footer
from utils.settings import (APP_DEBUG, APP_HOST, APP_PORT, DEV_TOOLS_PROPS_CHECK)

# Specific imports from dash
from dash import html

# Specific imports from components
#from components.login import User, login_location
server = Flask(__name__)
app = dash.Dash(
    __name__,
    server=server,
    use_pages=True,    # turn on Dash pages
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

server.config.update(SECRET_KEY=os.getenv('SECRET_KEY'))

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'

@login_manager.user_loader
def load_user(username):
    """This function loads the user by user id. Typically this looks up the user from a user database.
    We won't be registering or looking up users in this example, since we'll just login using LDAP server.
    So we'll simply return a User object with the passed in username.
    """
    return User(username)

def serve_layout():
    '''Define the layout of the application'''
    return html.Div(
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


app.layout = serve_layout   # set the layout to the serve_layout function
server = app.server         # the server is needed to deploy the application

# Run the app locally for development
if __name__ == "__main__":
    app.run(debug=True)

# Run the app on server
# if __name__ == "__main__":
#     app.run_server(
#         host=APP_HOST,
#         port=APP_PORT,
#         debug=APP_DEBUG,
#         dev_tools_props_check=DEV_TOOLS_PROPS_CHECK
#     )

