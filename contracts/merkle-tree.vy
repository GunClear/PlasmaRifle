# Implementation of a Sparse Merkle Tree in Vyper

# IDEA: Validate proof to transition root,
# then emit the proof and have clients parse logs to keep their
# own personal proof up to date
# Args: key, value, proof (existing value)
# 1. Validate proof is correct for existing value
# 2. Change the value
# 3. Recompute the merkle root with the updated value
# 4. Emit the updated proof as an event (an index of which location it touches)

# Clients can loop over each emitted event with indices they are interested in and update their own proofs

UpdatedBranch: event({
        key: indexed(bytes32),
        value: indexed(bytes32),
        branch: bytes32[160]  # Hash updates for key, starting with root
    })


# Root of the tree. Used to validate state transitions
root: bytes32  # Must be initialized for an empty tree

# "key" denotes path from root to leaf (1 is right, 0 is left)
db: bytes32[bytes32]  # Key: Value DB (empty to start)


@public
def __init__():
    empty_node: bytes32 = keccak256('')
    # each node is hash(left, right), where left/right are also empty
    for lvl in range(160):
        empty_node = keccak256(concat(empty_node, empty_node))
    # Merkle root for a tree of height N that is empty
    self.root = empty_node


#@dev   This function takes a key-value pair and the existing proof required to
#       show that that the value is correct to others. The proof is validated
#       and updated to reflect what it would be with the value modified, and
#       it is then emitted as a log so that others may iterate over transactions
#       to this contract and keep their own personal proofs up to date for changes
#       to keys that affect their own. This has the side benefits of reducing
#       linkability of keys to specific addresses querying them, as well as
#       reducing data storage in the contract by offloading to event storage.
#@param _key    bytes32     key used to lookup existing value and set new one
#@param _value  bytes32     value to update to
#@param _proof  bytes32[N]  proof for N-depth tree
@private
def _set(_key: bytes32, _value: bytes32, _proof: bytes32[160]):
    # Get the party started at the leaf node for _key
    new_node_hash: bytes32 = keccak256(_value)
    prior_node_hash: bytes32 = keccak256(self.db[_key])
    
    # For recording the updated proof as we go
    proof_updates: bytes32[160]
    proof_updates[159] = new_node_hash
    
    # Validate each step of the proof is correct
    # Also, keep track of the merklized updates
    for i in range(159): # 0 to 160-1, start at end of proof and travel upwards
        lvl: int128 = 160-1 - i  # 159 to 1 (159 - [0:158] = [159:1])

        #if convert(_key, 'uint256') & 2**convert(i, 'uint256') > 0:
        if ((convert(_key, 'uint256') % 2**(convert(i, 'uint256')+1)) > (2**convert(i, 'uint256'))-1):
            assert _proof[lvl] == keccak256(concat(_proof[lvl-1], prior_node_hash))
            proof_updates[lvl] = keccak256(concat(_proof[lvl-1], new_node_hash))
        else:
            assert _proof[lvl] == keccak256(concat(prior_node_hash, _proof[lvl-1]))
            proof_updates[lvl] = keccak256(concat(new_node_hash, _proof[lvl-1]))

        # Update loop variables
        prior_node_hash = _proof[lvl]
        new_node_hash = proof_updates[lvl]
    
    # Validate root hash
    #if convert(_key, 'uint256') & 1 > 0:
    if (convert(_key, 'uint256') % 2 > 0):
        assert self.root == keccak256(concat(_proof[0], prior_node_hash))
        self.root = keccak256(concat(_proof[0], new_node_hash))
    else:
        assert self.root == keccak256(concat(prior_node_hash, _proof[0]))
        self.root = keccak256(concat(new_node_hash, _proof[0]))
    
    # Update the root hash for the updated proof
    proof_updates[0] = self.root

    # Finally update value in db since we validated the proof
    self.db[_key] = _value

    # Emit updated proof so those listening at home can follow along
    # through event filtering
    log.UpdatedBranch(_key, _value, proof_updates)
    # NOTE: Clients can subscribe to these events and filter on keys
    #       that match theirs via `not(bitxor(update.key, my_key))`.
    #       The first K bits that match theirs should be processed
    #       because they are on the same branch (diverging at K+1).
    #       This reduces the total amount of processing the client
    #       does when iterating through logs from this contract.


@public
def set(_key: bytes32, _value: bytes32, _proof: bytes32[160]):
    self._set(_key, _value, _proof)
