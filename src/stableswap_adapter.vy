# pragma version 0.4.1
# @license MIT

"""
@title Stableswap CurveV1 Adapter
@author denissosnowsky
@notice This contract links to all stableswap pools on CurveV1
There are two types of stableswaps: base pool and metapool
Both can be used for adding/removing liquidity, exchanging tokens
Both have gauge contract to stake lp tokens and earn CRV tokens
CRV tokens can be claimed from minter (CRV emission rewards) and gauge (permissionless rewards)
In this contract we allow claiming CRV rewards from minter only.
Metapool has zapper contract as well, but we do not use them in this contract
"""

from snekmate.auth import ownable
from interfaces import i_basepool
from interfaces import i_metapool
from interfaces import i_meta_registry
from interfaces import i_minter
from interfaces import i_gauge
from libraries import stableswap_liquidity
from ethereum.ercs import IERC20

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
# minter address used to claim CRV rewards
minter: public(immutable(i_minter))

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


# Emitted when liquidity is removed from a pool
event LiquidityRemoved:
    pool: indexed(address)
    min_amounts: DynArray[uint256, MAX_COINS]
    amount: uint256


# Emitted when liquidity is removed from a pool
event LiquidityRemovedImbalanced:
    pool: indexed(address)
    amounts: DynArray[uint256, MAX_COINS]
    burn_amount: uint256


# Emitted when liquidity is removed from a pool
event LiquidityRemovedOneCoin:
    pool: indexed(address)
    coin_index: int128
    lp_amount: uint256
    min_amount: uint256
    out_amount: uint256


# Emitted when coins are exchanged
event Exchange:
    pool: indexed(address)
    index_in: int128
    index_out: int128
    amount_in: uint256
    min_amount_out: uint256
    out_amount: uint256


# Emitted when liquidity is deposited for CRV tokens
event LiquidityDepositedForCrv:
    pool: indexed(address)
    lp_amount: uint256


# Emitted when CRV rewards are claimed
event CrvRewardsClaimed:
    pool: indexed(address)


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

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(pool_address)

    # because some tokens can have fees on transfer, we need to approve and send to curve pool actual amounts after fees charged
    amounts_after_fees: DynArray[uint256, MAX_COINS] = []

    counter: uint256 = 0
    for amount: uint256 in amounts:
        in_coin: address = coins[counter]
        counter += 1
        if amount > 0:
            balance_before_fees: uint256 = staticcall IERC20(in_coin).balanceOf(
                self
            )

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

            balance_after_fees: uint256 = staticcall IERC20(in_coin).balanceOf(
                self
            )
            amount_after_fees: uint256 = (
                balance_after_fees - balance_before_fees
            )

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

    stableswap_liquidity._add_liquidity(
        pool_info.contract, amounts_after_fees, min_mint_amount
    )

    lp_balance_after: uint256 = staticcall IERC20(pool_info.lp_token).balanceOf(
        self
    )
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


