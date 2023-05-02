import requests
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3, EthereumTesterProvider
import web3
from web3.middleware import construct_sign_and_send_raw_middleware
import os

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

        private_key = os.environ.get("PRIVATE_KEY")
        self.has_wallet = False
        if private_key is None:
            print("PRIVATE_KEY environment variable is not set, continuing without it")
            self.has_wallet = False
        elif private_key.startswith("0x"):
            self.account = Account.from_key(private_key)
            self.w3.middleware_onion.add(construct_sign_and_send_raw_middleware(self.account))

            print(f"Your hot wallet address is {self.account.address}")
            self.balance = self.w3.eth.get_balance(self.account.address)
            print(
                f"Your hot wallet balance is {OneInch.parse_float(self.w3.from_wei(self.balance, 'ether'))} {self.currency}")
            self.has_wallet = True
        else:
            raise ("PRIVATE_KEY must start with 0x")

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

        fee = min(max(0.1, slippage * 0.1), 3.0)
        url = f"https://api.1inch.io/v4.0/{self.chain_id}/swap?fromAddress={self.account.address}&fromTokenAddress={from_token_address}&toTokenAddress={to_token_address}&amount={amount}&slippage={slippage}&complexityLevel=3&fee={fee}&referrerAddress={REFERRAL}"
        response = requests.get(url=url).json()

        return response

    def send_swap(self, from_token_address, to_token_address, amount, slippage=0.1):
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
        if token_addr == NATIVE_TOKEN:
            return 2**256 - 1
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        return token_contract.functions.allowance(self.account.address, ONE_INCH_ROUTER).call()

    def get_readable_allowance(self, token_addr):
        """
        Get readable allowance
        :param token_addr:
        :return:
        """
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
        if token_addr == NATIVE_TOKEN:
            balance = self.w3.eth.get_balance(self.account.address)
            return f"{OneInch.parse_float(balance / 10 ** 18)} {self.currency}"
        token_contract = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        balance = token_contract.functions.balanceOf(self.account.address).call()
        return f"{OneInch.parse_float(balance / 10 ** token_contract.functions.decimals().call())} {token_contract.functions.symbol().call()}"

    @staticmethod
    def parse_float(num):
        # integer_part = int(num)
        # _, decimal_part = f"{(num - integer_part):.4}".split(".")
        # return f"{integer_part}.{decimal_part}"

        # Native format string functionality can be used to format Decimals when printing
        return f"{num:.4f}"
