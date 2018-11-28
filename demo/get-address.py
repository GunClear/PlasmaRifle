import argparse
from eth_utils import to_bytes
from eth_account import Account


def to_bytes32(value: int) -> bytes:
    v = to_bytes(value).rjust(32, b'\x00')
    assert len(v) == 32, \
            "{} must be less than 2**256".format(value)
    return v


if __name__ == '__main__':
    ap = argparse.ArgumentParser("Script to create account address from public key")
    ap.add_argument("private_key", type=int, help="Private key, must be an integer in [1, 2**256)")
    args = ap.parse_args()
    assert 1 <= args.private_key < 2**256, "Must be within [1, 2**256)!"
    a = Account.privateKeyToAccount(to_bytes32(args.private_key))
    print(a.address)
