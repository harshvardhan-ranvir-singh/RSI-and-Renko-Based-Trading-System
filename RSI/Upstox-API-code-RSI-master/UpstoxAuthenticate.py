# -*- coding: utf-8 -*-
"""
Created on Thu Aug 22 09:51:40 2019

@author: Harsh
"""


from upstox_api.api import Session

u = Session('T57lEJhTxJ2cdoWETCTVf5WvKTpfVh0f5QltvUBh')

u.set_redirect_uri('http://127.0.0.1:8000/upstox/redirect/')
u.set_api_secret('ini3zida2k')

#print (u.get_login_url())

#u.set_code('6b25edaeedc694a3b842af78dd19f1464b513b89')

#access_token = u.retrieve_access_token()
#print ('Received access_token: %s' % access_token)

