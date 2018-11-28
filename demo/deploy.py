import json
import web3
import argparse
from click import confirm


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


if __name__ == '__main__':
    from web3.auto.infura.ropsten import w3
    with open('../contracts.json', 'r') as f:
        contracts = json.loads(f.read())['contracts']
    
    ap = argparse.ArgumentParser("Deploy contracts")
    ap.add_argument("--network",  default="ropsten", \
            help="Network to deploy to")
    ap.add_argument("contract", type=str, choices=contracts.keys(), \
            help="Contract file to deploy")
    ap.add_argument("arguments", nargs='*', \
            help="Contract file to deploy")

    args = ap.parse_args()
    
    from pathlib import Path
    #TODO get 'w3' from args.network
    dev, _middleware = _keyfile_middleware(Path.home() / '.eth-dev.key')
    w3.middleware_stack.add(_middleware)

    interface = contracts[args.contract]
    c = w3.eth.contract(**interface)
    if confirm("Do you want to deploy '{}'?".format(args.contract), err=True):
        txn_hash = c.constructor(*args.arguments).transact({'from':dev.address})
        receipt = w3.eth.waitForTransactionReceipt(txn_hash)
        address = receipt['contractAddress']
        print(address)
