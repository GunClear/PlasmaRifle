import json


def _keyfile_middleware(keyfile_path):
    with open(keyfile_path, 'r') as f:
        keyfile = json.loads(f.read())
    
    from sys import stderr
    from getpass import getpass
    password = getpass("Please Input Keyfile Password ({}): ".format(keyfile_path), stderr)
    
    from eth_account import Account
    privateKey = Account.decrypt(keyfile, password)
    account = Account.privateKeyToAccount(privateKey)
    
    from web3.middleware.signing import construct_sign_and_send_raw_middleware
    middleware = construct_sign_and_send_raw_middleware(privateKey)
    return account, middleware


from web3.auto.infura.ropsten import w3  #TODO get 'w3' from args.network
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

from pathlib import Path
dev, _middleware = _keyfile_middleware(Path.home() / '.eth-dev.key')
w3.middleware_stack.add(_middleware)  #TODO get 'w3' from args.network

authlist = w3.eth.contract(address=args.authlist, **interface)
assert authlist.functions.status(args.account).call() == 0, "Account onboarded prior!"

from plasma_rifle import get_branch
branch = get_branch(args.authlist, args.account)  # FIXME must obtain merkle branch!
from trie.smt import calc_root
assert calc_root(args.account, 0, branch) == authlist.functions.root().call(), \
        "Do not have up-to-date branch to perform operation!"

from click import confirm
if confirm("Do you want to authorize '{}'?".format(args.account), err=True):
    txn_hash = authlist.functions.authorize(args.account, branch).\
            transact({'from':dev.address})
    receipt = w3.eth.waitForTransactionReceipt(txn_hash)
    print("SUCCESS!" if receipt else "FAIL!")