# Automatic Staking Rewards Casher

## Introduction

This collection of scripts enable you to set up an infrastructure that automatically cashes (part of) your staking rewards. Once set up, it realizes the "mental 
accounts" that we have for staking rewards. Namely, some portion of it needs to be reserved for taxes while the other is free to use for whatever you like. By 
using this setup, you will cash out regularly and thereby achieve average prices that protect you from the tax-risk caused by high volatility phases. As this 
happens all automatically, you don't have to worry about it and reduce the risk of using funds that should be reserved for taxes. There are three key stages to 
the process.

1) Automatically send staking rewards to kraken from your account that receives the staking rewards (thanks to 
[Nexus2k](https://github.com/Nexus2k/rewards-sender)). 
2) Automatically sell everything on Kraken (from DOT and KSM to EUR to CHF).
3) Receive notifications on Telegram about the trades.

All stages are made via cronjobs that - in my case - run every week. Personally, I use a separate kraken account for the rewards (to reduce the risk of selling 
DOT/KSM that I did not want to) and a second address that keeps the rewards.

### Risks
This setup exposes the private keys of the account that the funds are sent from (usually where you gather your staking rewards), the API keys to Kraken as well 
as messages via telegram. The idea is to keep the risk here to a minimum by:
1) Sending the rewards frequently to kraken (the maximum that a hacker could steal is the accumulated rewards during that phase).
2) Make a separate kraken account that is only made for cashing rewards.
3) Generally, I do not trust Telegram very much. 

### Disclaimer
I don't take any responsibility for lost funds. Check the code that you copy&paste and execute yourself.

# Setup

## Prerequisits
1) Set up a linux server to use for running the scripts.
2) Clone this repo to get all the scripts necessary.
3) Make a new (!) account where your staking rewards will go.
4) Make a new Account at Kraken and set up a new API Key with all permissions except deposit and withdrawal.
5) Get the deposit address for your Polkadot or Kusama on Kraken (the **primaryDestinationAddress** in the following).
6) Set up another account and get the Polkadot or Kusama address where you want to send the other part of the rewards (the **secondaryDestinationAddress** in 
the following).


## Step 1: Automatically send staking rewards
In this step, we will set up the script that automatically sends your staking rewards to two different addresses (`primaryDestinationAddress` and 
`secondaryDestinationAddress`).

2) Export the account created before as .json
3) Rename it to key.json and move it to rewards-sender/config
4) Rename `sample.config.yaml` to `config.yaml`
5) Edit the `config.yaml` with any text editor
6) Insert your addresses from before. For example your `primaryDestinationAddress` is the deposit address with Kraken. Your `secondaryDestinationAddress` is 
another on-chain account.
7) Adjust the `primaryDestinationShare` to your liking. Everytime the script runs, it will take this share of the available balance and send it to the 
`primaryDestinationAddress`. Note, that this amount should exceed the existential deposit, otherwise the script will terminate (or a loss of funds could occur).
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
2) Store your keys as environmental variables.
    - set the key as: `api_key` and the secret as `api_sec`


## Step 4: Setting up the cronjob
We want to create a script that triggers the sending of rewards and then sleeps for a while and executes the kraken trades. 

1) Open the `scheduler.sh` script with any text editor and adjust the paths.
2) Make the script executable `chmod +x scheduler.sh`
3) Make a new cronjob with your desired properties. `crontab -e`
4) For example, the following cronjob triggers the the process once every week. For further help, check the [Cronjob Guru](https://crontab.guru/). We also want 
to write the output to a log-file.
    * `@weekly /home/user/scheduler.sh >> /home/user/scheduler.log`
    
You should now be set up.

## Step 5: Testing
* You should test your setup by adjusting the Cronjob to trigger more frequently (e.g., towards the next hour or half-hour) and see if everything works.
* To do so, fund your staking rewards account with sufficient tokens. Note, that you will need to have enough tokens to cover the ED of the staking rewards 
account, 2x transaction costs. In addition, enough tokens need to be send to the `primaryDestinationAddress` and `secondaryDestinationAddress` to cover each ED. 
The rewards-sender allows to send less than the ED when the destination already has ED, though.

# Ideas for future improvements

* Make the process be able to handle multiple accounts (e.g., one Kusama and one Polkadot).
* Instead of converting EUR immediately to fiat, we could **automatically stake the EUR** at Kraken and gain a few % of yield.
