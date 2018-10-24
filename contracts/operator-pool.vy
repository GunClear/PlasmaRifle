# Plasma operator's contract
# This contract allows GunClear to manage the list of Ethereum accounts
# that can publish blocks to the Plasma root chain contract

owner: public(address)
pendingOwner: address

isOperator: bool[address]
numOperators: public(uint256)


@public
def __init__():
    self.owner = msg.sender


@public
def nominateOwner(_owner: address):
    assert msg.sender == self.owner
    self.pendingOwner = _owner


@public
def acceptOwnerNominee():
    assert msg.sender == self.pendingOwner
    self.owner = self.pendingOwner


@public
def addOperator(_operator: address):
    self.isOperator[_operator] = True
    self.numOperators += 1


@public
def remOperator(_operator: address):
    self.isOperator[_operator] = False
    self.numOperators -= 1
