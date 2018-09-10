## Whitelist of accounts
# Accounts that are allowed to participate in a GunClear transaction
# Merklized into a Simple Binary Merkle Tree for access

operator: public(address)
pendingOperator: address

# 0: not valid user
# 1: valid user
# 2: pending review
# 3: no longer valid
status: public(uint256[address])

@public
def __init__():
    self.operator = msg.sender


@public
def nominateOperator(_operator: address):
    assert msg.sender == self.operator
    self.pendingOperator = _operator


@public
def acceptOperatorNominee():
    assert msg.sender == self.pendingOperator
    self.operator = self.pendingOperator


@public
def modifyStatus(_account: address, _status: uint256):
    assert msg.sender == self.operator
    self.status[_account] = _status
