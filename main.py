#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime

from os import listdir
from os.path import isfile, join

from eth_utils.address import is_address

from clint.textui.validators import ValidationError
from pyfiglet import Figlet

f = Figlet(font='big')
from one_inch import OneInch
from util import open_json, find_token_in_files, fetch_coingecko_token
from pprint import pprint

sys.path.insert(0, os.path.abspath('..'))

from clint.textui import prompt, puts, colored, validators


def generate_selector(data):
    options = []
    count = 1
    for name, values in data.items():
        options.append({'selector': count, 'prompt': name, 'return': name})
        count += 1
    return options


class NumberValidator(object):
    message = 'Enter a valid number.'

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __call__(self, value):
        """
        Validates that the input is a float.
        """
        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValidationError(self.message)


class CLI:

    def __init__(self):
        print(f.renderText('Goblin Trading CLI'))
        print("Powered by 1inch\n")
        self.one_inch = None
        self.amount_in = None
        self.token_out = None
        self.token_in = None
        self.token_list = None
        self.chain_id = None
        self.rpc = None
        self.explorer = None
        self.currency = None
        self.select_chain()

    def select_chain(self):
        chains = open_json('config/chains.json')
        chain_options = generate_selector(chains)
        chain = prompt.options("Select chain:", chain_options)
        self.chain_id = chains[chain]['id']
        self.rpc = chains[chain]['rpc']
        self.explorer = chains[chain]['explorer']
        self.currency = chains[chain]['currency']
        self.generate_one_inch()
        self.select_rpc()

    def select_rpc(self):
        rpcs = open_json('config/rpc.json')
        if str(self.chain_id) in rpcs.keys() and len(rpcs[str(self.chain_id)]) > 1:
            rpc_options = generate_selector(rpcs[str(self.chain_id)])
            self.rpc = rpcs[str(self.chain_id)][prompt.options("Select rpc:", rpc_options)]

        self.select_pair()

    # def select_token_list(self):
    #     token_list_path = f"config/token_lists/{self.chain_id}/"
    #     token_list_files = [f for f in listdir(token_list_path) if isfile(join(token_list_path, f))]
    #     token_list_file = token_list_files[prompt.options("select token list:", token_list_files) - 1]
    #     self.token_list = open_json(f"{token_list_path}{token_list_file}")
    #     self.select_pair()

    def select_token(self, token_direction=""):
        while True:
            selected_token = None
            from_symbol = prompt.query(f"Select {token_direction} token:")

            # If from_symbol is native currency of a chain like ETH
            if from_symbol.upper() == self.currency.upper():
                selected_token = {'symbol': self.currency, 'name': self.currency, 'address': "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", 'decimals': 18}

            # if from symbol is an address, we can to fetch details directory
            # from the blockchain
            elif is_address(from_symbol):
                potential_token = self.one_inch.get_token(from_symbol)
                if potential_token is not None:
                    print(f"Token found by address: {potential_token['symbol']}, use at your own risk")
                    selected_token = potential_token

            # Otherwise we read through json files in ./config/token_lists/{chain_id}
            # to try and find the token
            else:
                selected_token = find_token_in_files(self.chain_id, from_symbol)

            if selected_token is not None:
                break

        if selected_token["symbol"].upper() == self.currency.upper():
            selected_token["explorer_url"] = self.explorer
        else:
            selected_token["explorer_url"] = f"{self.explorer}token/{selected_token['address']}"


        print(f"Selected token: {selected_token['symbol']}\nName: {selected_token['name']}\nAddress: {selected_token['explorer_url']}\nDecimals: {selected_token['decimals']}")
    

        # Sanity check the token details by fetching data about token from coingecko 
        coingecko_data = fetch_coingecko_token(self.chain_id, selected_token["address"])
        if coingecko_data is None:
            msg = "# No data about the selected token was found on coingecko! Proceed at your own risk #"
            print(f"\n{'#'*len(msg)}\n{msg}\n{'#'*len(msg)}\n")

        return selected_token


    def select_pair(self):
        # Just to give some space between menus and make sure the token selection stands out
        print("")
        self.token_in = self.select_token(token_direction="from")
        self.token_out = self.select_token(token_direction="to")
        if self.token_in == self.token_out:
            print("You can't swap the same token")
            self.select_pair()
        print(f"Selected Pair {self.token_in['symbol']}->{self.token_out['symbol']}")
        self.select_amount()

    def select_amount(self):
        # Just to give some space between menus and make sure the token selection stands out
        print("")
        print("(NOTE: use -1 to select max amount available in wallet)")
        self.token_amount_in = prompt.query("Select amount:", validators=[NumberValidator()])
        if self.token_amount_in < 0:
            if self.one_inch.has_wallet:
                self.amount_in = self.one_inch.get_balance(self.token_in['address'])
                self.token_amount_in = self.amount_in / 10 ** self.token_in['decimals']
            else:
                print("No wallet set, Can't proceed with 0 amount")
                self.select_amount()
        else:
            self.amount_in = int(self.token_amount_in * 10 ** int(self.token_in['decimals']))
        if self.amount_in == 0:
            print("Can't proceed with 0 amount")
            self.select_amount()
        self.select_action()

    def generate_one_inch(self):
        self.one_inch = OneInch(self.chain_id, self.rpc, self.currency, self.explorer)

    def fetch_quote(self):
        print("fetching quote...")
        quote = self.one_inch.get_quote(self.token_in['address'], self.token_out['address'], self.amount_in)
        amount_out = int(quote['toTokenAmount']) / 10 ** self.token_out['decimals']
        price_out = amount_out / self.token_amount_in
        price_in = self.token_amount_in / amount_out
        ct = datetime.datetime.now()
        print(f"\nAmount out: {OneInch.parse_float(amount_out)} {self.token_out['symbol']}\n")
        print(f"[{ct}] price: {OneInch.parse_float(price_out)} {self.token_out['symbol']}/{self.token_in['symbol']} | {OneInch.parse_float(price_in)} {self.token_in['symbol']}/{self.token_out['symbol']}")

    def watch(self):
        try:
            while True:
                quote = self.one_inch.get_quote(self.token_in['address'], self.token_out['address'], self.amount_in)
                amount_out = int(quote['toTokenAmount']) / 10 ** self.token_out['decimals']
                price_out = amount_out / self.token_amount_in
                price_in = self.token_amount_in / amount_out
                ct = datetime.datetime.now()
                print(
                    f"[{ct}] price: {OneInch.parse_float(price_out)} {self.token_out['symbol']}/{self.token_in['symbol']} | {OneInch.parse_float(price_in)} {self.token_in['symbol']}/{self.token_out['symbol']}")
                time.sleep(5)
        
        except KeyboardInterrupt:
            print("Going back to action menu\n")
            self.select_action()


    def trigger(self, price_type, direction, price, slippage):
        if price_type == "forward":
            q = f"{self.token_in['symbol']}/{self.token_out['symbol']}"
        else:
            q = f"{self.token_out['symbol']}/{self.token_in['symbol']}"
        print(f"Triggering  {direction} trigger price: {price} {q} with slippage: {slippage}%")
        cont = prompt.yn("Continue with swap?", default="y")
        if not cont:
            print("Exiting...")
            exit()
        while True:
            quote = self.one_inch.get_quote(self.token_in['address'], self.token_out['address'], self.amount_in)
            amount_out = int(quote['toTokenAmount']) / 10 ** self.token_out['decimals']
            price_out = amount_out / self.token_amount_in
            price_in = self.token_amount_in / amount_out
            ct = datetime.datetime.now()
            print(f"\nAmount out: {OneInch.parse_float(amount_out)} {self.token_out['symbol']}\n")
            print(f"[{ct}] price: {OneInch.parse_float(price_out)} {self.token_out['symbol']}/{self.token_in['symbol']} | {OneInch.parse_float(price_in)} {self.token_in['symbol']}/{self.token_out['symbol']}")

            if price_type == "forward":
                trigger_price = price_in
            else:
                trigger_price = price_out

            if direction == "above":
                if trigger_price >= price:
                    print("Price above target, swapping")
                    self.one_inch.send_swap(self.token_in['address'], self.token_out['address'], self.amount_in, slippage)
                    break
            elif direction == "below":
                if trigger_price <= price:
                    print("Price below target, swapping")
                    self.one_inch.send_swap(self.token_in['address'], self.token_out['address'], self.amount_in, slippage)
                    break
        self.select_pair()

    def twap(self, interval, slippage, trade_count):
        if self.amount_in < 0:
            self.amount_in = self.one_inch.get_balance(self.token_in['address'])
        twap_amount = int(self.amount_in / trade_count)
        token_twap_amount = twap_amount / 10 ** self.token_in['decimals']
        print(f"TWAPing, {OneInch.parse_float(token_twap_amount)} {self.token_in['symbol']}, {trade_count} trades, {interval} seconds interval, {slippage}% slippage")
        cont = prompt.yn("Continue with swap?", default="y")
        if not cont:
            print("Exiting...")
            exit()


        for t in range(trade_count):
            print(f"Trade {t+1}/{trade_count}")
            quote = self.one_inch.get_quote(self.token_in['address'], self.token_out['address'], twap_amount)
            amount_out = int(quote['toTokenAmount']) / 10 ** self.token_out['decimals']
            price_out = amount_out /token_twap_amount
            price_in = token_twap_amount/ amount_out
            ct = datetime.datetime.now()
            print(f"\nAmount out: {OneInch.parse_float(amount_out)} {self.token_out['symbol']}\n")
            print(
                f"[{ct}] price: {OneInch.parse_float(price_out)} {self.token_out['symbol']}/{self.token_in['symbol']} | {OneInch.parse_float(price_in)} {self.token_in['symbol']}/{self.token_out['symbol']}")
            self.one_inch.send_swap(self.token_in['address'], self.token_out['address'], twap_amount, slippage)
            if t < trade_count - 1:
                print(f"Waiting {interval} seconds for next trade")
                time.sleep(interval)
            else:
                print("All trades completed")
        self.select_pair()


    def swap(self):
        if not self.one_inch.has_wallet:
            print("No wallet found, please import wallet")
            exit()
        token_in_allowed = self.one_inch.get_allowance(self.token_in['address'])
        if self.amount_in > token_in_allowed:
            cont = prompt.yn(f"insufficient {self.token_in['symbol']} allowance, approve token?", default="y")
            if not cont:
                print("Exiting...")
                exit()
            print("Approving token...")
            self.one_inch.approve_token(self.token_in['address'], 2**255 - 1)

        swap_type = prompt.options("Select swap type:", [{'selector': 1, 'prompt': 'Swap', 'return': 'swap'},
                                                    {'selector': 2, 'prompt': 'Trigger', 'return': 'trigger'},
                                                    {'selector': 3, 'prompt': 'TWAP', 'return': 'twap'}])
        slippage = prompt.options("Select slippage:", [{'selector': 1, 'prompt': 'default - 0.5%', 'return': 0.5},
                                                    {'selector': 2, 'prompt': 'high - 5%', 'return': 5.0},
                                                    {'selector': 3, 'prompt': 'medium - 1%', 'return': 1.0},
                                                    {'selector': 4, 'prompt': 'low - 0.1%', 'return': 0.1},
                                                    {'selector': 5, 'prompt': 'meme coin - 20%', 'return': 20},
                                                    {'selector': 6, 'prompt': 'custom', 'return': -1}])
        if slippage == -1:
            slippage = prompt.query("Select slippage:", validators=[NumberValidator()])
            slippage = max(min(slippage, 100), 0.05)

        if swap_type == "swap":
            print(f"swapping {OneInch.parse_float(self.token_amount_in)} {self.token_in['symbol']} for {self.token_out['symbol']}")
            cont = prompt.yn("Continue with swap?", default="y")
            if not cont:
                print("Exiting...")
                exit()
            self.one_inch.send_swap(self.token_in['address'], self.token_out['address'], self.amount_in, slippage)
            self.select_pair()
        elif swap_type == "trigger":
            price_type = prompt.options("Select price direction:", [{'selector': 1, 'prompt': f"{self.token_in['symbol']}/{self.token_out['symbol']}", 'return': "forward"},
                                                            {'selector': 2, 'prompt': f"{self.token_out['symbol']}/{self.token_in['symbol']}", 'return': "backward"}])
            direction = prompt.options("Select trigger type:", [
                {'selector': 1, 'prompt': "Above", 'return': "above"},
                {'selector': 2, 'prompt': "Below", 'return': "below"}])
            trigger_price = prompt.query("Select trigger price:", validators=[NumberValidator()])

            self.trigger(price_type, direction, trigger_price, slippage)

        elif swap_type == "twap":
            interval = prompt.options("Select interval:", [{'selector': 1, 'prompt': '1 minute', 'return': 60},
                                                           {'selector': 2, 'prompt': '5 minutes', 'return': 300},
                                                           {'selector': 3, 'prompt': '15 minutes', 'return': 900},
                                                           {'selector': 4, 'prompt': '1 hour', 'return': 3600},
                                                           {'selector': 5, 'prompt': 'custom', 'return': -1}])
            if interval == -1:
                interval = prompt.query("Select interval seconds:", validators=[validators.IntegerValidator()])
            trade_count = prompt.query("Select number of trades:", validators=[validators.IntegerValidator()])
            self.twap(interval, slippage, trade_count)


    def select_action(self):
        self.fetch_quote()
        action = prompt.options("Select action:", [{'selector': 1, 'prompt': 'Swap', 'return': 'swap'},
                                                     {'selector': 2, 'prompt': 'Change amount', 'return': 'amount'},
                                                     {'selector': 3, 'prompt': 'Change pair', 'return': 'pair'},
                                                     {'selector': 4, 'prompt': 'Watch price', 'return': 'watch'},
                                                     {'selector': 5, 'prompt': 'Exit', 'return': 'exit'}])
        if action == "swap":
            self.swap()
        elif action == "amount":
            self.select_amount()
        elif action == "pair":
            self.select_pair()
        elif action == "watch":
            self.watch()
        elif action == "exit":
            print("Bye")
            exit()

    def fetch_native_token_balance(self):
        self.one_inch.get_native_token_balance()

    def fetch_token_balance(self):
        self.one_inch.get_token_balance(self.token_in['address'])


if __name__ == '__main__':
    try:
        cli = CLI()
    except KeyboardInterrupt:
        pass