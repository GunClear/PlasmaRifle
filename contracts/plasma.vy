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
