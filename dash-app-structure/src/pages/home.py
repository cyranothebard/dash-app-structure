# package imports
import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(
    __name__,
    path='/',
    redirect_from=['/home'],
    title='Admin'
)

layout = html.Div(
    [
        html.H1('Admin'),
        html.Div(
            html.A('Checkout the process analysis dashboard page here.', href='/complex')
        ),
        html.A('/page2', href='/page2'),
    
        dcc.Checklist(
            id='profile-dimensions',
            options=[
                {'label': 'Dovetail Back Side Height', 'value': 'Dovetail Back Side Height'},
                {'label': 'Dovetail Face Side Height', 'value': 'Dovetail Face Side Height'},
                {'label': 'Dovetail Side Hem Height', 'value': 'Dovetail Side Hem Height'},
                {'label': 'Dovetail Leg Height', 'value': 'Dovetail Leg Height'},
                {'label': 'Dovetail Lower Leg Height', 'value': 'Dovetail Lower Leg Height'},
                {'label': 'Dovetail Lower Leg Trough Height', 'value': 'Dovetail Lower Leg Trough Height'},
                {'label': 'Dovetail Upper Leg Height', 'value': 'Dovetail Upper Leg Height'},
                {'label': 'Dovetail Upper Leg Trough Height', 'value': 'Dovetail Upper Leg Trough Height'},
                {'label': 'Dovetail Inne Width', 'value': 'Dovetail Inner Width'},
                {'label': 'Dovetail Neck Width', 'value': 'Dovetail Neck Width'},
                {'label': 'Shadow Line Depth', 'value': 'Shadow Line Depth'},
                {'label': 'TOG-L-LOC Foot Clearance', 'value': 'TOG-L-LOC Foot Clearance'},
                {'label': 'Tongue Side Hem Height', 'value': 'Tongue Side Hem Height'},
                {'label': 'Tongue Leg Height - Lower', 'value': 'Tongue Leg Height - Lower'},
                {'label': 'Tongue Leg Height - Middle', 'value': 'Tongue Leg Height - Middle'},
                {'label': 'Tongue Leg Height - Top', 'value': 'Tongue Leg Height - Top'},
                ],
            value=['Dovetail Back Side Height'],
        ),
        
        html.Div(id='content')
    ]
)

@callback(Output('content', 'children'), Input('radios', 'value'))
def home_radios(value):
    return f'You have selected {value}'
