

# 1inch-cli

A command-line interface for the [1inch.exchange](https://1inch.exchange/) decentralized exchange aggregator.

Supports on-chain trading and advanced order types, letting you TWAP in to $PEPE and take profit with a trigger order!

WARNING: this is in beta, txs could revert, things might break, please be careful with your wallet and your funds when using this, I am not responsible for any losses

1inch recently blocked cloud providers from accessing their API, you may run into issues running this from a major data centre, please open a PR if you have any work arounds!

## Requirements

* Python 3.8 or higher

## Installation


### Install from script (recommended)

paste the following into your terminal to install 1inch-cli
```commandline
curl -L https://raw.githubusercontent.com/liquiditygoblin/1inch-cli/main/install.sh | bash
```
change directory to 1inch-cli
```commandline
cd  1inch-cli
```
Then to run 1inch-cli just run
```commandline
./run.sh
```
	
Upon running the script for the first time, you will be prompted to create a keystore, a keystore is a password protected way to store your private key, it is more secure than storing your private key in plain text. If you do not want to create a keystore, you can just press enter and continue without a wallet. You will then be asked to enter your private key, paste it in and press enter. You will then be prompted to create a password, make sure to appropriately back up both your private key/seed phrase and your password. Your keystore will then be created in `keystore.json` and you will be able to use 1inch-cli.
To use a new wallet, simply move `keystore.json` out of the directory and run `./run.sh` again, you will be prompted to create a new keystore.

if you don't know where to find your private key, follow this tutorial to get your private key from metamask https://support.metamask.io/hc/en-us/articles/360015289632-How-to-export-an-account-s-private-key
### Install from source

Clone the repository:

```
$ git clone https://github.com/user/repo.git
$ cd repo/1inch-cli
```

Create a virtual environment and install the required packages:

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

To use the 1inch cli, run:

```
$ python main.py
```

The script will guide you through the process of selecting the tokens to swap and the amount to exchange. 

## Usage

Upon running the script, the user will be prompted with many select modals, just type the number of the choice you'd like and hit enter.

To select a token, either type the symbol of the token you'd like to select or the paste the address of the token.


## Features

* Select the chain (Ethereum, Arbitrum, etc.) and the RPC endpoint
* Select the token list
* Select the token pair to swap
* Enter the amount to swap or use the maximum available balance
* Get a quote for the swap
* Advanced swap types, TWAP & Trigger

## Contributing

Contributions are welcome! Please feel free to submit a pull request or an issue.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Referral Notice

1inch-cli takes a small referral fee on each trade, if you find this tool useful & wish to self refer or remove this, please consider donating at `0xdb5D4e46AeE4Eb45768460abeEb03b6fB813819d`
