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
from libraries import stableswap_liquidity
from ethereum.ercs import IERC20

initializes: ownable

exports: (ownable.__interface__)

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
    # number of coins in the pool
    n_coins: uint256


# ------------------------------------------------------------------
#                              STATE
# ------------------------------------------------------------------

# max number of coins in a pool
MAX_COINS: constant(uint256) = 8
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
    n_coins: uint256


# Emitted when liquidity is added to a pool
event LiquidityAdded:
    pool: indexed(address)
    amounts: DynArray[uint256, MAX_COINS]
    min_mint_amount: uint256
    mint_amount: uint256


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
    n_coins: uint256 = staticcall meta_registry.get_n_coins(pool_address)

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
        n_coins=n_coins,
    )

    log PoolRegistered(
        pool=pool_address,
        pool_type=pool_type,
        gauge=pool_gauge,
        zapper=zapper_address,
        lp_token=lp_token,
        n_coins=n_coins,
    )


@external
@nonreentrant
def add_liquidity(
    pool_address: address,
    amounts: DynArray[uint256, MAX_COINS],
    min_mint_amount: uint256,
) -> uint256:
    """
    @notice Add liquidity to a pool
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to add
    @param min_mint_amount minimum amount of lp tokens to mint
    @return mint_amount amount of lp tokens minted
    """

    pool_info: Pool = self.pool_registry[pool_address]

    self._check_are_amounts_valid(pool_address, amounts)
    self._check_is_pool_valid(pool_address)

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(
        pool_address
    )

    # because some tokens can have fees on transfer, we need to approve and send to curve pool actual amounts after fees charged
    amounts_after_fees: DynArray[uint256, MAX_COINS] = []

    counter: uint256 = 0
    for amount: uint256 in amounts:
        in_coin: address = coins[counter]
        counter += 1
        if amount > 0:
            balance_before_fees: uint256 = staticcall IERC20(in_coin).balanceOf(self)

            responseTransfer: Bytes[32] = raw_call(
                in_coin,
                concat(
                    method_id("transferFrom(address,address,uint256)"),
                    convert(msg.sender, bytes32),
                    convert(self, bytes32),
                    convert(amount, bytes32),
                ),
                max_outsize=32,
            )
            if len(responseTransfer) > 0:
                assert convert(
                    responseTransfer, bool
                ), "stableswap_adapter: failed to transfer coins"

            balance_after_fees: uint256 = staticcall IERC20(in_coin).balanceOf(self)
            amount_after_fees: uint256 = balance_after_fees - balance_before_fees

            amounts_after_fees.append(amount_after_fees)

            responseApprove: Bytes[32] = raw_call(
                in_coin,
                concat(
                    method_id("approve(address,uint256)"),
                    convert(pool_info.contract, bytes32),
                    convert(amount_after_fees, bytes32),
                ),
                max_outsize=32,
            )
            if len(responseApprove) > 0:
                assert convert(
                    responseApprove, bool
                ), "stableswap_adapter: failed to approve coins"

    mint_amount: uint256 = 0

    # base pool does not return mint amount
    lp_balance_before: uint256 = staticcall IERC20(
        pool_info.lp_token
    ).balanceOf(self)

    stableswap_liquidity._add_liquidity(pool_info.contract, amounts_after_fees, min_mint_amount)

    lp_balance_after: uint256 = staticcall IERC20(
        pool_info.lp_token
    ).balanceOf(self)
    mint_amount = lp_balance_after - lp_balance_before

    if mint_amount > 0:
        response: Bytes[32] = raw_call(
            pool_info.lp_token,
            concat(
                method_id("transfer(address,uint256)"),
                convert(msg.sender, bytes32),
                convert(mint_amount, bytes32),
            ),
            max_outsize=32,
        )
        if len(response) > 0:
            assert convert(
                response, bool
            ), "stableswap_adapter: failed to transfer coins"
            
    log LiquidityAdded(
        pool=pool_address,
        amounts=amounts,
        min_mint_amount=min_mint_amount,
        mint_amount=mint_amount,
    )

    return mint_amount

# @external
# @nonreentrant
# def remove(_name: type):


# ------------------------------------------------------------------
#                               VIEW
# ------------------------------------------------------------------

@external
@view
def get_lp_amount_after_deposit(pool_address: address, amounts: DynArray[uint256, MAX_COINS]) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing amounts
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to add
    @return lp_amount amount of lp tokens after depositing amounts
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, amounts)
    return stableswap_liquidity._get_lp_amount_after_deposit(pool_address, amounts, True)

@external
@view
def get_lp_amount_after_withdraw(pool_address: address, amounts: DynArray[uint256, MAX_COINS]) -> uint256:
    """
    @notice Get the amount of lp tokens after withdrawing amounts
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to withdraw
    @return lp_amount amount of lp tokens after withdrawing amounts
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, amounts)
    return stableswap_liquidity._get_lp_amount_after_deposit(pool_address, amounts, False)

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

@internal
@view
def _check_is_pool_valid(pool_address: address):
    """
    @notice Check if a pool is valid
    @param pool_address address of the pool contract
    @dev This function will check if the pool is registered in the adapter and if the pool address matches the pool contract address
    """
    pool_info: Pool = self.pool_registry[pool_address]

    assert (
        pool_address == pool_info.contract
    ), "stableswap_adapter: pool address mismatch"

@internal
@view
def _check_are_amounts_valid(pool_address: address, amounts: DynArray[uint256, MAX_COINS]):
    """
    @notice Check if the amounts are valid
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to add
    @dev This function will check if the amounts are valid
    """
    pool_info: Pool = self.pool_registry[pool_address]

    assert (
        len(amounts) == pool_info.n_coins
    ), "stableswap_adapter: invalid number of amounts"