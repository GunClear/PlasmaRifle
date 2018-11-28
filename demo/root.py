import json

from web3.auto.infura.ropsten import w3  #TODO get 'w3' from args.network
with open('../contracts.json', 'r') as f:
    interface = json.loads(f.read())['contracts']['auth-list']

import argparse
ap = argparse.ArgumentParser("Deploy contracts")
ap.add_argument("--network",  default="ropsten", \
        help="Network to deploy to")
ap.add_argument("authlist", type=str, \
        help="Authorization list address")

args = ap.parse_args()

authlist = w3.eth.contract(address=args.authlist, **interface)
print('0x'+authlist.functions.root().call().hex())
