# rewards-sender

This tool sends funds from a given Polkadot account to two other accounts. The ratio of how the funds are split are defined by the split in the config file.

## Usage

1. Copy `sample.config.yaml` to `config.yaml` and update the values
1. Export a Polkadot.js.org Wallet to json and store it under `config/key.json`
1. Build the script using `yarn install && yarn build` (only needed once or when you change it)
1. Run the script using `yarn start`

## Tips & Tricks

- To send funds on Kusama, just change the `end_point` entry to `wss://kusama-rpc.polkadot.io` and change everything accordingly.