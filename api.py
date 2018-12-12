# ###############################################79############################
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Module Api (Api cryptopia)

This module is a simple wrapper to access Cryptopia public and private API. 
Code was found initially on the Cryptopia Forum that has closed since that.
So I can't say who was the initial author. 
It was written for Python 2.7, I've made the adaption to Python 3.
Some changes made to implement the "UTF-8" compliance.

Functions : 
    query : calls the api given method with the given parameters
        input : 
            method : name of the method (string)
            reg : name of the method (List for the public API
                  Dictionnary for the private API)
        output :
            json object of the API answer

Config file:
    The API needs a key and a secret that are to be sotred in a config file
    -----------
    config.py
    -----------
    API_KEY = '____________your_key____________'
    API_SECRET = '_________________your_secret________________'


"""
# #############79##############################################################
#                                      #
__author__ = "?"                       # Found on Cryptopia Forum (closed now)
__contact__ = "bYhO-bOwA-dIcA"         #
__date__ = "tIfY-mArI-kA"              # Mon Nov 26 16:26:55 2018
__email__ = "yeah[4t]free.fr"          #
__version__ = "2.0.1"                  #
#                                      #
# ##################################79#########################################

import time
import hmac
import urllib
import urllib.parse
import requests
import hashlib
import base64
import json
from random import randint

import config

def query( method, req = None ):
    """calls the api given method with the given parameters

        input : 
            method : name of the method (string)
            reg : name of the method (List for the public API
                  Dictionnary for the private API)
        output :
            json object of the API answer
    """
    base_url = "https://www.cryptopia.co.nz/api/" 
    url = base_url + method
    if not req:
        req = {}
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
        print(url)
    elif method in private_set:
        nonce = str(int(time.time()))+str((randint(100, 999)))
        post_data = json.dumps( req );
        m = hashlib.md5()
        m.update(post_data.encode("UTF-8"))
        requestContentBase64String = base64.b64encode(
                m.digest()).decode("UTF-8")
        signature = config.API_KEY + "POST" 
        signature += urllib.parse.quote_plus( url ).lower() + nonce 
        signature += requestContentBase64String
        hmacsignature = base64.b64encode(
                hmac.new(base64.b64decode( config.API_SECRET ), 
                        signature.encode("UTF-8"), 
                        hashlib.sha256).digest()).decode("UTF-8")
        header_value = "amx " + config.API_KEY + ":" + hmacsignature 
        header_value += ":" + nonce
        headers = { 'Authorization': header_value, 
                   'Content-Type':'application/json; charset=utf-8' }
        r = requests.post( url, data = post_data, headers = headers)
    response = r.json()
    return response

# #################################################################79##########
# local unit tests

if __name__ == "__main__":

    if  hasattr(config, "API_KEY") == False:
        print("API_KEY is missing in config")
    if  hasattr(config, "API_SECRET") == False:
        print("API_SECRET is missing in config")
    
    if  config.API_KEY == "":
        print("API_KEY is missing in config")
    if  config.API_SECRET == "":
        print("API_SECRET is missing in config")

    print (query("GetMarket", ["XMR_BTC"]))
    print (query("GetBalance", {"Currency":"BTC"}))

# #######################################################79####################