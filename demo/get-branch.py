from eth_typing import (
        Address,
    )

from eth_utils import (
        keccak,
        to_bytes,
        to_int,
        to_canonical_address,
    )

from trie.smt import SparseMerkleProof

from web3 import Web3


def int_to_bytes32(value: int) -> bytes:
    v = to_bytes(value).rjust(32, b'\x00')
    return v


EMPTY_NODE_HASHES = []
node = keccak(int_to_bytes32(0))
for _ in range(160):  # Tree depth
    EMPTY_NODE_HASHES.insert(0, node)
    node = keccak(EMPTY_NODE_HASHES[0] + EMPTY_NODE_HASHES[0])

authlist_abi = [
        {
            'name': 'TreeUpdate',
            'inputs': [
                {'type': 'address', 'name': 'account', 'indexed': True},
                {'type': 'uint256', 'name': 'status', 'indexed': True},
                {'type': 'bytes32[160]', 'name': 'nodes', 'indexed': False}
            ],
            'anonymous': False,
            'type': 'event',
        },{
            'name': 'status',
            'outputs': [{'type': 'uint256', 'name': 'out'}],
            'inputs': [{'type': 'address', 'name': 'arg0'}],
            'constant': True,
            'payable': False,
            'type': 'function',
        },{
            'name': 'root',
            'outputs': [{'type': 'bytes32', 'name': 'out'}],
            'inputs': [],
            'constant': True,
            'payable': False,
            'type': 'function'
        }
    ]


class Listener:
    """
    The Listener listens for updates and synchronizes their
    proof and value accordingly
    """
    def __init__(self, w3: Web3, acct: Address, tree_address: Address):
        self._tree = w3.eth.contract(tree_address, abi=authlist_abi)
        self.acct = acct
        self._proof = SparseMerkleProof(
                to_canonical_address(acct),
                int_to_bytes32(0),
                EMPTY_NODE_HASHES
            )
        self._filter = self._tree.events.TreeUpdate().createFilter(fromBlock=0)
        # Iterate over all previously logged entries
        for log in self._filter.get_all_entries():
            self._proof.merge(
                    to_canonical_address(log.args.account),
                    int_to_bytes32(log.args.status),
                    log.args.nodes
                )

    def sync(self):
        # Iterate over last unchecked logs, update proof for them
        for log in self._filter.get_new_entries():
            self._proof.merge(
                    to_canonical_address(log.args.account),
                    int_to_bytes32(log.args.status),
                    log.args.nodes
                )

    @property
    def branch(self) -> list:
        return self._proof.branch[:]  # shallow copy

    @property
    def updated(self) -> bool:
        return self._proof.root_hash == self._tree.functions.root().call()

    @property
    def status(self) -> int:
        self.sync()  # Validate that the value is up-to-date

        # Validate that the proof is correct (and therefore matches tree)
        status = to_int(self._proof.value)
        assert self._tree.functions.status(self.acct).call() == status
        return status


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

listener = Listener(w3, args.account, args.authlist)

branch = listener.branch

[print('0x'+node.hex()) for node in branch]  # Print in list format
