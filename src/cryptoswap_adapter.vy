# pragma version 0.4.1
# @license MIT

"""
@title CryptoSwap Adapter
@author denissosnowsky
@notice This contract links to all cryptoswap pools on CurveV2.
Can be used for adding/removing liquidity, exchanging tokens.
Has gauge contract to stake lp tokens and earn CRV tokens.
CRV tokens can be claimed from minter (CRV emission rewards) and gauge (permissionless rewards).
In this contract we allow claiming CRV rewards from minter only.
Has zapper contract as well, but we do not use them in this contract.
"""

from snekmate.auth import ownable
from interfaces import i_meta_registry
from interfaces import i_minter
from interfaces import i_gauge
from ethereum.ercs import IERC20

initializes: ownable

exports: ownable.__interface__

# ------------------------------------------------------------------
#                              TYPES
# ------------------------------------------------------------------

# Stores pool information
struct Pool:
    # address of the pool contract
    contract: address
    # address of the gauge contract
    gauge: address
    # address of the zapper contract
    zapper: address
    # address of the lp token
    lp_token: address
    # number of coins in the pool
    n_coins: uint256

# ------------------------------------------------------------------
#                              STATE
# ------------------------------------------------------------------

# max number of coins in a pool
MAX_COINS: constant(uint256) = 3
# max number of pools that can be registered
POOLS_CAP: constant(uint256) = 1000
# meta registry address used to validate pools and their types
meta_registry: public(immutable(i_meta_registry))
# minter address used to claim CRV rewards
minter: public(immutable(i_minter))

# registry of pools
pool_registry: public(HashMap[address, Pool])
# set of pool addresses
pool_registry_set: public(DynArray[address, POOLS_CAP])

# ------------------------------------------------------------------
#                              EVENTS
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#                            FUNCTIONS
# ------------------------------------------------------------------

@deploy
def __init__(_meta_registry: address, _minter: address):
    ownable.__init__()
    meta_registry = i_meta_registry(_meta_registry)
    minter = i_minter(_minter)


# ------------------------------------------------------------------
#                             EXTERNAL
# ------------------------------------------------------------------