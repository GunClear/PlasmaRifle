import pytest


@pytest.fixture
def token(t):
    return t.c('contracts/gun-token.vy')()


def test_nominateAuthority(t, token):
    # The authority is whomever deployed the contract
    assert token.authority() == t.a[0]
    # Only the authority can nominate a successor
    with t.tx_fails:
        token.nominateAuthority(t.a[1], transact={'from':t.a[1]})
    token.nominateAuthority(t.a[1], transact={'from':t.a[0]})
    # Nomination doesn't select an authority until accepted
    assert token.authority() == t.a[0]
    assert token.pendingAuthority() == t.a[1]
    # No one else besides the nominee can accept
    with t.tx_fails:
        token.acceptNomination(transact={'from':t.a[0]})
    with t.tx_fails:
        token.acceptNomination(transact={'from':t.a[0]})
    # Only the nominee can accept
    token.acceptNomination(transact={'from':t.a[1]})
    assert token.authority() == t.a[1]


TOKEN_ID = 123


def test_mint(t, token):
    assert token.balanceOf(t.a[1]) == 0  # For later
    # Only the authority can mint
    with t.tx_fails:
        token.mint(t.a[1], TOKEN_ID, transact={'from':t.a[1]})
    token.mint(t.a[1], TOKEN_ID, transact={'from':t.a[0]})
    # The same token can't be minted twice
    with t.tx_fails:
        token.mint(t.a[2], TOKEN_ID, transact={'from':t.a[0]})
    # Minting a token increases the new owner's balance
    assert token.balanceOf(t.a[1]) == 1
    # The new token is owned by the mintee
    assert token.ownerOf(TOKEN_ID) == t.a[1]

@pytest.fixture
def token_m(t, token):
    token.mint(t.a[1], TOKEN_ID, transact={'from':t.a[0]})
    return token


def test_burn(t, token_m):
    # No one can burn a token they don't own
    assert token.ownerOf(TOKEN_ID) != t.a[2]
    with t.tx_fails:
        token.burn(TOKEN_ID, transact={'from':t.a[2]})
    # Not even the authority
    with t.tx_fails:
        token.burn(TOKEN_ID, transact={'from':t.a[0]})
    # Only the owner can burn it
    assert token.balanceOf(t.a[1]) == 1  # for later...
    assert token.ownerOf(TOKEN_ID) == t.a[1]
    token.burn(TOKEN_ID, transact={'from':t.a[1]})
    # Burning a token removes it from the supply
    assert token.balanceOf(t.a[1]) == 0
    # An unowned token will throw when queried
    with t.tx_fails:
        token.ownerOf(TOKEN_ID)


def test_safeTransferFrom_account(t, token_m):
    assert token_m.balanceOf(t.a[1]) == 1
    assert token_m.balanceOf(t.a[2]) == 0
    assert token_m.ownerOf(TOKEN_ID) == t.a[1]
    # No one other than the owner can transfer the token
    with t.tx_fails:
        token_m.safeTransferFrom(t.a[1], t.a[2], TOKEN_ID, transact={'from':t.a[2]})
    # An account can transfer to another account with no problems
    token_m.safeTransferFrom(t.a[1], t.a[2], TOKEN_ID, transact={'from':t.a[1]})
    assert token_m.ownerOf(TOKEN_ID) == t.a[2]
    assert token_m.balanceOf(t.a[1]) == 0
    assert token_m.balanceOf(t.a[2]) == 1    


from vyper.compiler import compile as vyc
from vyper.compiler import mk_full_signature as vya

@pytest.fixture
def good_receiver(t):
    code = """
@public
def onERC721Received(
        _operator: address,
        _from: address,
        _tokenId: uint256,
        _data: bytes[1024]
    ) -> bytes32:
    return method_id("onERC721Received(address,address,uint256,bytes)", bytes32)
    """
    return t.get_contract({
            'abi': vya(code),
            'bytecode': vyc(code),
            'bytecode_runtime': vyc(code, bytecode_runtime=True)
        })


@pytest.fixture
def bad_receiver(t, good_receiver):
    return t.new_contract({'abi': good_receiver.abi,
        'bytecode': '0x0',
        'bytecode_runtime': '0x0'
    })


def test_safeTransferFrom_contracts(t, token_m, good_receiver, bad_receiver):
    assert token_m.balanceOf(t.a[1]) == 1
    assert token_m.balanceOf(good_receiver.address) == 0
    assert token_m.balanceOf(bad_receiver.address) == 0
    assert token_m.ownerOf(TOKEN_ID) == t.a[1]
    # To receive ERC721 tokens, a contract must implement
    # the full `onERC721Received()` handshake, not just the interface
    with t.tx_fails:
        token_m.safeTransferFrom(t.a[1], bad_receiver.address, TOKEN_ID, transact={'from':t.a[1]})
    token_m.safeTransferFrom(t.a[1], good_receiver.address, TOKEN_ID, transact={'from':t.a[1]})
    # Contracts can own tokens
    assert token_m.ownerOf(TOKEN_ID) == good_receiver.address
    assert token_m.balanceOf(t.a[1]) == 0
    assert token_m.balanceOf(good_receiver.address) == 1
    assert token_m.balanceOf(bad_receiver.address) == 0
