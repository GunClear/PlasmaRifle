#
############################################################################
#%                                                                         %
#%    ██████╗                     ██████╗                                  %
#%   ██╔════╝ ██╗   ██╗███╗  ██╗ ██╔════╝██╗     ███████╗ █████╗ ██████╗   %
#%   ██║      ██║   ██║████╗ ██║ ██║     ██║     ██╔════╝██║  ██╗██║  ██╗  %
#%   ██║  ███╗██║   ██║██╔██╗██║ ██║     ██║     █████╗  ███████║██████╔╝  %
#%   ██║   ██║██║   ██║██║╚████║ ██║     ██║     ██╔══╝  ██╔══██║██╔══██╗  %
#%   ╚██████╔╝╚██████╔╝██║ ╚███║ ╚██████╗███████╗███████╗██║  ██║██║  ██║  %
#%    ╚═════╝  ╚═════╝ ╚═╝  ╚══╝  ╚═════╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝  %
#%                                                                         %
############################################################################
#
#  @title The GunClear GUN Token
#  @dev   ERC721 token
#         w/ Mint/Burn functionality
#         w/o Approvals or Custodialship (Operators)
#         Represents tokenized firearms
#
#  @author Bryant Eisenbach (@fubuloubu)
#
#  (C) 2018 GunClear, inc.
#
#  Made available under MIT License
#


#@dev Interface for the contract called by safeTransferFrom()
contract NFTReceiver:
    def onERC721Received(
            _operator: address,
            _from: address,
            _tokenId: uint256,
            _data: bytes[1024]
        ) -> bytes32: constant


#@dev   Emits when ownership of any NFT changes by any mechanism. This event emits when NFTs are
#       created (`from` == 0) and destroyed (`to` == 0).
#@param _from       Sender of NFT (if address is zero address it indicates token creation).
#@param _to         Receiver of NFT (if address is zero address it indicates token destruction).
#@param _tokenId    The NFT that got transfered.
Transfer: event({
        _from: indexed(address),
        _to: indexed(address),
        _tokenId: indexed(uint256)
    })


#@dev   Mapping from NFT ID to the address that owns it.
idToOwner: address[uint256]

#@dev   Mapping from owner address to count of their tokens.
ownerToNFTokenCount: uint256[address]

#@dev   Contract owner. Has special privledges to mint new tokens.
authority: public(address)

#@dev   Transitional variables used to change owner.
pendingAuthority: public(address)


#@dev   Contract constructor. Sets the owner
@public
def __init__():
    self.authority = msg.sender


#
# Authority Assignee functions
#

#@
@public
def nominateAuthority(_authority: address):
    assert msg.sender == self.authority
    self.pendingAuthority = _authority

@public
def acceptNomination():
    assert msg.sender == self.pendingAuthority
    self.authority = self.pendingAuthority


#
# ERC 721 Functions
#

# @dev Returns the number of NFTs owned by `_owner`. NFTs assigned to the zero address are
#      considered invalid, and this function throws for queries about the zero address.
# @param _owner Address for whom to query the balance.
@public
@constant
def balanceOf(_owner: address) -> uint256:
    assert _owner != ZERO_ADDRESS
    return self.ownerToNFTokenCount[_owner]


# @dev Returns the address of the owner of the NFT. NFTs assigned to zero address are considered
#      invalid, and queries about them do throw. 
# @param _tokenId The identifier for an NFT.
@public
@constant
def ownerOf(_tokenId: uint256) -> address:
    assert self.idToOwner[_tokenId] != ZERO_ADDRESS
    return self.idToOwner[_tokenId]

# NOTE: No regular `transferFrom` is provided as the primary use case is for locking into the Plasma contract


# @dev Transfers the ownership of an NFT to another address.
# @notice   Throws unless `msg.sender` is the current owner
#           Throws if `_from` is not `msg.sender`.
#           Throws if `_to` is the zero address.
#           Throws if `_tokenId` is not a valid NFT (aka is zero).
#           When transfer is complete, this function checks if `_to` is a smart contract (code size > 0).
#           If so, it calls `onERC721Received()` on `_to` and throws if the return value is not
#               `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`
#           NOTE: bytes4 (the official ABI spec for this feature) is represented by bytes32 with padding
# @param _from The current owner of the NFT [UNUSED]
# @param _to The new owner
# @param _tokenId The NFT to transfer
# @param _data Additional data with no specified format, sent in call to `_to` [UNUSED]
@public
def safeTransferFrom(
        _from: address,
        _to: address,
        _tokenId: uint256,
        _data: bytes[1024]=""
    ):
    # _from must be the transaction sender. Done for compatibility
    assert _from == msg.sender

    # Check that _to is valid addresses (non-zero)
    assert _to != ZERO_ADDRESS

    # Throws if `msg.sender` is not the current owner
    assert self.idToOwner[_tokenId] == msg.sender
    
    # Change the owner
    self.idToOwner[_tokenId] = _to
    
    # Change count tracking
    self.ownerToNFTokenCount[_to] += 1
    self.ownerToNFTokenCount[msg.sender] -= 1
    
    # Log the transfer
    log.Transfer(msg.sender, _to, _tokenId)
    
    # If the reciever is a smart contract, then ensure it executes a "safe" transaction by validating the return code
    if(_to.codesize > 0):
        returnValue: bytes32 = NFTReceiver(_to).onERC721Received(msg.sender, msg.sender, _tokenId, _data)
        # Validate the return code is the correct method ID
        assert returnValue == method_id('onERC721Received(address,address,uint256,bytes)', bytes32)


#@dev Mint new token with ID `_tokenID` to `_owner`
#@notice    This function allows the authority to mint a new token to the specified recipient
#           The token must not currently exist
#           The `tokenId` is generated by the authority, and is composed of the serial number
#           and a secret nonce that is only made available to selected parties, both of which
#           are hashed together to generate the tokenId (and converted to uint256)
#           In order to limit the depth of the SMT storing these tokens in the Gunero network,
#           only the first 20 bytes are used to represent the tokenId. This should be acceptable
#@param _to         Recipient of the NFT
#@param _tokenId    The Id of the newly minted token
@public
def mint(_to: address, _tokenId: uint256):
    # Only the authority can mint
    assert msg.sender == self.authority

    # A token can be minted only if it doesn't exist (is unowned)
    assert self.idToOwner[_tokenId] == ZERO_ADDRESS

    # Give the token to the mintee
    self.idToOwner[_tokenId] = _to

    # Change count tracking
    self.ownerToNFTokenCount[_to] += 1

    # Log the transfer (A "mint" is a transfer from the zero addr)
    log.Transfer(ZERO_ADDRESS, _to, _tokenId)


#@dev   Burns an existing token with ID `_tokenId`
#@notice    This function allows the current owner to "burn" or remove the specified token from
#           the supply. At that point, it is no longer considered to be tracking the underlying
#           asset at all, as it has been decided to remove it from the system.
#@param _tokenId    The Id of the token to be destroyed
@public
def burn(_tokenId: uint256):
    # Validate ownership of token
    assert msg.sender == self.idToOwner[_tokenId]

    # Reset the owner for tokenId (destroys the token)
    self.idToOwner[_tokenId] = ZERO_ADDRESS

    # Change count tracking
    self.ownerToNFTokenCount[msg.sender] -= 1

    # Log the transfer (A "burn" is a transfer to the zero addr)
    log.Transfer(msg.sender, ZERO_ADDRESS, _tokenId)
