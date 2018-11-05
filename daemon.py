from pathlib import Path
import IPython
from web3.auto.infura.ropsten import w3
from eth_utils import keccak, to_int


class ValidationError(Exception):
    pass


TREE_HEIGHT=160
EMPTY_VALUE=b'\x00' * 32
# keccak(EMPTY_VALUE)
EMPTY_LEAF_NODE_HASH = b')\r\xec\xd9T\x8bb\xa8\xd6\x03E\xa9\x888o\xc8K\xa6\xbc\x95H@\x08\xf66/\x93\x16\x0e\xf3\xe5c'


# sanity check
assert EMPTY_LEAF_NODE_HASH == keccak(EMPTY_VALUE)
EMPTY_NODE_HASHES = [EMPTY_LEAF_NODE_HASH]


hash_duplicate = lambda h: keccak(h + h)
# Branch for any value in an empty tree in root->leaf order
for _ in range(TREE_HEIGHT-1):
    EMPTY_NODE_HASHES.insert(0, hash_duplicate(EMPTY_NODE_HASHES[0]))


def validate_is_bytes(value):
    if not isinstance(value, bytes):
        raise ValidationError("Value is not of type `bytes`: got '{0}'".format(type(value)))


def validate_length(value, length):
    if len(value) != length:
        raise ValidationError("Value is of length {0}.  Must be {1}".format(len(value), length))


class SparseMerkleTree:
    def __init__(self, db={}):
        self.db = db
        # Initialize an empty tree with one branch
        self.root_hash = hash_duplicate(EMPTY_NODE_HASHES[0])
        self.db[self.root_hash] = EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0]
        for i in range(TREE_HEIGHT - 1):
            self.db[EMPTY_NODE_HASHES[i]] = EMPTY_NODE_HASHES[i+1] + EMPTY_NODE_HASHES[i+1]
        self.db[EMPTY_LEAF_NODE_HASH] = EMPTY_VALUE

    def get(self, key):
        value, _ = self._get(key)
        return value
    
    def branch(self, key):
        _, branch = self._get(key)
        return branch

    def _get(self, key):
        """
        Returns db value and branch in root->leaf order
        """
        validate_is_bytes(key)
        validate_length(key, 20)
        branch = []

        target_bit = 1 << (TREE_HEIGHT - 1)
        path = to_int(key)
        node_hash = self.root_hash
        # Append the sibling to the branch
        # Iterate on the parent
        for i in range(TREE_HEIGHT):
            if path & target_bit:
                branch.append(self.db[node_hash][:32])
                node_hash = self.db[node_hash][32:]
            else:
                branch.append(self.db[node_hash][32:])
                node_hash = self.db[node_hash][:32]
            target_bit >>= 1

        return self.db[node_hash], branch

    def set(self, key, value):
        """
        Returns all updated hashes in root->leaf order
        """
        validate_is_bytes(key)
        validate_length(key, 20)
        validate_is_bytes(value)

        path = to_int(key)
        branch = self.branch(key)
        node = value
        proof_update = []

        target_bit = 1
        # branch is in root->leaf order, so flip
        for sibling in reversed(branch):
            # Set
            node_hash = keccak(node)
            proof_update.append(node_hash)
            self.db[node_hash] = node

            # Update
            if (path & target_bit):
                node = sibling + node_hash
            else:
                node = node_hash + sibling

            target_bit <<= 1

        self.root_hash = keccak(node)
        self.db[self.root_hash] = node
        # updates need to be in root->leaf order, so flip back
        return list(reversed(proof_update))

    def exists(self, key):
        validate_is_bytes(key)
        validate_length(key, 20)
        return (self.get(key) != EMPTY_VALUE)

    def delete(self, key):
        """
        Equals to setting the value to None
        """
        validate_is_bytes(key)
        validate_length(key, 20)

        self.set(key, EMPTY_VALUE)

    #
    # Dictionary API
    #
    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        return self.set(key, value)

    def __delitem__(self, key):
        return self.delete(key)

    def __contains__(self, key):
        return self.exists(key)


def _keyfile_middleware(keyfile_path):
    import json
    with open(keyfile_path, 'r') as f:
        keyfile = json.loads(f.read())
    
    from getpass import getpass
    password = getpass("Please Input Keyfile Password: ")
    
    from eth_account import Account
    privateKey = Account.decrypt(keyfile, password)
    account = Account.privateKeyToAccount(privateKey)
    
    from web3.middleware.signing import construct_sign_and_send_raw_middleware
    middleware = construct_sign_and_send_raw_middleware(privateKey)
    return account, middleware


def _deployer(name, w3, contract_interface):
    def deploy(*args, transact={}):
        print("Deploying '{}' with args: {}".format(name, args))
        # TODO: Check for args
        txn_hash = w3.eth.contract(**contract_interface).constructor(*args).transact(transact)
        print("Waiting for {:02x} to mine...".format(txn_hash))
        contract_address = w3.eth.waitForTransactionReceipt(txn_hash).contractAddress
        print("Deployed! @ {}".format(contract_address))
        return w3.eth.contract(contract_address, **contract_interface)
    return deploy


def _loader(name, w3, contract_interface):
    def load(address):
        print("Getting already deployed contract {} @ {}".format(name, address))
        return w3.eth.contract(address, **contract_interface)
    return load
        


def console(interfaces):
    dev, _middleware = _keyfile_middleware(Path.home() / '.eth-dev.key')
    w3.middleware_stack.add(_middleware)

    # You need to set the account that executes transactions by default
    #w3.eth.defaultAccount = w3.eth.coinbase

    # Create interface deployers
    deployers = dict([(c, _deployer(c, w3, i)) for c, i in interfaces.items()])
    loaders = dict([(c, _loader(c, w3, i)) for c, i in interfaces.items()])

    return IPython.terminal.embed.InteractiveShellEmbed(
            user_ns={
                'w3': w3,
                'deploy': deployers,
                'load': loaders,
                'dev': dev,
                'smt': SparseMerkleTree()
            },
            banner1="""
Available contracts:
    {}
            """.format('\n    '.join(deployers.keys()))
    )


if __name__ == '__main__':
    import json
    import argparse

    ap = argparse.ArgumentParser(description="""
Daemon to work with web3py and interact with contracts, including deployment.
    """)
    ap.add_argument('contracts', help='Contract assets file (JSON)')
    args = ap.parse_args()
    with open(args.contracts, 'r') as f:
        interfaces = json.loads(f.read())['contracts']

    console(interfaces)()
