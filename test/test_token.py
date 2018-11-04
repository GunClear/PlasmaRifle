import pytest
from eth_tester.exceptions import TransactionFailed


@pytest.fixture
def token(vy_deployer):
    # We don't need the address...
    package, _ = vy_deployer.deploy('gun-token')
    return package.deployments.get_contract_instance('gun-token')


def test_nominateAuthority(w3, token):
    # The authority is whomever deployed the contract
    assert token.functions.authority().call() == w3.eth.accounts[0]
    # Only the authority can nominate a successor
    with pytest.raises(TransactionFailed):
        token.functions.nominateAuthority(w3.eth.accounts[1]).transact({'from':w3.eth.accounts[1]})
    token.functions.nominateAuthority(w3.eth.accounts[1]).transact({'from':w3.eth.accounts[0]})
    # Nomination doesn't select an authority until accepted
    assert token.functions.authority().call() == w3.eth.accounts[0]
    assert token.functions.pendingAuthority().call() == w3.eth.accounts[1]
    # No one else besides the nominee can accept
    with pytest.raises(TransactionFailed):
        token.functions.acceptNomination().transact({'from':w3.eth.accounts[0]})
    with pytest.raises(TransactionFailed):
        token.functions.acceptNomination().transact({'from':w3.eth.accounts[0]})
    # Only the nominee can accept
    token.functions.acceptNomination().transact({'from':w3.eth.accounts[1]})
    assert token.functions.authority().call() == w3.eth.accounts[1]


TOKEN_ID = 123


def test_mint(w3, token):
    assert token.functions.balanceOf(w3.eth.accounts[1]).call() == 0  # For later
    # Only the authority can mint
    with pytest.raises(TransactionFailed):
        token.functions.mint(w3.eth.accounts[1], TOKEN_ID).transact({'from':w3.eth.accounts[1]})
    token.functions.mint(w3.eth.accounts[1], TOKEN_ID).transact({'from':w3.eth.accounts[0]})
    # The same token can't be minted twice
    with pytest.raises(TransactionFailed):
        token.functions.mint(w3.eth.accounts[2], TOKEN_ID).transact({'from':w3.eth.accounts[0]})
    # Minting a token increases the new owner's balance
    assert token.functions.balanceOf(w3.eth.accounts[1]).call() == 1
    # The new token is owned by the mintee
    assert token.functions.ownerOf(TOKEN_ID).call() == w3.eth.accounts[1]

@pytest.fixture
def token_m(w3, token):
    token.functions.mint(w3.eth.accounts[1], TOKEN_ID).transact({'from':w3.eth.accounts[0]})
    return token


def test_burn(w3, token_m):
    # No one can burn a token they don't own
    assert token_m.functions.ownerOf(TOKEN_ID).call() != w3.eth.accounts[2]
    with pytest.raises(TransactionFailed):
        token_m.functions.burn(TOKEN_ID).transact({'from':w3.eth.accounts[2]})
    # Not even the authority
    with pytest.raises(TransactionFailed):
        token_m.functions.burn(TOKEN_ID).transact({'from':w3.eth.accounts[0]})
    # Only the owner can burn it
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 1  # for later...
    assert token_m.functions.ownerOf(TOKEN_ID).call() == w3.eth.accounts[1]
    token_m.functions.burn(TOKEN_ID).transact({'from':w3.eth.accounts[1]})
    # Burning a token_m removes it from the supply
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 0
    # An unowned token_m will throw when queried
    with pytest.raises(TransactionFailed):
        token_m.functions.ownerOf(TOKEN_ID).call()


def test_safeTransferFrom_account(w3, token_m):
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 1
    assert token_m.functions.balanceOf(w3.eth.accounts[2]).call() == 0
    assert token_m.functions.ownerOf(TOKEN_ID).call() == w3.eth.accounts[1]
    # No one other than the owner can transfer the token
    with pytest.raises(TransactionFailed):
        token_m.functions.safeTransferFrom(w3.eth.accounts[1], w3.eth.accounts[2], TOKEN_ID).transact({'from':w3.eth.accounts[2]})
    # An account can transfer to another account with no problems
    token_m.functions.safeTransferFrom(w3.eth.accounts[1], w3.eth.accounts[2], TOKEN_ID).transact({'from':w3.eth.accounts[1]})
    assert token_m.functions.ownerOf(TOKEN_ID).call() == w3.eth.accounts[2]
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 0
    assert token_m.functions.balanceOf(w3.eth.accounts[2]).call() == 1    


from vyper.compiler import compile as vyc
from vyper.compiler import mk_full_signature as vya


@pytest.fixture
def good_receiver(w3):
    CODE = """
@public
def onERC721Received(
        _operator: address,
        _from: address,
        _tokenId: uint256,
        _data: bytes[1024]
    ) -> bytes32:
    return method_id("onERC721Received(address,address,uint256,bytes)", bytes32)
    """
    interface = {
        'abi': vya(CODE),
        'bytecode': vyc(CODE),
        'bytecode_runtime': vyc(CODE, bytecode_runtime=True)
    }
    txn_hash = w3.eth.contract(**interface).constructor().transact()
    address = w3.eth.waitForTransactionReceipt(txn_hash)['contractAddress']
    from eth_utils import to_canonical_address  # Waiting on ethereum/pytest-ethereum #20
    return w3.eth.contract(to_canonical_address(address), **interface)


@pytest.fixture
def bad_receiver(w3):
    CODE = """
@public
def onERC721Received(
        _operator: address,
        _from: address,
        _tokenId: uint256,
        _data: bytes[1024]
    ) -> bytes32:
    return method_id("NOT_RIGHT", bytes32)
    """
    interface = {
        'abi': vya(CODE),
        'bytecode': vyc(CODE),
        'bytecode_runtime': vyc(CODE, bytecode_runtime=True)
    }
    txn_hash = w3.eth.contract(**interface).constructor().transact()
    address = w3.eth.waitForTransactionReceipt(txn_hash)['contractAddress']
    from eth_utils import to_canonical_address  # Waiting on ethereum/pytest-ethereum #20
    return w3.eth.contract(to_canonical_address(address), **interface)


def test_safeTransferFrom_contracts(w3, token_m, good_receiver, bad_receiver):
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 1
    assert token_m.functions.balanceOf(good_receiver.address).call() == 0
    assert token_m.functions.balanceOf(bad_receiver.address).call() == 0
    assert token_m.functions.ownerOf(TOKEN_ID).call() == w3.eth.accounts[1]
    # To receive ERC721 tokens, a contract must implement
    # the full `onERC721Received()` handshake, not just the interface
    with pytest.raises(TransactionFailed):
        token_m.functions.safeTransferFrom(w3.eth.accounts[1], bad_receiver.address, TOKEN_ID).transact({'from':w3.eth.accounts[1]})
    token_m.functions.safeTransferFrom(w3.eth.accounts[1], good_receiver.address, TOKEN_ID).transact({'from':w3.eth.accounts[1]})
    # Contracts can own tokens
    assert token_m.functions.ownerOf(TOKEN_ID).call() == good_receiver.address
    assert token_m.functions.balanceOf(w3.eth.accounts[1]).call() == 0
    assert token_m.functions.balanceOf(good_receiver.address).call() == 1
    assert token_m.functions.balanceOf(bad_receiver.address).call() == 0
