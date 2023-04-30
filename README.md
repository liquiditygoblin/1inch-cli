

# 1inch-cli

A command-line interface for the [1inch.exchange](https://1inch.exchange/) decentralized exchange aggregator.

Supports on-chain trading and advanced order types, letting you TWAP in to $PEPE and take profit with a trigger order!

WARNING: this is in beta, txs could revert, things might break, please be careful with your wallet and your funds when using this, I am not responsible for any losses

1inch recently blocked cloud providers from accessing theit API, you may run into issues running this from a major data centre, please open a PR if you have any work arounds!

## Requirements

* Python 3.8 or higher

## Installation

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

Next, add your private key to environment variables, if you don't know where to find one, follow this tutorial to get your private key from metamask https://support.metamask.io/hc/en-us/articles/360015289632-How-to-export-an-account-s-private-key

WARNING: this is an unencrypted hot wallet, be careful with your private key. Future updates will include a more secure way to store your private key (keystores & eventually hardware wallet), but for now, this is the only way to use the CLI.
```bash
export PRIVATE_KEY="0x<YOUR_KEY_HERE>"
```

## Usage

To use the 1inch cli, run:

```
$ python main.py
```

The script will guide you through the process of selecting the tokens to swap and the amount to exchange. 

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

