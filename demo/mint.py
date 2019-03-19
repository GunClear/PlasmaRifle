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
    from web3.auto.infura.ropsten import w3
    with open('../contracts.json', 'r') as f:
        abi = json.loads(f.read())['contracts']['gun-token']['abi']
    
    ap = argparse.ArgumentParser("Deploy contracts")
    # NOTE Rinkeby doesn't work with web3py
    ap.add_argument("--network",  default="ropsten", \
            choices=["ropsten", "kovan", "mainnet"], \
            help="Network to deploy to")
    ap.add_argument("address", type=str, \
            help="Token contract address")
    ap.add_argument("tokenid", type=int, \
            help="Token UID (256 bit integer)")
    ap.add_argument("recipient", type=str, \
            help="Receiver's address (20 byte hash)")

    args = ap.parse_args()
    
    w3 = importlib.import_module("web3.auto.infura."+args.network).w3
    
    from pathlib import Path
    dev, _middleware = _keyfile_middleware(Path.home() / '.eth-dev.key')
    w3.middleware_stack.add(_middleware)

    token = w3.eth.contract(args.address, abi=abi)
    if click.confirm("Do you want to mint token {} to {}?".format(args.tokenid, args.recipient), err=True):
        txn_hash = token.functions.mint(args.recipient, args.tokenid).transact({'from':dev.address})
        click.echo("https://"+("" if args.network is "mainnet" else args.network+".")+\
                "etherscan.io/tx/"+txn_hash.hex(), err=True)
        receipt = w3.eth.waitForTransactionReceipt(txn_hash)
        print("SUCCESS!" if receipt.status == 1 else "FAIL!")
