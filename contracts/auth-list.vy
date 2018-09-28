## Authlist of accounts
# Accounts that are allowed to participate in a GunClear transaction
# Merklized into a Simple Binary Merkle Tree for access

operator: public(address)
pendingOperator: address

# Status enum:
# 0: not valid user
# 1: valid user
# 2: pending review
# 3: blacklisted
status: public(uint256[address])


# Review period is 30 days
REVIEW_PERIOD: timestamp = constant(30*24*60*60)
review_started: timestamp[address]


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


# The operator can authorize a user at any time
# This action updates the public list
@public
def authorize(_account: address):
    assert msg.sender == self.operator
    self.status[_account] = 1
    # TODO: Update Merkle Tree


# The operator can start the review cycle for a specific account
# This does NOT change the public list
@public
def review(_account: address):
    assert msg.sender == self.operator
    assert self.status[_account] == 1
    self.status[_account] = 2
    self.review_started[_account] = blk.timestamp


# The operator can remove someone from the list after the review period
@public
def remove(_account: address):
    assert msg.sender == self.operator
    assert self.review_started[_account] + REVIEW_PERIOD >= blk.timestamp
    assert self.status[_account] == 2
    self.status[_account] = 3
    # TODO: Update Merkle Tree
