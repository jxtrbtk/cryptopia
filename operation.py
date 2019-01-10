# ###############################################79############################
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Module Operation (Cryptopia)

This module aim to manage orders on the Cryptopia Exchange. 
The principle is to use the Create_Order method to create an order.
Then the Execute_Pipeline is run on a regulare basis (ie: every minute)
to take care of the orders. A sell order is created a the start. 
If the price stay under the stoploss several times (DEFAULT COUNTDOWN), 
the sellorder at the target price is canceled 
and an order at the market price is created instead.

Methods : 

    Initialisation : Generate de needed subfolder in the default data folder 

    Create_Order : Generate a new order in the pipeline
        parameters : 
            pair (req) : market (ie: "XMR_BTC")
            amount (req) : amount to use (BTC) 
            target (opt) : ratio of the sell target - default : 0.1 (+10%)
            stoploss (opt) : ratio of the stoploss - default : 0.0618 (-6.18%)

    Execute_Pipeline : Execute all orders in the pipeline

"""
# #############79##############################################################
#                                      #
__author__ = "jxtrbtk"                 #
__contact__ = "bYhO-bOwA-dIcA"         #
__date__ = "cYfE-rIrI-kA"              # Mon Dec  3 21:47:41 2018
__email__ = "j.t[4t]free.fr"           #
__version__ = "2.0.1"                  #
#                                      #
# ##################################79#########################################

import os
import platform
import datetime
import time
import uuid
import xml.etree.ElementTree as etree

import api

DATA_PATH = "data"
LOGS_ENABLED = True

DEFAULT_COUNTDOWN = 7
# security coeff to avoid to trade under the minimum trade amount
PHI = 1.38

# cache for api data, to avoid errors caused by too many api calls
CACHE = {}

def Main():
    Initialisation()
#    Create_Order("XMR_BTC", 0.00080903)
#    Create_Order("XMR_BTC", 0.00080904, target=0.0618, stoploss=0.0618)
#    Create_Order("TRX_BTC", 0.00000004, target=0.0618, stoploss=0.0618)
    Execute_Pipeline()


def Create_Order(pair, amount, target=0.1, stoploss=0.0618):
    """
    Method to create a new order to be added in the pipline. The parameters 
    passed are as follows:
    pair     (req) - Market pair, string in format XXX_YYY ("XMR_BTC")
    amount   (req) - Amount to use for the order (in YYY, ie in BTC)
    target   (opt) - Target to sell with a benefit (ratio, default=0.1)
    stoploss (opt) - Target to sell if market drops (ratio, default=0.0618)
    """
    file_name = str(uuid.uuid4())+".xml"
    file_path = os.path.join("data","in", file_name)
    root = etree.Element("order")    
    etree.SubElement(root, "header", 
                     date=str(datetime.datetime.now()), pair=pair, 
                     amount='{:.8f}'.format(amount), 
                     target='{:.8f}'.format(target), 
                     stoploss='{:.8f}'.format(stoploss), status="init" )
    etree.SubElement(root, "entry")
    etree.SubElement(root, "action", countdown=str(DEFAULT_COUNTDOWN)) 
    etree.SubElement(root, "audit")
    tree = etree.ElementTree(root)
    tree.write(file_path)
    Log("Order "+file_name+" created")

def Execute_Pipeline():
    """
    Method to execute all orders in the pipline. 
    No parameters 
    """
    global CACHE
    CACHE = {}
    machine_name = platform.node()
    Log(machine_name)
    Log(str(datetime.datetime.now()))
    Log("-----------------------------")
    Feed_Pipeline()
    for name in os.listdir(os.path.join("data","work")):
        Log("Order " + name )
        Log("-----------------------------start")
        try:
            Execute_Order(name)
        except Exception as e:
            Log("ERROR Pipline : "+str(e)+"")
        Log("-----------------------------done")
    Log(str(datetime.datetime.now()))

def Feed_Pipeline():
    """
    Method to add a created order to the pipline. 
    No parameters 
    """
    for name in os.listdir(os.path.join(DATA_PATH, "in")):
        source_file_path = os.path.join(DATA_PATH, "in", name)
        destination_file_name = str(uuid.uuid4()) + ".xml"
        destination_file_path = os.path.join(DATA_PATH, "work", 
                                             destination_file_name)
        os.rename(source_file_path, destination_file_path)
        Log("new order " + destination_file_name)
        Log(" from file : " + name)

def Execute_Order(filename):
    """
    Method to execute a give order. The parameter are:
    filename (req) - Name of the xml file containing the order parameters
    """
    file_path = os.path.join(DATA_PATH, "work",filename)
    tree = etree.parse(file_path)
    root = tree.getroot()
    header = Get_Child_By_Name(root, "header")
    Log("pair : " + header.get("pair"))
    if header.get("status") in (None, "", "init") :
        header.set("status", "ready")
    entry = Get_Child_By_Name(root, "entry")
    if (entry.get("status") != "ready"):
        Log("step - entry")
        Execute_Entry(header, entry)
        tree.write(file_path)
        return "entry"
    action = Get_Child_By_Name(root, "action")
    if (action.get("status") != "ready"):
        Log("step - action")
        Execute_Action(header, entry, action)
        tree.write(file_path)
        return "action"
    audit = Get_Child_By_Name(root, "audit")
    if (audit.get("status") != "ready"):
        Log("step - audit")
        Execute_Audit(header, entry, action, audit)
        tree.write(file_path)
        return "audit"
    ## Pipeline completed = order backed up
    os.rename(os.path.join("data","work",filename), 
              os.path.join("data","bak", filename))
    Log(" has been sent out of pipeline")

def Get_Minimum_Trade_Amount(pair):
    """
    Method to calculate The minimum amount for an order of a given trade pair.
    The method get the minimum from the exchange api and apply a security coeff
    Parameters :
    pair     (req) - Market pair, string in format XXX_YYY ("XMR_BTC")
    """
    minimumtradepair = 0.0005000
    Output = Get_Cache("GetTradePairs", "")
    for data in Output["Data"]:
        if data["Label"]==pair.replace("_", "/"):
            minimumtradepair = float(data["MinimumBaseTrade"])
    minimumtradepair = minimumtradepair*(PHI)+0.00000001
    Log("minimumtradepair: "+'{:.8f}'.format(minimumtradepair))
    return minimumtradepair

def Check_Buy_Orders(pair):
    """
    Method to check if buy orders are existing for a given pair. Parameters:
    pair     (req) - Market pair, string in format XXX_YYY ("XMR_BTC")
    """
    Output = Get_Cache("GetMarket", [pair])
    pairid = Output["Data"]["TradePairId"]
    Output = api.query("GetOpenOrders", {'TradePairId':pairid})
    buy_orders = False
    for order_item in Output["Data"]:
        if order_item["Type"] == "Buy":
            buy_orders = True
    return buy_orders

def Execute_Entry(header, entry):
    """
    Method to handle the entry stage of an order. It creates the buy order and
    check that it is correctly filled. Parameters as follows:
    header    (req) - Header xml object from the xml ordee config file
    entry     (req) - Entry xml object from the xml ordee config file
    """
    pair = header.get("pair")
    stoploss = float(header.get("stoploss"))
    if entry.get("status") in (None, "") :
        entry.set("status", "init")

    if (entry.get("status") == "init"):
        Log("status - init")
        Output = api.query("GetMarket", [pair])
        pairid = Output["Data"]["TradePairId"]
        refprice = float(Output["Data"]["AskPrice"])
        Log("ref price: "+'{:.8f}'.format(refprice))
        baseamount = float(header.get("amount"))
        Log("base amount : "+'{:.8f}'.format(baseamount))
        amount = baseamount/refprice
        Log("amount : "+'{:.8f}'.format(amount))
        currency = pair[:pair.index('_')]
        Output = api.query("GetBalance", {'Currency':currency})
        if (Output["Data"] == None):
            already = float(0.0)
        else:
            already = float(Output["Data"][0]["Total"])
        Log("already : "+'{:.8f}'.format(already))
        amount = amount - already
        minimumtradepair = Get_Minimum_Trade_Amount(pair)*(1-stoploss)
        minimumamount = float('{:.8f}'.format(minimumtradepair/refprice))
        Log("minimumamount: "+'{:.8f}'.format(minimumamount))
        if(amount<minimumamount):
            entry.set("status", "ready")
            entry.set("message", "amount too small")
            Log("....amount too small")
        else: 
            tradetype = 'Buy'
            Output = api.query("SubmitTrade", {'TradePairId':pairid, 
                                               'Type':tradetype, 
                                               'Rate':refprice, 
                                               'Amount':amount})
            Log ("Buy ID : "+ str(pairid) + "  " + "{:.8f}".format(amount)+ 
                 " @ " + '{:.8f}'.format(refprice) + " = " + 
                 "{:.8f}".format(baseamount))
            Log(Output)
            entry.set("price", '{:.8f}'.format(refprice))
            entry.set("status", "sent")
            entry.set("countdown", str(DEFAULT_COUNTDOWN))
            Log ("sent")
            time.sleep(8)

    if (entry.get("status") == "sent"):
        Log("status - sent")
        countdown = int(entry.get("countdown"))
        has_buy_orders = Check_Buy_Orders(pair)
        if not has_buy_orders :
            minimumtradepair = Get_Minimum_Trade_Amount(pair)*(1-stoploss)
            price = float(entry.get("price"))
            minimumamount = float('{:.8f}'.format(minimumtradepair/price))
            Log("minimumamount: "+'{:.8f}'.format(minimumamount))
            currency = pair[:pair.index('_')]
            Output = api.query("GetBalance", {'Currency':currency})
            if (Output["Data"] == None):
                available = float(0.0)
            else:
                available = float(Output["Data"][0]["Available"])
            Log("available: "+'{:.8f}'.format(available))
            countdown = 0
            if(available>=minimumamount):
                countdown = DEFAULT_COUNTDOWN
                Log("filled")
                entry.set("status", "ready")
        Log("countdown : "+str(countdown))
        if (countdown > 0):
            countdown = countdown - 1
            entry.set("countdown", str(countdown))
        else:
            Log("retry")
            pair = header.get("pair")
            Output = Get_Cache("GetMarket", [pair])
            pairid = Output["Data"]["TradePairId"]
            Output = api.query("CancelTrade", {'Type':'TradePair', 
                                               'TradePairId':pairid})
            Log(Output)
            Log("Cancel Trade")
            entry.set("status", "init")
    
def Execute_Action(header, entry, action):
    """
    Method to handle the action stage of an order. It creates the target sell
    order, check the prive level all the time and launche the stoploss process
    if the price stays below the stoploss level defined in the order more that
    [DEFAULT_COUNTDOWN] times. Stoploss cancels the target order sell and sells
    the coins at the market price
    header    (req) - Header xml object from the xml ordee config file
    entry     (req) - Entry xml object from the xml ordee config file
    action    (req) - Action xml object from the xml ordee config file
    """
    pair = header.get("pair")
    if action.get("status") in (None, "") :
        action.set("status", "init")

    if (action.get("status") == "init"):
        Log("status - init")
        if (entry.get("price") == None):
            action.set("status", "ready")
        else:
            price = float(entry.get("price"))
            target = float(header.get("target"))
            stoploss = float(header.get("stoploss"))
            target_price = price*(1+target)+0.00000001
            stoploss_price = price*(1-stoploss)+0.00000001
            action.set("stoploss", '{:.8f}'.format(stoploss_price))
            action.set("target", '{:.8f}'.format(target_price))
            action.set("status", "sell")

    if (action.get("status") == "sell"):
        Log("status - sell order")
        price = float(entry.get("price"))
        target = float(action.get("target"))
        stoploss = float(action.get("stoploss"))
        Output = Get_Cache("GetMarket", [pair])
        pairid = Output["Data"]["TradePairId"]
        tradetype = 'Sell'
        currency = pair[:pair.index('_')]
        Output = api.query("GetBalance", {'Currency':currency})
        amount = float(Output["Data"][0]["Total"])
        Log(tradetype + " " + pair + " " + '{:.8f}'.format(amount) + 
            " at " + '{:.8f}'.format(target))
        Output = api.query("SubmitTrade", {'TradePairId':pairid, 
                                           'Type':tradetype, 
                                           'Rate':target, 'Amount':amount})
        time.sleep(15)
        has_buy_orders = Check_Buy_Orders(pair)
        if not has_buy_orders :
            action.set("status", "active")

    if (action.get("status") == "active"):
        Log("status - active")
        pair = header.get("pair")
        currency = pair[:pair.index('_')]        
        Output = Get_Cache("GetMarket", [pair])            
        pairid = Output["Data"]["TradePairId"]
        refprice = float(Output["Data"]["LastPrice"])
        bidprice = float(Output["Data"]["BidPrice"])
        price = float(entry.get("price"))
        target = float(action.get("target"))
        stoploss = float(action.get("stoploss"))
        spacer = max(0, min(22, int(22*(refprice-stoploss)/(price-stoploss))))
        spacer += max(0, min(17, int(17*(refprice-price)/(target-price))))
        Log(" "*spacer + "| last:"+'{:.8f}'.format(refprice))
        Log("| stoploss:" + '{:.8f}'.format(stoploss) + 
            " | buy:"+'{:.8f}'.format(price) + 
            " | target:"+'{:.8f}'.format(target)+" |")
        if (refprice <= stoploss):
            if (action.get("countdown") == None):
                action.set("countdown", str(DEFAULT_COUNTDOWN))
            countdown = int(action.get("countdown"))
            Log("stoploss countdown:" + str(countdown))
            if (countdown <= 0):
                Log("stoploss process launched")
                #check minimum trade
                minimumtradepair = Get_Minimum_Trade_Amount(pair)
                minimumamount = minimumtradepair/bidprice
                minimumamount = float('{:.8f}'.format(minimumamount))
                Output = api.query("GetBalance", {'Currency':currency})
                amount = float(Output["Data"][0]["Total"])
                available = float(Output["Data"][0]["Available"])
                Log("bidprice*amount:"+'{:.8f}'.format(bidprice*amount))
                Log("available:"+'{:.8f}'.format(available))
                if (bidprice*amount > minimumtradepair):
                    Output = api.query("CancelTrade", {'Type':'TradePair', 
                                                       'TradePairId':pairid})
                    Log(Output)
                    time.sleep(7)
                else:
                    Log("trade not canceled")
                Output = api.query("GetBalance", {'Currency':currency})
                available = float(Output["Data"][0]["Available"])
                print ("available:"+'{:.8f}'.format(available))
                if (available>minimumamount):
                    Output = api.query("SubmitTrade", {'TradePairId':pairid, 
                                                       'Type':'Sell', 
                                                       'Rate':bidprice, 
                                                       'Amount':available})
                    Log("Exit trade sent")
                    Log(Output)
                    time.sleep(15)
                else:
                    Log("trade not submitted")
            else:
                action.set("countdown", str(countdown-1))
        else:
            if (action.get("countdown") != None):
                del action.attrib["countdown"]

        price = float(entry.get("price"))
        baseamount = float(header.get("amount"))
        amount = baseamount/price
        Output = api.query("GetBalance", {'Currency':currency})
        if (Output["Data"] != []):
            total = float(Output["Data"][0]["Total"])
            if (total==0.0):
                    action.set("status", "ready")
                    action.set("date", str(datetime.datetime.now()))
            Log("check amount {:.8f}".format(total))
        Log("           | {:.8f}".format(amount))

def Execute_Audit(header, entry, action, audit):
    """
    Method to handle the audit stage of an order. Calculate the profit/perf of
    a trade.
    header    (req) - Header xml object from the xml ordee config file
    entry     (req) - Entry xml object from the xml ordee config file
    action    (req) - Action xml object from the xml ordee config file
    audit     (req) - Audit xml object from the xml ordee config file
    """
    pair = header.get("pair")
    indate = datetime.datetime.strptime(header.get("date"), 
                                        "%Y-%m-%d %H:%M:%S.%f")
    nowdate = datetime.datetime.now()
    if action.get("date") != None :
        outdate = datetime.datetime.strptime(action.get("date"), 
                                             "%Y-%m-%d %H:%M:%S.%f")
        Log("pending till "+str(outdate + datetime.timedelta(hours=1)))
    else:
        Log("no audit (no data)")
        outdate = nowdate
        audit.set("status", "ready")
    if(nowdate > (outdate + datetime.timedelta(hours=1)) ) : 
        TotalBuy = 0.0
        TotalSell = 0.0
        TotalFees = 0.0
        RawPerf = 0.0
        NetPerf = 0.0
        Output = api.query("GetTradeHistory", {'Market':pair, 'Count':25})
        if (Output["Data"] != []):
            for line in Output["Data"]:
                linedate_str = str(line["TimeStamp"]).replace("T"," ")[:-2]+"0"
                linedate = datetime.datetime.strptime(linedate_str,
                                                      "%Y-%m-%d %H:%M:%S.%f")
                linedate = linedate + datetime.timedelta(hours=1)
                if (linedate > (indate + datetime.timedelta(hours=-1)) and 
                    linedate < (outdate + datetime.timedelta(hours=1))) :
                    if(line["Type"] == "Buy"):
                        TotalBuy = TotalBuy + line["Total"]
                        TotalFees = TotalFees + line["Fee"]
                    if(line["Type"] == "Sell"):
                        TotalSell = TotalSell + line["Total"]
                        TotalFees = TotalFees + line["Fee"]
    
            audit.set("Buy", '{:.8f}'.format(TotalBuy))
            audit.set("Sell", '{:.8f}'.format(TotalSell))
            audit.set("Fees", '{:.8f}'.format(TotalFees))
            RawProfit = TotalSell - TotalBuy
            audit.set("RawProfit", '{:.8f}'.format(RawProfit))
            NetProfit = TotalSell - TotalBuy - TotalFees
            audit.set("NetProfit", '{:.8f}'.format(NetProfit))
            if(TotalBuy > 0):
                RawPerf = RawProfit/TotalBuy
            audit.set("RawPerf", '{:.8f}'.format(RawPerf))
            if(TotalBuy > 0):
                NetPerf = NetProfit/TotalBuy
            audit.set("NetPerf", '{:.8f}'.format(NetPerf))
            audit.set("status", "ready")
            
def Log(message):
    """
    Method to write in the log a the message passed in the parameters:
    message  (req) - Message (string)
    """
    print(message)

def Get_Child_By_Name(root, name):
    """
    Method to get the child element of an XML node. It returns a xml object. 
    The parameters are : 
    root     (req) - XML root object
    name     (req) - Child name tag to search 
    """
    for phase in root:
        if (phase.tag == name):
            return phase 
    return None

def Initialisation():
    """
    Method to create the necessary resource folders for the pipeline to operate
    No parameters.
    """
    folders = {"in":[],"work":[],"out":[],"logs":[],}
    Create_Folder(DATA_PATH)
    for folder in folders.keys():
        Create_Folder(DATA_PATH, folder)
        for subfolder in folders[folder]:
            Create_Folder(DATA_PATH, folder, subfolder)

def Create_Folder(*args):
    """
    Method to create folders recursively, parameters = Folders tree
    """
    if len(args) > 1:
        Create_Folder(*args[:-1])
    path = os.path.join(*args)
    if not os.path.exists(path):
        os.mkdir(path)

def Get_Cache(method, req = None):
    """
    Method used to call the api or retrieve the data in cache if the api has 
    already been called with the same parameters. I had to create this method 
    to fix some bugs caused by the api refusing too many calls. Parameters
    are the same than those passed to the api
    method   (req) - api method called
    req      (opt) - List or dictionnary of parameters to pass to the api
    """
    data = method
    if req:
     for param in req:
         data += '|' + str(param)
    if data in CACHE.keys():
        Output = CACHE[data]
    else:
        Output = api.query(method, req)
        CACHE[data] = Output
    return Output

if __name__ == "__main__":
    Main()


