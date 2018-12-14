import json

with open('../contracts.json', 'r') as f:
    interface = json.loads(f.read())['contracts']['auth-list']

import argparse
ap = argparse.ArgumentParser("Deploy contracts")
# NOTE Rinkeby doesn't work with web3py
ap.add_argument("--network",  default="ropsten", \
        choices=["ropsten", "kovan", "mainnet"], \
        help="Network to deploy to")
ap.add_argument("authlist", type=str, \
        help="Authorization list address")

args = ap.parse_args()

import importlib
w3 = importlib.import_module("web3.auto.infura."+args.network).w3

authlist = w3.eth.contract(address=args.authlist, **interface)
print('0x'+authlist.functions.root().call().hex())
