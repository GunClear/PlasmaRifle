from typing import Sequence
from hashlib import sha3_256

def sha256(val: bytes) -> bytes:
    return sha3_256(val).digest()

def calc_root(keypath: int, value: bytes, branch: Sequence[bytes]) -> bytes:
    target_bit = 1
    # traverse the path in leaf->root order
    # branch is in root->leaf order (key is in MSB to LSB order)
    node_hash = sha256(value)
    for sibling_node in reversed(branch):
        if keypath & target_bit:
            node_hash = sha256(sibling_node + node_hash)
        else:
            node_hash = sha256(node_hash + sibling_node)
        target_bit <<= 1

    return node_hash

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser("Calculate root hash")
    ap.add_argument("account", type=str, \
            help="Account address (hex)")
    ap.add_argument("status", type=int, \
            help="Status of account")
    ap.add_argument("branch", type=str, nargs='*', \
            help="List of hashes in Merkle Branch Proof (hex[160])")
    args = ap.parse_args()
    key = int(args.account, 16)
    value = args.status.to_bytes(32, byteorder='big')
    branch = [bytearray.fromhex(n[2:]) for n in args.branch]
    print('0x'+calc_root(key, value, branch).hex())