@external
@nonreentrant
def remove_liquidity(
    pool_address: address,
    amount: uint256,
    min_amounts: DynArray[uint256, MAX_COINS],
):
    """
    @notice Remove liquidity from a pool
    @param amount amount of lp tokens to remove
    @param min_amounts array of minimum amounts of coins to receive
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, min_amounts)

    pool_info: Pool = self.pool_registry[pool_address]

    response_tf: Bytes[32] = raw_call(
        pool_info.lp_token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(msg.sender, bytes32),
            convert(self, bytes32),
            convert(amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response_tf) > 0:
        assert convert(
            response_tf, bool
        ), "stableswap_adapter: failed to transfer coins"

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(pool_address)

    balances_before: DynArray[uint256, MAX_COINS] = []
    counter_before: uint256 = 0
    for i: uint256 in min_amounts:
        balances_before.append(
            staticcall IERC20(coins[counter_before]).balanceOf(self)
        )
        counter_before += 1

    stableswap_liquidity._remove_liquidity(
        pool_info.contract, amount, min_amounts
    )

    balances_after: DynArray[uint256, MAX_COINS] = []
    counter_after: uint256 = 0
    for i: uint256 in min_amounts:
        balances_after.append(
            staticcall IERC20(coins[counter_after]).balanceOf(self)
        )
        counter_after += 1

    counter: uint256 = 0
    for i: uint256 in min_amounts:
        out_amount: uint256 = balances_after[counter] - balances_before[counter]

        if out_amount > 0:
            response_t: Bytes[32] = raw_call(
                coins[counter],
                concat(
                    method_id("transfer(address,uint256)"),
                    convert(msg.sender, bytes32),
                    convert(out_amount, bytes32),
                ),
                max_outsize=32,
            )
            if len(response_t) > 0:
                assert convert(
                    response_t, bool
                ), "stableswap_adapter: failed to transfer coins"
        counter += 1

    log LiquidityRemoved(
        pool=pool_address,
        min_amounts=min_amounts,
        amount=amount,
    )


@external
@nonreentrant
def remove_liquidity_imbalance(
    pool_address: address,
    amounts: DynArray[uint256, MAX_COINS],
    max_burn_amount: uint256,
):
    """
    @notice Remove liquidity from a pool
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to remove
    @param max_burn_amount maximum amount of lp tokens to burn
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, amounts)

    pool_info: Pool = self.pool_registry[pool_address]

    response_tf: Bytes[32] = raw_call(
        pool_info.lp_token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(msg.sender, bytes32),
            convert(self, bytes32),
            convert(max_burn_amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response_tf) > 0:
        assert convert(
            response_tf, bool
        ), "stableswap_adapter: failed to transfer coins"

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(pool_address)

    balances_before: DynArray[uint256, MAX_COINS] = []
    counter_before: uint256 = 0
    for i: uint256 in amounts:
        balances_before.append(
            staticcall IERC20(coins[counter_before]).balanceOf(self)
        )
        counter_before += 1

    lp_balance_before: uint256 = staticcall IERC20(
        pool_info.lp_token
    ).balanceOf(self)

    stableswap_liquidity._remove_imbalanced_liquidity(
        pool_info.contract, amounts, max_burn_amount
    )

    lp_balance_after: uint256 = staticcall IERC20(pool_info.lp_token).balanceOf(
        self
    )
    burn_amount: uint256 = lp_balance_before - lp_balance_after

    balances_after: DynArray[uint256, MAX_COINS] = []
    counter_after: uint256 = 0
    for i: uint256 in amounts:
        balances_after.append(
            staticcall IERC20(coins[counter_after]).balanceOf(self)
        )
        counter_after += 1

    counter: uint256 = 0
    for i: uint256 in amounts:
        out_amount: uint256 = balances_after[counter] - balances_before[counter]

        if out_amount > 0:
            response_t: Bytes[32] = raw_call(
                coins[counter],
                concat(
                    method_id("transfer(address,uint256)"),
                    convert(msg.sender, bytes32),
                    convert(out_amount, bytes32),
                ),
                max_outsize=32,
            )
            if len(response_t) > 0:
                assert convert(
                    response_t, bool
                ), "stableswap_adapter: failed to transfer coins"
        counter += 1

    if burn_amount < max_burn_amount:
        response_t: Bytes[32] = raw_call(
            pool_info.lp_token,
            concat(
                method_id("transfer(address,uint256)"),
                convert(msg.sender, bytes32),
                convert(max_burn_amount - burn_amount, bytes32),
            ),
            max_outsize=32,
        )
        if len(response_t) > 0:
            assert convert(
                response_t, bool
            ), "stableswap_adapter: failed to transfer coins"
    log LiquidityRemovedImbalanced(
        pool=pool_address,
        amounts=amounts,
        burn_amount=burn_amount,
    )


@external
@nonreentrant
def remove_liquidity_one_coin(
    pool_address: address,
    coin_index: int128,
    lp_amount: uint256,
    min_amount: uint256,
):
    """
    @notice Remove liquidity from a pool
    @param pool_address address of the pool contract
    @param coin_index index of the coin to remove
    @param lp_amount amount of lp tokens to remove
    @param min_amount minimum amount of coin to receive
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    response_tf: Bytes[32] = raw_call(
        pool_info.lp_token,
        concat(
            method_id("transferFrom(address,address,uint256)"),
            convert(msg.sender, bytes32),
            convert(self, bytes32),
            convert(lp_amount, bytes32),
        ),
        max_outsize=32,
    )
    if len(response_tf) > 0:
        assert convert(
            response_tf, bool
        ), "stableswap_adapter: failed to transfer coins"

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(pool_address)

    coin_indexed_balance_before: uint256 = staticcall IERC20(
        coins[coin_index]
    ).balanceOf(self)

    if pool_info.pool_type == PoolType.BASE:
        extcall i_basepool(pool_info.contract).remove_liquidity_one_coin(
            lp_amount, coin_index, min_amount
        )
    else:
        extcall i_metapool(pool_info.contract).remove_liquidity_one_coin(
            lp_amount, coin_index, min_amount
        )

    coin_indexed_balance_after: uint256 = staticcall IERC20(
        coins[coin_index]
    ).balanceOf(self)

    out_amount: uint256 = (
        coin_indexed_balance_after - coin_indexed_balance_before
    )

    if out_amount > 0:
        response_t: Bytes[32] = raw_call(
            coins[coin_index],
            abi_encode(
                msg.sender,
                out_amount,
                method_id=method_id("transfer(address,uint256)"),
            ),
            max_outsize=32,
        )
        if len(response_t) > 0:
            assert convert(
                response_t, bool
            ), "stableswap_adapter: failed to transfer coins"
    log LiquidityRemovedOneCoin(
        pool=pool_address,
        coin_index=coin_index,
        lp_amount=lp_amount,
        min_amount=min_amount,
        out_amount=out_amount,
    )


@external
@nonreentrant
def exchange(
    pool_address: address,
    index_in: int128,
    index_out: int128,
    amount_in: uint256,
    min_amount_out: uint256,
):
    """
    @notice Exchange coins in a pool
    @param pool_address address of the pool contract
    @param index_in index of the coin to exchange
    @param index_out index of the coin to receive
    @param amount_in amount of coin to exchange
    @param min_amount_out minimum amount of coin to receive
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    assert index_in >= convert(0, int128) and index_in < convert(
        pool_info.n_coins, int128
    ), "stableswap_adapter: index in out of bounds"
    assert index_out >= convert(0, int128) and index_out < convert(
        pool_info.n_coins, int128
    ), "stableswap_adapter: index out out of bounds"
    assert (
        index_in != index_out
    ), "stableswap_adapter: index in and index out cannot be the same"

    coins: address[MAX_COINS] = staticcall meta_registry.get_coins(pool_address)

    response_tf: Bytes[32] = raw_call(
        coins[index_in],
        abi_encode(
            msg.sender,
            self,
            amount_in,
            method_id=method_id("transferFrom(address,address,uint256)"),
        ),
        max_outsize=32,
    )
    if len(response_tf) > 0:
        assert convert(
            response_tf, bool
        ), "stableswap_adapter: failed to transfer coins"

    response_t: Bytes[32] = raw_call(
        coins[index_in],
        abi_encode(
            pool_info.contract,
            amount_in,
            method_id=method_id("approve(address,uint256)"),
        ),
        max_outsize=32,
    )
    if len(response_t) > 0:
        assert convert(
            response_t, bool
        ), "stableswap_adapter: failed to transfer coins"

    out_token_balance_before: uint256 = staticcall IERC20(
        coins[index_out]
    ).balanceOf(self)

    if pool_info.pool_type == PoolType.BASE:
        extcall i_basepool(pool_info.contract).exchange(
            index_in, index_out, amount_in, min_amount_out
        )
    else:
        extcall i_metapool(pool_info.contract).exchange(
            index_in, index_out, amount_in, min_amount_out
        )

    out_token_balance_after: uint256 = staticcall IERC20(
        coins[index_out]
    ).balanceOf(self)

    out_amount: uint256 = out_token_balance_after - out_token_balance_before

    if out_amount > 0:
        response_t_out: Bytes[32] = raw_call(
            coins[index_out],
            abi_encode(
                msg.sender,
                out_amount,
                method_id=method_id("transfer(address,uint256)"),
            ),
            max_outsize=32,
        )
        if len(response_t_out) > 0:
            assert convert(
                response_t_out, bool
            ), "stableswap_adapter: failed to transfer coins"
    log Exchange(
        pool=pool_address,
        index_in=index_in,
        index_out=index_out,
        amount_in=amount_in,
        min_amount_out=min_amount_out,
        out_amount=out_amount,
    )


@external
@nonreentrant
def deposit_lp_for_crv(pool_address: address, lp_amount: uint256):
    """
    @notice Deposit lp tokens for CRV tokens
    @param pool_address address of the pool contract
    @param lp_amount amount of lp tokens to deposit
    notice Required msg.sender to have approved this contract to deposit lp tokens to gauge
    msg.sender should call 'def set_approve_deposit(addr: address, can_deposit: bool)' from gauge contract
    to allow this contract to deposit lp tokens to gauge
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    response_tf: Bytes[32] = raw_call(
        pool_info.lp_token,
        abi_encode(
            msg.sender,
            self,
            lp_amount,
            method_id=method_id("transferFrom(address,address,uint256)"),
        ),
        max_outsize=32,
    )
    if len(response_tf) > 0:
        assert convert(
            response_tf, bool
        ), "stableswap_adapter: failed to transfer coins"

    response_a: Bytes[32] = raw_call(
        pool_info.lp_token,
        abi_encode(
            pool_info.gauge,
            lp_amount,
            method_id=method_id("approve(address,uint256)"),
        ),
        max_outsize=32,
    )
    if len(response_a) > 0:
        assert convert(
            response_a, bool
        ), "stableswap_adapter: failed to transfer coins"

    extcall i_gauge(pool_info.gauge).deposit(lp_amount, msg.sender)

    log LiquidityDepositedForCrv(
        pool=pool_address,
        lp_amount=lp_amount,
    )


@external
def claim_crv_rewards(pool_address: address):
    """
    @notice Claim CRV rewards from minter
    @param pool_address address of the pool contract
    Required msg.sender to have approved this contract to claim CRV rewards from minter
    msg.sender should call 'def toggle_approve_mint(minting_user: address)' from minter contract
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    extcall minter.mint_for(pool_info.gauge, msg.sender)

    log CrvRewardsClaimed(
        pool=pool_address,
    )


# ------------------------------------------------------------------
#                               VIEW
# ------------------------------------------------------------------

@external
@view
def get_exchange_amount_out(
    pool_address: address,
    index_in: int128,
    index_out: int128,
    amount_in: uint256,
) -> uint256:
    """
    @notice Get the amount of coins out after exchanging
    @param pool_address address of the pool contract
    @param index_in index of the coin to exchange
    @param index_out index of the coin to receive
    @param amount_in amount of coin to exchange
    @return amount_out amount of coin to receive
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    assert index_in >= convert(0, int128) and index_in < convert(
        pool_info.n_coins, int128
    ), "stableswap_adapter: index in out of bounds"
    assert index_out >= convert(0, int128) and index_out < convert(
        pool_info.n_coins, int128
    ), "stableswap_adapter: index out out of bounds"
    assert (
        index_in != index_out
    ), "stableswap_adapter: index in and index out cannot be the same"

    out_amount: uint256 = 0
    if pool_info.pool_type == PoolType.BASE:
        out_amount = staticcall i_basepool(pool_info.contract).get_dy(
            index_in, index_out, amount_in
        )
    else:
        out_amount = staticcall i_metapool(pool_info.contract).get_dy(
            index_in, index_out, amount_in
        )

    return out_amount


@external
@view
def get_lp_amount_after_remove_one_coin(
    pool_address: address,
    coin_index: int128,
    lp_amount: uint256,
) -> uint256:
    """
    @notice Get the amount of lp tokens after removing one coin
    @param pool_address address of the pool contract
    @param coin_index index of the coin to remove
    @param lp_amount amount of lp tokens to remove
    @return lp_amount amount of lp tokens after removing one coin
    """
    self._check_is_pool_valid(pool_address)

    pool_info: Pool = self.pool_registry[pool_address]

    out_amount: uint256 = 0
    if pool_info.pool_type == PoolType.BASE:
        out_amount = staticcall i_basepool(
            pool_info.contract
        ).calc_withdraw_one_coin(lp_amount, coin_index)
    else:
        out_amount = staticcall i_metapool(
            pool_info.contract
        ).calc_withdraw_one_coin(lp_amount, coin_index)

    return out_amount


@external
@view
def get_lp_amount_after_deposit(
    pool_address: address, amounts: DynArray[uint256, MAX_COINS]
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing amounts
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to add
    @return lp_amount amount of lp tokens after depositing amounts
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, amounts)
    return stableswap_liquidity._get_lp_amount_after_deposit(
        pool_address, amounts, True
    )


@external
@view
def get_lp_amount_after_withdraw(
    pool_address: address, amounts: DynArray[uint256, MAX_COINS]
) -> uint256:
    """
    @notice Get the amount of lp tokens after withdrawing amounts
    @param pool_address address of the pool contract
    @param amounts array of amounts of coins to withdraw
    @return lp_amount amount of lp tokens after withdrawing amounts
    """
    self._check_is_pool_valid(pool_address)
    self._check_are_amounts_valid(pool_address, amounts)
    return stableswap_liquidity._get_lp_amount_after_deposit(
        pool_address, amounts, False
    )


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
def _check_are_amounts_valid(
    pool_address: address, amounts: DynArray[uint256, MAX_COINS]
):
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
