## Whitelist of accounts
# Accounts that are allowed to participate in a GunClear transaction
# Merklized into a Simple Binary Merkle Tree for access

operator: address
pendingOperator: address

# 0: not valid user
# 1: valid user
# 2: pending review
# 3: no longer valid
status: uint256[address]

def __init__():
    self.operator = msg.sender

def nominateOperator(_operator: address):
    assert msg.sender == self.operator

def acceptOperatorNominee():
    assert msg.sender == self.pendingOperator
    self.operator = self.pendingOperator

def modifyStatus(_account: address, _status: uint256):
    assert msg.sender == self.operator
    self.status[_account] = _status
