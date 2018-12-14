# Getting Started

## Using the Daemon
The user can specify the location of the Ethereum node they wish to use using the following:

## Documentation
The [wiki](https://github.com/GunClear/PlasmaRifle/wiki) serves as the public-facing documentation for this project.

If something is unclear, please submit an [issue](https://github.com/GunClear/PlasmaRifle/issues/new) for it
and we will work on updating the documentation to address your issues when learning about the platform.

## Testing


## Demo
Here are the steps for testing the demo:

1. Generate two private keys (DO NOT USE THESE TO STORE FUNDS)
```bash
$ cd demo
$ echo [PICK RANDOM NUMBER] > ./receiver.key
$ echo [PICK RANDOM NUMBER] > ./sender.key
```

2. Get Ethereum account addresses for these keys (for later)
```bash
$ python get-address.py $(cat ./receiver.key) > ./receiver.acct
$ python get-address.py $(cat ./sender.key) > ./sender.acct
```

3. Deploy the authlist contract to the network
```bash
$ python deploy.py --network ropsten auth-list > ./authlist.acct
```

4. Add these addresses to the deployed Authorization List
```bash
$ python authorize.py --network ropsten $(cat ./authlist.acct) $(cat ./receiver.acct) \
    $(python get-branch.py --network ropsten $(cat ./authlist.acct) $(cat ./receiver.acct))
# Wait for txn to mine...
$ python authorize.py --network ropsten $(cat ./authlist.acct) $(cat ./sender.acct) \
    $(python get-branch.py --network ropsten $(cat ./authlist.acct) $(cat ./sender.acct))
# Wait for txn to mine...
```

5. Record the auth root hash
```bash
$ python root.py --network ropsten $(cat ./authlist.acct) > auth-root.hash
```

6. Obtain Merkle Branch via Listener
```bash
$ python get-branch.py --network ropsten $(cat ./authlist.acct) $(cat ./receiver.acct) > receiver-branch.ls
$ python get-branch.py --network ropsten $(cat ./authlist.acct) $(cat ./sender.acct) > sender-branch.ls
```

7. Also, mint tokens!
```bash
$ python deploy.py --network ropsten gun-token > ./token.acct
# Wait for txn to mine...
$ python mint.py --network ropsten $(cat ./token.acct) [RANDOM HEX HERE] $(cat ./receiver.acct)
# Wait for txn to mine...
```

## Release


## Reporting Security Issues
