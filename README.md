# Automatic Staking Rewards Casher

## Introduction

This collection of scripts enable you to set up an infrastructure that automatically cashes (part of) your staking rewards to any asset available on Kraken. Once set up, it realizes the "mental accounts" that some of us have for staking rewards. Namely, some portion of it needs to be reserved for taxes while the other is free to use for whatever we like. This setup allows you to automatically cash out regularly and thereby achieve average prices that protect you from the tax-risk caused by high volatile phases. As this happens all automatically, you don't have to worry about it and reduce the risk of using funds that should be reserved for taxes or having to sell in bad marketconditions to cover expenses. There are three key stages to the process.

1) Automatically send all transferrable balance of an account to two other accounts (with a variable ratio set by the user) (thanks to [Nexus2k](https://github.com/Nexus2k/rewards-sender)).
2) Executing certain trading / withdrawal orders on Kraken through an API wrapper. In this example, the script converts all available DOT to EUR to CHF and then withdraws all CHF to a bank account. This can, of course, be adjusted to virtually any desired flow that fits the preferences of the user.
3) After all orders are executed, a telegram message is sent to the user to their private chat with their own bot informing about various details of the trades and/or current balances.

Everything is orchestrated through a cronjob that triggers the scripts in the correct order. The user can adjust the frequency with which this occurs. I would strongly recommend to create a dedicated Kraken account and never leave significant amounts there, as this setup requires you to handle and store API keys. It is also important to separate the account from your main account to avoid the auto_sell script to access funds it was not suppose to.

### Risks
This setup exposes the private key of the account that the funds are sent from (usually where you gather your staking rewards), the API keys to Kraken as well as messages via telegram. There are several risks involved:
1) Funds can be stolen if a hacker gets access to the private key of the account that the rewards-sender is accessing. Sending the rewards frequently to Kraken and never have too much funds on the account reduces the impact of a leak.
2) The `auto_sell.py` script requires API keys that potentially have permissions for trading and even withdrawals. Leaking these keys could also lead in loss of funds, so it is highly advisable to make a separate Kraken account only for this process and not store large amounts of funds for long.
3) The usual risks involved with handling private keys on a setup that requires several libraries to work. A particular example is the library to send Telegram messages with all risks associated to privacy. 

### Disclaimer
**I don't take any responsibility for lost funds. Review the code yourself.**

# Setup

## Prerequisits
1) Set up a linux server to use for running the scripts. Ideally a Raspberry Pi or some hosted service.
2) Clone this repo to get all the scripts necessary.
3) Make a new (!) Polkadot account which you set as payee for you staking stashes.
4) Make a new Account with Kraken and create new API Key with all permissions necessary.
5) Get the deposit address for your Polkadot Account on Kraken (the `primaryDestinationAddress` in the example setup here).
6) Specify the second account to set the remainder of the rewards to (the `secondaryDestinationAddress` in 
the following). Note, you could even make yet another kraken account, have a copy of the auto_sell.py script (with the changed API keys) and have a different routine for that account.


## Step 1: Automatically send staking rewards
In this step, we will set up the script that automatically sends your staking rewards to two different addresses (`primaryDestinationAddress` and `secondaryDestinationAddress`).

2) Export the newly created account as .json
3) Rename it to key.json and move it to rewards-sender/config
4) Rename `sample.config.yaml` to `config.yaml`
5) Edit the `config.yaml` with any text editor
6) Insert your addresses from before. For example your `primaryDestinationAddress` is the deposit address with Kraken. Your `secondaryDestinationAddress` is another on-chain account.
7) Adjust the `primaryDestinationShare` to your liking. Everytime the script runs, it will take this share of the available balance and send it to the `primaryDestinationAddress`. Note, that this amount should exceed the existential deposit, otherwise the script will terminate (or a loss of funds could occur).
8) Replace the password necessary to unlock the account.
9) Make sure you defined the correct endpoint. `wss://rpc.polkadot.io` for Polkadot and `wss://kusama-rpc.polkadot.io` for Kusama.
10) Move your terminal to the rewards-sender folder and run `yarn install && yarn build`.

## Step 2: Set Up Telegram Notifications
We want to receive Telegram messages from a bot with further information on the trades. Luckily, this is rather easy. I follow mostly 
[this](https://hackernoon.com/how-to-create-a-simple-bash-shell-script-to-send-messages-on-telegram-lcz31bx) tutorial.

1) Open your telegram
2) Find the bot creator bot @BotFather
3) Add a new bot 
4) Create a new channel
5) Add the bot as admin
6) Write a random message in the channel
7) go to https://api.telegram.org/botID/getUpdates - replace "ID" with the token that was given to you after creating the bot. Leave the "bot" there.
8) Find the "id" entry with the "-" in front.
9) Edit the `telegram-send.sh` script with any text editor and add the channel ID and bot token.
10) Make the script executable ```chmod +x telegram-send.sh```
11) Test the script by writing `./telegram-send "test"` - the message should appear in the channel on telegram.
12) Move the script to `/usr/local/bin`


## Step 3: Setting up your Kraken Account
1) Get your API keys from Kraken
2) Store the keys in `\api_keys` as `api_key` and `api_sec`.

## Step 4: Adjusting the auto_sell script
Adjust the process in `auto_sell.py` to your needs. In the example script, we convert all DOT to EUR, then CHF and then withdraw the CHF. For withdrawals, you need to change the `YOURKEY` identifier to the name you gave the withdrawal method.

## Step 5: Setting up the cronjob
We want to create a script that triggers the sending of rewards and then sleeps for a while (waiting for a confirmed deposit) and executes our trade routine. 

1) Open the `scheduler.sh` script with any text editor and adjust the paths.
2) Make the script executable `chmod +x scheduler.sh`
3) Make a new cronjob with your desired properties. `crontab -e`
4) For example, the following cronjob triggers the the process once every week. For further help, check the [Cronjob Guru](https://crontab.guru/). We also want 
to write the output to a log-file.
    * `@weekly /home/user/scheduler.sh >> /home/user/scheduler.log`
    
You should now be set up.

## Step 6: Testing
* Fund your staking rewards account with a small but sufficient amount of tokens. Note, that you will need to have enough tokens to cover the ED of the staking rewards account, 2x transaction costs. In addition, enough tokens need to be send to the `primaryDestinationAddress` and `secondaryDestinationAddress` to cover each ED. The rewards-sender allows to send less than the ED when the destination already has ED, though.

# Ideas for future improvements

* Instead of converting EUR immediately to fiat, we could **automatically stake the EUR** at Kraken and gain a few % of yield.
