# notes
'''
This file is for creating a navigation bar that will sit at the top of your application.
Much of this page is pulled directly from the Dash Bootstrap Components documentation linked below:
https://dash-bootstrap-components.opensource.faculty.ai/docs/components/navbar/
'''

# package imports
from dash import html, callback, Output, Input, State
import dash_bootstrap_components as dbc

# local imports
from utils.images import logo_encoded, denali_logo_encoded
from components.login import login_info

# component
navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=logo_encoded, height='75px')),
                    ],
                    align='center',
                    className='g-0',
                ),
                href='https://www.amarr.com/us/en',
                style={'textDecoration': 'none'},
            ),
            dbc.NavbarToggler(id='navbar-toggler', n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        # dbc.NavItem(
                        #     dbc.NavLink(
                        #         'Home',
                        #         href='/'
                        #     )
                        # ),
                        dbc.NavItem(
                            dbc.NavLink(
                                'Complex Page',
                                href='/'
                            )
                        )
                        # ),
                        # html.Div(
                        #     login_info
                        # )
                    ]
                ),
                id='navbar-collapse',
                navbar=True
            ),
            html.A(
                dbc.Row(
                        [
                            dbc.Col(html.Img(src=denali_logo_encoded, height='75px'), width={"size": 5, "offset": 250}), # Adjusted to move to the right
                        ],
                        align='center',
                        className='g-0',
                    ),
                    href='https://www.denaliai.com/about-denali/',
                    style={'textDecoration': 'none'},
            ),
        ]
    ),
    color='dark',
    dark=True,
)

# add callback for toggling the collapse on small screens
@callback(
    Output('navbar-collapse', 'is_open'),
    Input('navbar-toggler', 'n_clicks'),
    State('navbar-collapse', 'is_open'),
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
