## Authlist of accounts
# Accounts that are allowed to participate in a GunClear transaction
# Merklized into a Simple Binary Merkle Tree for access

KEYLEN: constant(int128) = 160  # addresses are 160 bits long

# Event for listeners to synchronize with tree updates
TreeUpdate: event({
        account: indexed(address),
        status: indexed(uint256),
        nodes: bytes32[KEYLEN]  # Hash updates for account as key (len 160 bits)
    })


# Operator
operator: public(address)
pendingOperator: address


# Review period before permanent modifications
REVIEW_PERIOD: constant(timedelta) = 2592000  # 30*24*60*60 secs = 30 days
review_started: timestamp[address]


# Status enum:
# 0: not valid user
# 1: valid user
# 2: pending review (restricted permissions)
# 3: banned
status: public(uint256[address])


# Merkle tree root (db is 'status' mapping)
root: public(bytes32)


@public
def __init__():
    self.operator = msg.sender
    # Compute and set empty root hash
    empty_node: bytes32 = keccak256(convert(0, 'bytes32'))  # Default status
    for _ in range(KEYLEN):
        empty_node = keccak256(concat(empty_node, empty_node))
    self.root = empty_node


@public
def nominateOperator(_operator: address):
    assert msg.sender == self.operator
    self.pendingOperator = _operator


@public
def acceptOperatorNominee():
    assert msg.sender == self.pendingOperator
    self.operator = self.pendingOperator


# Update status entry, modify tree root, and emit sync event
@private
def _set(_account: address, _status: uint256, _proof: bytes32[KEYLEN]):
    node_hash: bytes32 = keccak256(convert(self.status[_account], 'bytes32'))

    # For recording the node updates as we go (root->leaf order)
    node_updates: bytes32[KEYLEN]
    # Start the updates at the leaf
    node_updates[KEYLEN-1] = keccak256(convert(_status, 'bytes32'))

    # Validate each step of the proof is correct (traverse leaf->root)
    # Also record node updates up the tree
    for i in range(KEYLEN-2): # [0:KEYLEN-2]
        # We want to start at the leaf and merklize up
        lvl: int128 = KEYLEN-1 - i  # lvl = (159 - [0:158]) = [159:1]

        # Keypath maps MSB:root->LSB:leaf, but we are traversing backwards
        # (e.g. path choice: leaf is bit0 and root is bit159)
        # so, this is how we check whether to branch right or left:
        if bitwise_and(convert(_account, 'uint256'), shift(1, i)):
            # Path goes to the right at `lvl`, so sibling is to our left
            # Update node to hash of current node and sibling
            node_hash = keccak256(concat(_proof[lvl], node_hash))
            # Record hash of node update and sibling as next node up
            node_updates[lvl-1] = keccak256(concat(_proof[lvl], node_updates[lvl]))
        else:
            # Path goes to the reft at `lvl`, so sibling is to our right
            # Update node to hash of current node and sibling
            node_hash = keccak256(concat(node_hash, _proof[lvl]))
            # Record hash of node update and sibling as next node up
            node_updates[lvl-1] = keccak256(concat(node_updates[lvl], _proof[lvl]))

    # Validate and update the root hash using the above methodology
    if bitwise_and(convert(_key, 'uint256'), shift(1, KEYLEN-1)):
        # Path goes to the right at root, so sibling is to our left
        # Validate root matches hash of current node and sibling
        assert self.root == keccak256(concat(_proof[0], node_hash))
        # Update root to hash of node update and sibling
        self.root = keccak256(concat(_proof[0], node_updates[0]))
    else:
        # Path goes to the left at root, so sibling is to our right
        # Validate root matches hash of current node and sibling
        assert self.root == keccak256(concat(node_hash, _proof[0]))
        # Update root to hash of node update and sibling
        self.root = keccak256(concat(node_updates[0], _proof[0]))

    # Only if proof validates can we update the account's status
    self.status[_account] = _status

    # Make sure we emit the updates for anyone listening along to track
    log.UpdatedBranch(_account, _status, node_updates)


# The operator can authorize a user at any time
@public
def authorize(_account: address, _proof: bytes32[KEYLEN]):
    assert msg.sender == self.operator
    self.review_started[_account] = 0  # Just reset back to zero to recover gas from review
    self._set(_account, 1, _proof)


# The operator can start the review cycle for a specific account
# NOTE: Operator will call `authorize` again to cancel
@public
def review(_account: address, _proof: bytes32[KEYLEN]):
    assert msg.sender == self.operator
    assert self.status[_account] == 1
    self.review_started[_account] = blk.timestamp
    self._set(_account, 2, _proof)


# The operator can remove someone from the list after the review period
@public
def remove(_account: address, _proof: bytes32[KEYLEN]):
    assert msg.sender == self.operator
    assert self.status[_account] == 2
    assert self.review_started[_account] + REVIEW_PERIOD >= blk.timestamp
    self._set(_account, 3, _proof)
