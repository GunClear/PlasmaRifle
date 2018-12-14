import json
import web3
import argparse
import click
import importlib


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
    with open('../contracts.json', 'r') as f:
        contracts = json.loads(f.read())['contracts']
    
    ap = argparse.ArgumentParser("Deploy contracts")
    # NOTE Rinkeby doesn't work with web3py
    ap.add_argument("--network",  default="ropsten", \
            choices=["ropsten", "kovan", "mainnet"], \
            help="Network to deploy to")
    ap.add_argument("contract", type=str, choices=contracts.keys(), \
            help="Contract file to deploy")
    ap.add_argument("arguments", nargs='*', \
            help="Contract file to deploy")

    args = ap.parse_args()

    w3 = importlib.import_module("web3.auto.infura."+args.network).w3
    
    from pathlib import Path
    dev, _middleware = _keyfile_middleware(Path.home() / '.eth-dev.key')
    w3.middleware_stack.add(_middleware)

    interface = contracts[args.contract]
    c = w3.eth.contract(**interface)
    if click.confirm("Do you want to deploy '{}'?".format(args.contract), err=True):
        txn_hash = c.constructor(*args.arguments).transact({'from':dev.address})
        click.echo("https://"+("" if args.network is "mainnet" else args.network+".")+\
                "etherscan.io/tx/"+txn_hash.hex(), err=True)
        receipt = w3.eth.waitForTransactionReceipt(txn_hash)
        address = receipt['contractAddress']
        print(address)
