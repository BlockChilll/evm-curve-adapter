# pragma version 0.4.1
# @license MIT

"""
@title Stableswap CurveV1 Adapter
@author denissosnowsky
@notice This contract links to all stableswap pools on CurveV1
There are two types of stableswaps: base pool and metapool
Both can be used for adding/removing liquidity, exchanging tokens
Both have gauge contract to stake lp tokens and earn CRV tokens
Metapool has zapper contract as well, but we do not use them in this contract
"""

from snekmate.auth import ownable
from interfaces import i_basepool
from interfaces import i_metapool
from interfaces import i_meta_registry

initializes: ownable

exports: ownable.__interface__

# ------------------------------------------------------------------
#                              TYPES
# ------------------------------------------------------------------

# Indicates the type of stableswap pool
flag PoolType:
    # standard Curve stableswap pool
    BASE
    #  metapool built on top of a base pool (uses LP token from base pool)
    META


# Stores pool information
struct Pool:
    # address of the pool contract
    contract: address
    # type of the pool
    pool_type: PoolType
    # address of the gauge contract
    gauge: address
    # address of the zapper contract
    zapper: address
    # address of the lp token
    lp_token: address


# ------------------------------------------------------------------
#                              STATE
# ------------------------------------------------------------------

# max number of pools that can be registered
POOLS_CAP: constant(uint256) = 1000
# meta registry address used to validate pools and their types
meta_registry: public(immutable(i_meta_registry))

# registry of pools
pool_registry: public(HashMap[address, Pool])
# set of pool addresses
pool_registry_set: public(DynArray[address, POOLS_CAP])

# ------------------------------------------------------------------
#                              EVENTS
# ------------------------------------------------------------------

# Emitted when a new pool is registered
event PoolRegistered:
    pool: indexed(address)
    pool_type: indexed(PoolType)
    gauge: indexed(address)
    zapper: address
    lp_token: address


# ------------------------------------------------------------------
#                            FUNCTIONS
# ------------------------------------------------------------------

@deploy
def __init__(_meta_registry: address):
    ownable.__init__()
    meta_registry = i_meta_registry(_meta_registry)


# ------------------------------------------------------------------
#                             EXTERNAL
# ------------------------------------------------------------------

@external
def register_pool(pool_address: address, zapper_address: address):
    """
    @notice Register a new pool in the adapter.
    @param pool_address address of the pool contract
    @param zapper_address address of the zapper contract if applicable
    @dev This function is only callable by the owner of the contract.
    @dev This function will register the pool in the adapter.
    @dev It will fetch pool info from meta registry and register it in the adapter.
    """

    ownable._check_owner()

    assert (
        pool_address not in self.pool_registry_set
    ), "stableswap_adapter: pool already registered"

    # check if pool is registered in meta registry (native curve registry)
    # make raw_call for custom error handling
    # second optional argument must be set in raw_call
    success: bool = False
    response: Bytes[32] = b""
    success, response = raw_call(
        meta_registry.address,
        concat(
            method_id("is_registered(address,uint256)"),
            convert(pool_address, bytes32),
            convert(0, bytes32),
        ),
        max_outsize=32,
        revert_on_failure=False,
    )
    assert (
        success
    ), "stableswap_adapter: pool is not registered in meta registry"

    is_meta: bool = staticcall meta_registry.is_meta(pool_address)
    pool_gauge: address = staticcall meta_registry.get_gauge(pool_address)
    lp_token: address = staticcall meta_registry.get_lp_token(pool_address)

    pool_type: PoolType = PoolType.META if is_meta else PoolType.BASE

    if pool_type == PoolType.META and zapper_address == empty(address):
        raise "stableswap_adapter: zapper address is required for metapools"

    self.pool_registry_set.append(pool_address)
    self.pool_registry[pool_address] = Pool(
        contract=pool_address,
        pool_type=pool_type,
        gauge=pool_gauge,
        zapper=zapper_address,
        lp_token=lp_token,
    )

    log PoolRegistered(
        pool=pool_address,
        pool_type=pool_type,
        gauge=pool_gauge,
        zapper=zapper_address,
        lp_token=lp_token,
    )


# ------------------------------------------------------------------
#                               VIEW
# ------------------------------------------------------------------

@external
@view
def get_pool_info(pool_address: address) -> Pool:
    """
    @notice Get the pool info for a given pool address
    @param pool_address address of the pool contract
    @return pool_info Pool struct containing pool information
    """
    return self.pool_registry[pool_address]


@external
@view
def get_pools_count() -> uint256:
    """
    @notice Get the number of pools registered in the adapter
    @return pools_count number of pools registered
    """
    return len(self.pool_registry_set)


# ------------------------------------------------------------------
#                             INTERNAL
# ------------------------------------------------------------------


