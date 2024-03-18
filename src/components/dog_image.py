# notes
'''
This file creates a simples dog image card.
This is useful for when you are trying to keep your styling really consistent across multiple items.
For instance, our card is outline with the warning color.
'''

# package imports
import dash_bootstrap_components as dbc

# local imports
from utils.images import get_side_profile

# def create_dog_image_card(breed, name):
#     src = get_dog_image(breed, name)
#     card = dbc.Card(
#         [
#             dbc.CardHeader(f'Dog {breed} {name}'),
#             dbc.CardImg(src=src)
#         ],
#         class_name='w-50',
#         color='warning',
#         outline=True
#     )
#     return card

def create_profile_image_card(productid, side):
    src = get_side_profile(productid, side)
    card = dbc.Card(
        [
            dbc.CardHeader(f'Garage Door Model {productid} - {side} side'),
            dbc.CardImg(src=src)
        ],
        class_name='w-50',
        color='warning',
        outline=True
    )
    return card
