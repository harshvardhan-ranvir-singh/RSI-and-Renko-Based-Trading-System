# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 09:51:40 2019

@author: Harsh
"""


from upstox_api.api import Session

u = Session('aocg0mAF6R2uotb5Mae4Q1PyBBlznq6i7EakN5Dc')

u.set_redirect_uri('http://127.0.0.1:8000/upstox/redirect/')
u.set_api_secret('dzq2p8a0gf')

#print (u.get_login_url())

u.set_code('6b25edaeedc694a3b842af78dd19f1464b513b89')

access_token = u.retrieve_access_token()
print ('Received access_token: %s' % access_token)

