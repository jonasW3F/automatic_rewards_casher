import { Command } from "commander";
import { load } from "js-yaml";
import { readFileSync, createWriteStream, existsSync, WriteStream } from "fs";
import { ApiPromise, WsProvider } from "@polkadot/api";
import { KeyringPair, KeyringPair$Json } from "@polkadot/keyring/types";
import { Keyring } from "@polkadot/keyring";
import { createLogger } from "@w3f/logger";
import '@polkadot/api-augment';
import { assert } from "console";

interface Config {
  end_point: string;
  rewardsDestination: RewardsDestination;
  keystore: Keystore;
}

interface RewardsDestination {
  primaryDestinationAddress: string;
  primaryDestinationShare: string;
  secondaryDestinationAddress: string;
}

interface Keystore {
  walletFilePath: string;
  password: string;
}

function abort() {
  process.exit(1);
}

const start = async (args: { config: string }): Promise<void> => {
  const log = createLogger("debug");

  // Parse Config
  log.debug(`Reading config from file ${args.config}`);
  const config = load(readFileSync(args.config, "utf8")) as Config;

  // Parse and decode provided account.
  log.debug(`Reading account key from ${config.keystore.walletFilePath}`);
  const keyring = new Keyring({ type: "sr25519" });
  const json = JSON.parse(readFileSync(config.keystore.walletFilePath, "utf8"));
  const account = keyring.addFromJson(json);
  account.decodePkcs8(config.keystore.password);

  if (account.isLocked) {
    log.error("Failed to initialize keystore, account is locked");
    abort();
  }

  // Initialize RPC endpoint.
	const wsProvider = new WsProvider(config.end_point);
	const api = await ApiPromise.create({ provider: wsProvider });
  
  const { data: balance } = await api.query.system.account(account.address);
  const decimals = api.registry.chainDecimals;
  const base = 10**Number(decimals);
  const dm = Number(balance.free) / base;
  log.debug(`Account ${account.address} has free balance of: ${dm} ${api.registry.chainTokens}`);

  const existentialDeposit = Number(api.consts.balances.existentialDeposit) / base;
  // Sending funds to addresses
  const share = parseFloat(config.rewardsDestination.primaryDestinationShare) / 100;
  log.debug(`Share split: ${share * 100}%`);

  // We need to handle the ED of three addresses. First, we need to make sure that the balance of the Account we send from will not fall
  // below the ED after sending it. Afterwards, we need to make sure that funds do not get lost on the primaryDestinationAddress and 
  // secondaryDestinationAddress. There are two options here. Either the available_funds * share and available_funds * (1 - share) are both
  // above the ED or, if they are below the ED, both primaryDestinationAddress and secondaryDestinationAddress are already having more than the ED.
  // We only want to execute the transactions if no funds are lost anywhere, this should work without user interaction.

  // Get primary and secondary account balances.
  const { data: balance_primaryDestination } = await api.query.system.account(config.rewardsDestination.primaryDestinationAddress);
  const { data: balance_secondaryDestination } = await api.query.system.account(config.rewardsDestination.secondaryDestinationAddress);

  var primaryDestinationOverED;
  var secondaryDestinationOverED;

  // We check whether the two destination addresses have the ED.
  if((Number(balance_primaryDestination.free) / base) >= existentialDeposit){
    primaryDestinationOverED = true;
  } else {
    primaryDestinationOverED = false;
  }

  if((Number(balance_secondaryDestination.free) / base) >= existentialDeposit){
    secondaryDestinationOverED = true;
  } else {
    secondaryDestinationOverED = false;
  }

  // We make sure that the remaining funds are exactly the ED.
  // TODO: We need to reserve funds for two upcoming transactions. How do we do this? Right now, I just heuristically reserve 
  // 2x a tenth of the ED.
  const available_funds = (Number(balance.free)/ base) - existentialDeposit - 2*(existentialDeposit/10);

  // Check if we send the available_funds, that the remaining balance (minus ED) is positive. This is the first condition that needs to hold
  // in all cases.
  assert(available_funds >= 0)

  const primaryTransfer = available_funds * share;
  const secondaryTransfer = available_funds * (1-share);

  // Abort if any of the destination addresses does not have enough ED and the transfer would be below ED. In the case that we do not send
  // anything to the address, we can proceed even if it is without ED.
  if(primaryDestinationOverED == false && (primaryTransfer < existentialDeposit) && primaryTransfer != 0){
    abort();
  }

  if(secondaryDestinationOverED == false && (secondaryTransfer < existentialDeposit) && secondaryTransfer != 0){
    abort();
  }

  log.debug(`Will send ${primaryTransfer} ${api.registry.chainTokens} to ${config.rewardsDestination.primaryDestinationAddress}`)
  log.debug(`Will send ${secondaryTransfer} ${api.registry.chainTokens} to ${config.rewardsDestination.secondaryDestinationAddress}`)
  
  const transfers = [
    api.tx.balances.transfer(config.rewardsDestination.primaryDestinationAddress, Math.round(primaryTransfer * base)),
    api.tx.balances.transfer(config.rewardsDestination.secondaryDestinationAddress, Math.round(secondaryTransfer * base))
  ];
  await api.tx.utility
  .batch(transfers)
  .signAndSend(account, ({ status }) => {
    if (status.isInBlock) {
      console.log(`included in ${status.asInBlock}`);
    }
  });
  wsProvider.disconnect();
};

function delay(ms: number) {
  return new Promise( resolve => setTimeout(resolve, ms) );
}

const command = new Command()
  .description("Execute the reward transactions")
  .option("-c, --config [path]", "Path to config file.", "./config/config.yaml")
  .action(start);

command.parse();
