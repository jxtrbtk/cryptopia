# Cryptopia Exchange API Wrapper

[Public API](https://support.cryptopia.co.nz/csm?id=kb_article&sys_id=40e9c310dbf9130084ed147a3a9619eb)

[Public API](https://support.cryptopia.co.nz/csm?id=kb_article&sys_id=a75703dcdbb9130084ed147a3a9619bc)

## api.py
Basic wrapper for the public and private API.
The wrapper needs the key and secret to be stored in a config.xml file.

### config.xml
```
<config>
<API_KEY>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</API_KEY>
<API_SECRET>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</API_SECRET>
</config>
```

### query
Contains a single method called `query` with 2 parameters
- **method** : the method of the api to be called
- **req** : the parameters to pass to the api (as a list if the public api is called, as a dictionnary if the private api i called).

### examples 
```
output = query("GetMarket", ["XMR_BTC"]))

print(output)
{'Success': True, 
'Message': None, 
'Data': {   'TradePairId': 2999, 'Label': 'XMR/BTC', 
            'AskPrice': 0.01332882, 'BidPrice': 0.01325268, 
            'Low': 0.01249999, 'High': 0.0135, 'Volume': 249.00094569, 
            'LastPrice': 0.01338238, 'BuyVolume': 1313716.6395774, 
            'SellVolume': 1795.39241071, 'Change': 3.07, 
            'Open': 0.01298393, 'Close': 0.01338238, 'BaseVolume': 3.25274433, 
            'BuyBaseVolume': 3.48430831, 'SellBaseVolume': 29025222.97086225}, 
'Error': None}

output = print (query("GetBalance", {"Currency":"BTC"}))

print(output)
{'Success': True, 
'Error': None, 
'Data': [ { 'CurrencyId': 1, 'Symbol': 'BTC', 'Total': 0.0035989, 
            'Available': 0.0035989, 'Unconfirmed': 0.0, 'HeldForTrades': 0.0, 
            'PendingWithdraw': 0.0, 'Address': None, 'Status': 'OK', 
            'StatusMessage': None, 'BaseAddress': None}]}
```

## operation.py 
_(... coming soon ...)_

Simple implementation of the api that allows to : 
- creates an order for a given market with a target price and a stoploss
- execute a pipeline of orders


