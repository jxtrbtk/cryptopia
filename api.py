# ###############################################79############################
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Module Api (Api cryptopia)

This module is a simple wrapper to access Cryptopia public and private API. 
Code was found initially on the Cryptopia Forum that has closed since that.
So I can't say who was the author. 
It was written for Python 2.7, I've made the adaption to Python 3.
Some change ti implement the "UTF-8" compliance.

Methods:
    query (method, req) : 
        Call a method of the api with the parameters specified. 
        Return a JSON object with the response
        Arguments:
            method (req): method of the public or private api
            req (opt): list (public) or dictionnary (private) of parameters
                       default value = None

Config file:
    The API needs a key and a secret that are to be sotred in a xml config file
    -----------
    config.xml
    -----------
    <config>
        <API_KEY>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</API_KEY>
        <API_SECRET>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</API_SECRET>
    </config>

"""
# #############79##############################################################
#                                      #
__author__ = "?"                       # Found on Cryptopia Forum (closed now)
__contact__ = "bYhO-bOwA-dIcA"         #
__date__ = "tIfY-mArI-kA"              # Mon Nov 26 16:26:55 2018
__email__ = "j.t[4t]free.fr"           #
__version__ = "2.2.1"                  #
#                                      #
# ##################################79#########################################

import os
import time
import hmac
import urllib
import urllib.parse
import requests
import hashlib
import base64
import json
from random import randint
import xml.etree.ElementTree as etree

# Get the API key and secret from the xml file
api_file_path = os.path.realpath(__file__)
api_folder_path = os.path.dirname(api_file_path)
tree = etree.parse(os.path.join(api_folder_path,"config.xml"))
root = tree.getroot()
API_KEY = root.findall("API_KEY")[0].text
API_SECRET = root.findall("API_SECRET")[0].text

def query( method, req = None ):
    """Call a method of the api with the parameters specified. 
    Return a JSON object with the response
    Arguments:
        method: method of the public or private api
        req: list (public) or dictionnary (private) of parameters
    """    
    base_url = "https://www.cryptopia.co.nz/api/" 
    url = base_url + method
    if not req:
        req = {}
    # list of the methods covered 
    public_set = set(["GetCurrencies", "GetTradePairs", "GetMarkets", 
                      "GetMarket", "GetMarketHistory", "GetMarketOrders" ])
    private_set = set(["GetBalance", "GetDepositAddress", "GetOpenOrders", 
                       "GetTradeHistory", "GetTransactions", "SubmitTrade", 
                       "CancelTrade", "SubmitTip"])
    if method in public_set:
        if req:
            for param in req:
                url += '/' + str( param )
        r = requests.get( url )
    elif method in private_set:
        # preparing the headers for authorization to access the private api 
        nonce = str(int(time.time()))+str((randint(100, 999)))
        post_data = json.dumps( req );
        m = hashlib.md5()
        m.update(post_data.encode("UTF-8"))
        requestContentBase64String = base64.b64encode(
                m.digest()).decode("UTF-8")
        signature = API_KEY + "POST" 
        signature += urllib.parse.quote_plus( url ).lower() + nonce 
        signature += requestContentBase64String
        hmacsignature = base64.b64encode(
                hmac.new(base64.b64decode( API_SECRET ), 
                        signature.encode("UTF-8"), 
                        hashlib.sha256).digest()).decode("UTF-8")
        header_value = "amx " + API_KEY + ":" + hmacsignature 
        header_value += ":" + nonce
        # call the api 
        headers = { 'Authorization': header_value, 
                   'Content-Type':'application/json; charset=utf-8' }
        r = requests.post( url, data = post_data, headers = headers)
    else:
        return None
    response = r.json()
    return response

# #################################################################79##########
# local unit tests

if __name__ == "__main__":
    
    if  API_KEY == "":
        print("API_KEY is missing in config")
    if  API_SECRET == "":
        print("API_SECRET is missing in config")

    print (query("GetMarket", ["XMR_BTC"]))
    print (query("GetBalance", {"Currency":"BTC"}))
    print (query("Unknown"))

# #######################################################79####################