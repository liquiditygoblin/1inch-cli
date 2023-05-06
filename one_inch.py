import getpass
import requests
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, EthereumTesterProvider
import web3
from web3.middleware import construct_sign_and_send_raw_middleware
import os
import json

from util import open_json


ERC20_ABI = open_json("abi/ERC20.json")
ONE_INCH_ABI = open_json("abi/AggregationRouterV5.json")
ONE_INCH_ROUTER = "0x1111111254fb6c44bAC0beD2854e76F90643097d"
REFERRAL = "0xdb5D4e46AeE4Eb45768460abeEb03b6fB813819d"

NATIVE_TOKEN = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"


class OneInch:
    """
    OneInch class
    """

    def __init__(self, chain_id, rpc_url, currency, explorer_url):
        """
        OneInch class constructor
        :param chain_id:
        :param rpc_url:
        :param currency:
        :param explorer_url:
        """
        self.chain_id = chain_id
        self.rpc_url = rpc_url
        self.currency = currency
        self.explorer_url = explorer_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        self.one_inch_contract = self.w3.eth.contract(address=ONE_INCH_ROUTER, abi=ONE_INCH_ABI)

        self.has_wallet = False
        keystore_file = './keystore.json'
        if os.path.isfile(keystore_file):
            priv_key = Account.decrypt(open_json(keystore_file), getpass.getpass(prompt='Input keystore password: '))
            self.account = Account.from_key(priv_key)
            self.has_wallet = True
        else:
            print("keystore file not found, creating one")
            private_key = getpass.getpass(prompt='Input private key: ')
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            try:
                self.account = Account.from_key(private_key)
            except:
                print("invalid private key, continuing without...")
                return
            print(f"private key valid, account: {self.explorer_url}address/{self.account.address}\ncreating keystore file")
            for i in range(3):
                password = getpass.getpass("Enter a password for the keystore file: ")
                password2 = getpass.getpass("Confirm password: ")

                # Check that the passwords match
                if password != password2:
                    print("Passwords do not match")
                    print*(f"Please try again, attempt{i+2}/3")
                else:
                    break
            if password != password2:
                print("Passwords do not match, continueing without...")
                return
            keystore = Account.encrypt(private_key, password=password)
            with open(keystore_file, 'w') as f:
                f.write(json.dumps(keystore))
            self.has_wallet = True
        """
        if private_key is not None:
            if not private_key.startswith("0x"):
                raise Exception("PRIVATE_KEY must start with 0x")

            self.account = Account.from_key(private_key)
            self.has_wallet = True

        elif keystore is not None:

            priv_key = Account.decrypt(open_json(keystore), getpass.getpass(prompt='Input keystore password: '))
            self.account = Account.from_key(priv_key)
            self.has_wallet = True
        
        else:
            print("PRIVATE_KEY/KEYSTORE environment variables are not set, continuing without them")
            self.has_wallet = False
        """
        if self.has_wallet:
            self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(self.account))

            print(f"Your hot wallet address is {self.account.address}")
            self.balance = self.w3.eth.get_balance(self.account.address)
            print(
                f"Your hot wallet balance is {OneInch.parse_float(self.w3.from_wei(self.balance, 'ether'))} {self.currency}")

    def get_quote(self, from_token_address, to_token_address, amount):
        """
        Get quote

        :param from_token_address: Token address of the source token
        :type from_token_address: str
        :param to_token_address: Token address of the destination token
        :type to_token_address: str
        :param amount: Amount of source token
        :type amount: str
        :return: Quote
        """


        from_token_address = self.w3.to_checksum_address(from_token_address)

        if amount < 0:
            if not self.has_wallet:
                print("Selected max amount is negative, but you don't have a wallet, so we'll use 100000")
                amount = 100000
            else:
                amount = self.get_balance(from_token_address)
        to_token_address = self.w3.to_checksum_address(to_token_address)
        url = f"https://api.1inch.io/v4.0/{self.chain_id}/quote?fromTokenAddress={from_token_address}&toTokenAddress={to_token_address}&amount={amount}&complexityLevel=3"
        response = requests.get(url=url).json()
        if self.has_wallet:
            allowance = self.get_readable_allowance(from_token_address)
            balance = self.get_readable_balance(from_token_address)
            print(f"Your balance is {balance}")
            print(f"Your approved swap amount is {allowance}")
            # print(f"Estimated gas: {response['estimatedGas']}")

        return response

    def get_swap(self, from_token_address, to_token_address, amount, slippage=0.1):
        """
        Get swap

        :param from_token_address: Token address of the source token
        :type from_token_address: str
        :param to_token_address: Token address of the destination token
        :type to_token_address: str
        :param amount: Amount of source token
        :type amount: str
        :param from_address: Address of the source token
        :type from_address: str
        :param slippage: Maximum slippage percentage (0.5% => 0.005)
        :type slippage: str
        :param disable_estimate: Disable gas estimate
        :type disable_estimate: bool
        :return: Swap
        """
        if not self.has_wallet:
            print("You need to set PRIVATE_KEY environment variable to perform a swap")
            return
        if self.get_allowance(from_token_address) < amount:
            print("You need to approve the swap first")
            return
        if self.get_balance(from_token_address) < amount:
            print("You don't have enough balance")
            return
        from_token_address = self.w3.to_checksum_address(from_token_address)
        to_token_address = self.w3.to_checksum_address(to_token_address)
        if amount < 0:
            amount = self.get_balance(from_token_address)
            if amount == 0:
                print("You don't have any balance, exiting...")
                exit()

        fee = min(max(0.2, slippage * 0.1), 3.0)
        url = f"https://api.1inch.io/v4.0/{self.chain_id}/swap?fromAddress={self.account.address}&fromTokenAddress={from_token_address}&toTokenAddress={to_token_address}&amount={amount}&slippage={slippage}&complexityLevel=3&fee={fee}&referrerAddress={REFERRAL}"
        response = requests.get(url=url).json()

        return response

    def send_swap(self, from_token_address, to_token_address, amount, slippage=0.1):
        from_token_address = self.w3.to_checksum_address(from_token_address)
        to_token_address = self.w3.to_checksum_address(to_token_address)
        values = self.get_swap(from_token_address, to_token_address, amount, slippage)
        value = 0
        if from_token_address == NATIVE_TOKEN:
            value = amount
        
        tx = {
            'to': ONE_INCH_ROUTER,
            'chainId': self.chain_id,
            'data': values["tx"]["data"],
            'gas': values["tx"]["gas"],
            'value': value,
            'gasPrice': int(values["tx"]["gasPrice"]),
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        }

        signed_tx = self.account.sign_transaction(tx)
        # Send the signed transaction
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"sent swap tx: {self.explorer_url}tx/{tx_hash.hex()}")
        print("awaiting confirmation...")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"swap confirmed in block {receipt['blockNumber']}")

    def get_balance(self, token_addr):
        """
        Get balance

        :param token_addr: Token address
        :type token_addr: str
        :return: Balance
        """
        token_addr = self.w3.to_checksum_address(token_addr)
        if token_addr == NATIVE_TOKEN:
            return self.w3.eth.get_balance(self.account.address)
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        return token_contract.functions.balanceOf(self.account.address).call()

    def get_allowance(self, token_addr):
        """
        Get allowance

        :param token_addr: Token address
        :type token_addr: str
        :return: Allowance
        """
        token_addr = self.w3.to_checksum_address(token_addr)
        if token_addr == NATIVE_TOKEN:
            return 2**255 - 1
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        return token_contract.functions.allowance(self.account.address, ONE_INCH_ROUTER).call()

    def get_readable_allowance(self, token_addr):
        """
        Get readable allowance
        :param token_addr:
        :return:
        """
        token_addr = self.w3.to_checksum_address(token_addr)

        if token_addr == NATIVE_TOKEN:
            return "Unlimited"
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        allowance = token_contract.functions.allowance(self.account.address, ONE_INCH_ROUTER).call()
        return f"{OneInch.parse_float(allowance / 10 ** token_contract.functions.decimals().call())} {token_contract.functions.symbol().call()}"

    def get_readable_balance(self, token_addr):
        """
        Get readable balance
        :param token_addr:
        :return:
        """
        token_addr = self.w3.to_checksum_address(token_addr)

        if token_addr == NATIVE_TOKEN:
            balance = self.w3.eth.get_balance(self.account.address)
            return f"{OneInch.parse_float(balance / 10 ** 18)} {self.currency}"
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(self.account.address).call()
        return f"{OneInch.parse_float(balance / 10 ** token_contract.functions.decimals().call())} {token_contract.functions.symbol().call()}"

    def approve_token(self, token_addr, amount):
        token_addr = self.w3.to_checksum_address(token_addr)
        if token_addr == NATIVE_TOKEN:
            print("You don't need to approve native token")
            return
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        tx = token_contract.functions.approve(ONE_INCH_ROUTER, amount).build_transaction({'from': self.account.address,
                                                                                          'nonce': self.w3.eth.get_transaction_count(self.account.address),
                                                                                          'chainId': self.chain_id})
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        print(f"sent approval tx: {self.explorer_url}tx/{tx_hash.hex()}")
        print("awaiting confirmation...")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"approval confirmed in block {receipt['blockNumber']}")

    def get_token(self, string):
        try:
            addr = self.w3.to_checksum_address(string)
            token_contract = self.w3.eth.contract(address=addr, abi=ERC20_ABI)
            symbol = token_contract.functions.symbol().call()
            name = token_contract.functions.name().call()
            decimals = token_contract.functions.decimals().call()

            return {'address': addr, 'symbol': symbol, 'name': name, 'decimals': decimals}
        except:
            return None
    @staticmethod
    def parse_float(num):
        # integer_part = int(num)
        # _, decimal_part = f"{(num - integer_part):.4}".split(".")
        # return f"{integer_part}.{decimal_part}"

        # Native format string functionality can be used to format Decimals when printing
        return f"{num:.10f}"
