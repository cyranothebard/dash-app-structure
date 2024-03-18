# notes
'''
This file is used for handling anything image related.
I suggest handling the local file encoding/decoding here as well as fetching any external images.
'''

# package imports
import base64
import os

# image CDNs
image_cdn = 'https://images.dog.ceo/breeds'

# logo information
cwd = os.getcwd()
logo_path = os.path.join(cwd, 'src', 'assets', 'logos', 'amarr_logo_main.jpg')
logo_tunel = base64.b64encode(open(logo_path, 'rb').read())
logo_encoded = 'data:image/png;base64,{}'.format(logo_tunel.decode())
# productid picture information
# side_profile_path = os.path.join(cwd, 'src', 'assets', 'side_profiles')
# side_profile_tunel = base64.b64encode(open(side_profile_path, 'rb').read())
# side_profile_encoded = 'data:image/png;base64,{}'.format(side_profile_tunel.decode())                


# def get_dog_image(breed, name):
#     '''
#     This method assumes that you are fetching specific images hosted on a CDN.
#     For instance, random dog pics given a breed.
#     '''
#     if breed and name:
#         return f'{image_cdn}/{breed}/{name}.jpg'
#     return None

def get_side_profile(productid, side):
    '''
    This method generates src location of garage door profile to be used
    as visualization aid on main operator interface.
    '''
    side_profile_path_left = os.path.join(cwd, 'src', 'assets', 'side_profiles', '70E100_left.png')
    side_profile_tunel_left = base64.b64encode(open(side_profile_path_left, 'rb').read())
    side_profile_encoded_left = 'data:image/png;base64,{}'.format(side_profile_tunel_left.decode()) 
    side_profile_path_right = os.path.join(cwd, 'src', 'assets', 'side_profiles', '70E100_right.png')
    side_profile_tunel_right = base64.b64encode(open(side_profile_path_right, 'rb').read())
    side_profile_encoded_right = 'data:image/png;base64,{}'.format(side_profile_tunel_right.decode()) 
    if productid and side:
        if side == 'left':
            return f'{side_profile_encoded_left}'
        else:
            return f'{side_profile_encoded_right}'
        # return f'{side_profile_encoded}\{productid}_{side}.png'