#!/usr/bin/python3

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

# Define the path to the API keys directory
keys_dir = os.path.join(os.path.dirname(__file__), 'api_keys')

# Function to read a key from a file
def read_key(file_name):
    try:
        with open(os.path.join(keys_dir, file_name), 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        raise Exception(f"File {file_name} not found in {keys_dir}")

api_key = read_key('api_key')
api_sec = read_key('api_sec')

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

## Here you can specify your process. In this example, we sell all DOT for EUR, all EUR for CHF and then withdraw all CHF.
## If you withdraw fiat, make sure to replace "YOURKEY" (usually the name you gave the withdrawal method).

# Step 1: Sell all DOT for EUR
balances = makeRequest('/0/private/Balance', {"nonce": str(int(1000*time.time()))}, api_key, api_sec)
dot_balance = float(balances.json()['result']['DOT'])

if dot_balance >= 0.6:  # 0.6 DOT is the minimum volume
    sell_dot_for_eur = makeRequest('/0/private/AddOrder', {
        "nonce": str(int(1000*time.time())),
        "ordertype": "market",
        "type": "sell",
        "volume": str(dot_balance),
        "pair": 'DOTEUR',
    }, api_key, api_sec)
    sleep(10)

    # Step 2: Sell all EUR for CHF
    balances = makeRequest('/0/private/Balance', {"nonce": str(int(1000*time.time()))}, api_key, api_sec)
    eur_balance = float(balances.json()['result']['ZEUR'])
    
    if eur_balance >= 0.5:  # 0.5 EUR is the minimum volume
        sell_eur_for_chf = makeRequest('/0/private/AddOrder', {
            "nonce": str(int(1000*time.time())),
            "ordertype": "market",
            "type": "sell",
            "volume": str(eur_balance),
            "pair": 'EURCHF',
        }, api_key, api_sec)
        sleep(10)

        # Step 3: Withdraw CHF
        balances = makeRequest('/0/private/Balance', {"nonce": str(int(1000*time.time()))}, api_key, api_sec)
        chf_balance = float(balances.json()['result']['CHF'])
        
        if chf_balance > 2: # 2 CHF is the minimum withdrawal
            withdraw_chf = makeRequest('/0/private/Withdraw', {
                "nonce": str(int(1000*time.time())),
                "asset": 'CHF',
                "key": 'YOURKEY',
                "amount": str(chf_balance)
            }, api_key, api_sec)
            sleep(10)
            print("Withdrawal of CHF to account 'YUH' initiated.")
        else:
            print("Not enough CHF to initiate withdrawal.")
    else:
        print("Not enough EUR to trade for CHF.")
else:
    print("Not enough DOT to trade for EUR.")

message = 'LIFE: Hey Boss, I just cashed your rewards on Kraken. I sold ' + str(dot_balance) + ' DOT for ' + str(chf_balance) + ' CHF.'
message += " Then, I withdrew " + str(chf_balance) + " CHF."

subprocess.run(["telegram-send",
                message])