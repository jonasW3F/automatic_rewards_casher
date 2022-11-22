#!/opt/homebrew/bin/python3

import time
from time import sleep
import os
import requests
import urllib.parse
import hashlib
import hmac
import base64
import subprocess

# Read Kraken API key and secret stored in environment variables
api_url = "https://api.kraken.com"

api_key = os.environ['API_KEY_KRAKEN']
api_sec = os.environ['API_SEC_KRAKEN']

asset = 'KSM'
fiat = 'EUR'
pair = asset + fiat


def get_kraken_signature(urlpath, data, secret):

    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())
    return sigdigest.decode()

def makeRequest(uri_path, data, api_key, api_sec):
    headers = {}
    headers['API-Key'] = api_key
    # get_kraken_signature() as defined in the 'Authentication' section
    headers['API-Sign'] = get_kraken_signature(uri_path, data, api_sec)
    req = requests.post((api_url + uri_path), headers=headers, data=data)
    return req

balances = makeRequest('/0/private/Balance', {
    "nonce": str(int(1000*time.time()))
}, api_key, api_sec)

dot_balance = float(balances.json()['result']['DOT'])
ksm_balance = float(balances.json()['result']['KSM'])

traded_dot = False
traded_ksm = False
traded_fiat = False
profit_dot = 0
profit_ksm = 0

if(dot_balance < 0.2 and ksm_balance < 0.1):
    exit()



if(dot_balance >= 0.2):
    sell = makeRequest('/0/private/AddOrder', {
        "nonce": str(int(1000*time.time())),
        "ordertype": "market",
        "type": "sell",
        "volume": str(dot_balance),
        "pair": 'DOTEUR',
    }, api_key, api_sec)
    sleep(10)
    tx_id_dot = sell.json()['result']['txid'][0]
    traded_dot = True


if(ksm_balance >= 0.1):
    sell = makeRequest('/0/private/AddOrder', {
        "nonce": str(int(1000*time.time())),
        "ordertype": "market",
        "type": "sell",
        "volume": str(ksm_balance),
        "pair": 'KSMEUR',
    }, api_key, api_sec)
    sleep(10)
    tx_id_ksm = sell.json()['result']['txid'][0]
    traded_ksm = True

if(traded_dot == True):
    trade_dot = makeRequest('/0/private/QueryOrders', {
        "nonce": str(int(1000*time.time())),
        "txid": tx_id_dot,
        "trades": False
    }, api_key, api_sec)
    sleep(10)
    profit_dot = trade_dot.json()['result'][tx_id_dot]['cost']

if(traded_ksm == True):
    trade_ksm = makeRequest('/0/private/QueryOrders', {
        "nonce": str(int(1000*time.time())),
    	"txid": tx_id_ksm,
    	"trades": False
	}, api_key, api_sec)
    sleep(10)
    profit_ksm = trade_ksm.json()['result'][tx_id_ksm]['cost']

total_profit_eur = float(profit_dot) + float(profit_ksm)

sleep(10)

balances = makeRequest('/0/private/Balance', {
    "nonce": str(int(1000*time.time()))
}, api_key, api_sec)
sleep(10)
eur_balance = float(balances.json()['result']['ZEUR'])

if(eur_balance >= 5):
    traded_fiat = True
    sell = makeRequest('/0/private/AddOrder', {
        "nonce": str(int(1000*time.time())),
        "ordertype": "market",
        "type": "sell",
        "volume": str(eur_balance),
        "pair": 'EURCHF',
    }, api_key, api_sec)
    sleep(10)
    tx_id_eur = sell.json()['result']['txid'][0]

# To give Kraken backend time
if(traded_fiat == True):
    trade_eur = makeRequest('/0/private/QueryOrders', {
    	"nonce": str(int(1000*time.time())),
    	"txid": tx_id_eur,
    	"trades": False
	}, api_key, api_sec)
    sleep(10)
    profit_eur = trade_eur.json()['result'][tx_id_eur]['cost']
    profit_eur = float(profit_eur)
    profit_eur = round(profit_eur, 2)

dot_balance = round(dot_balance, 2)
ksm_balance = round(ksm_balance, 2)
total_profit_eur = round(total_profit_eur, 2)


message = 'Hey Boss, I just cashed your rewards on Kraken. I sold ' + str(dot_balance) + ' DOT and ' + str(ksm_balance) + ' KSM for a total of ' + str(total_profit_eur) + ' EUR.'

if(traded_fiat == True):
    message =  message + " I also converted EUR to CHF, which yielded " + str(profit_eur) + " CHF." 

balances = makeRequest('/0/private/Balance', {
    "nonce": str(int(1000*time.time()))
}, api_key, api_sec)
sleep(10)

final_chf_balance = float(balances.json()['result']['CHF'])
final_eur_balance = float(balances.json()['result']['ZEUR'])

message = message + " Your current EUR balance is " + str(final_eur_balance) + " EUR" + " and your current CHF balance is " + str(final_chf_balance) + " CHF." 
subprocess.run(["telegram-send",
                message])