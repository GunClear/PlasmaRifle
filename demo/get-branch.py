from web3.auto.infura.ropsten import w3

import json
with open('../contracts.json', 'r') as f:
    interface = json.loads(f.read())['contracts']['auth-list']

import argparse
ap = argparse.ArgumentParser("Deploy contracts")
ap.add_argument("--network",  default="ropsten", \
        help="Network to deploy to")
ap.add_argument("authlist", type=str, \
        help="Authorization list address")
ap.add_argument("account", type=str, \
        help="Account address to authorize")

args = ap.parse_args()
#TODO get 'w3' from args.network

authlist = w3.eth.contract(address=args.authlist, **interface)

from plasma_rifle import get_branch
branch = get_branch(args.authlist, args.account)  # FIXME must obtain merkle branch!

[print(node) for node in branch]  # Print in list format
