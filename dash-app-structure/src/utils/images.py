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
logo_path = os.path.join(cwd,'dash-app-structure', 'src', 'assets', 'logos', 'amarr_logo_main.jpg')
denali_logo_path = os.path.join(cwd,'dash-app-structure', 'src', 'assets', 'logos', 'denali_logo.jpg')
logo_tunel = base64.b64encode(open(logo_path, 'rb').read())
denali_logo_tunel = base64.b64encode(open(denali_logo_path, 'rb').read())
denali_logo_encoded = f'data:image/png;base64,{denali_logo_tunel.decode()}'
logo_encoded = f'data:image/png;base64,{logo_tunel.decode()}'

def get_side_profile(productid, side):
    '''
    This method generates src location of garage door profile to be used
    as visualization aid on main operator interface.
    '''
    side_profile_path_left = os.path.join(cwd, 'dash-app-structure', 'src', 'assets', 'side_profiles', '70E100_left.png')
    side_profile_tunel_left = base64.b64encode(open(side_profile_path_left, 'rb').read())
    side_profile_encoded_left = 'data:image/png;base64,{}'.format(side_profile_tunel_left.decode()) 
    side_profile_path_right = os.path.join(cwd, 'dash-app-structure', 'src', 'assets', 'side_profiles', '70E100_right.png')
    side_profile_tunel_right = base64.b64encode(open(side_profile_path_right, 'rb').read())
    side_profile_encoded_right = 'data:image/png;base64,{}'.format(side_profile_tunel_right.decode()) 
    if productid and side:
        if side == 'left':
            return f'{side_profile_encoded_left}'
        else:
            return f'{side_profile_encoded_right}'
        
        # return f'{side_profile_encoded}\{productid}_{side}.png'