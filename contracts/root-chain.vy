# Entry
# NOTE: Entries may need a challenge due to zk properties of wallet reset
#       For example, user onboards asset that has been minted prior with incr'd nonce
#       However, another user in the Plasma chain has rights to the old token and continues trading
#       We could burn the old token, but then the user would have to reveal their own token
#
#       So... thinking about this from a basic perspective, if user has a picture of serial number
#       and we decide to mint them a new token, and another person had the old token and it is burned
#       on them, then there is a dispute. The resolution of the dispute is unclear as it is a physical
#       asset and therefore must be validated in person by a trusted third party. But if we just let
#       this happen, we can blacklist who we find to be the bad actor, and they would have to obtain
#       another address. If we charge per token to mint (i.e. we will not mint without being paid),
#       then there is a disincentive to this sybil attack.
#
#       Therefore, perhaps the trivial case of burning whatever token was onboarded last (which may
#       inconvience users) should be minimized as there is a disincentive for that action.


# Exit
# NOTE: SNARKs don't need a challenge for exits, so instant exit


# Block sync
# Params:
#   plasmaBlockTime: 2 mins
#       - Confirmation time of transaction on Plasma chain
#       - NOTE: Plasma Cash has instant finality due to SMT
#   plasmaSyncTime: 7 days (5040 plasma blocks, max 2419200 txns @ 4 tps)
#       - This is how often we synchronize with Plasma
#       - No single tokenId can be transferred twice in this period
#   checkpointTime: 28 days (4 sync periods)
#       - can only issue challenges up to the 2nd most previous checkpoint
#       - NOTE: contract storage of history prior to 2 most recent checkpoints is not available


# Interface to the authlist
contract Authlist:
    def root() -> bytes32: constant
    def status(_user) -> uint256: constant


# Plasma chain operator
operator: public(address)


# Authlist and Plasma-chain roots are synchronized every 7 days
plasmachain_root: public(bytes32)
PLASMA_SYNC_TIME: timedelta = constant(604800) # 7 days in secs
last_synced: public(timestamp)


# 28 day checkpoint history (not including current setpoints)
# 28/7 - 1 = 3
root_history: {authlist: bytes32, plasma: bytes32}[3]


def __init__(_authlist: address):
    self.operator = msg.sender
    self.authlist = Authlist(_authlist)
    self.last_synced = 0  # Let the operator publish a block immediately
    # Note: root_history is left empty


def addBlock(_plasma_root: bytes32):
    # Only operator can submit a new root
    assert msg.sender == self.operator

    # Enough time has passed
    assert blk.timestamp - self.last_synced >= PLASMA_SYNC_TIME

    # Pop oldest and shuffle
    self.root_history[0] = self.root_history[1]
    self.root_history[1] = self.root_history[2]

    # Push current
    self.root_history[2] = {
        authlist: self.authlist.root(),
        plasma: self.plasmachain_root
    }

    # Set current plasma root
    self.plasmachain_root = _plasma_root
