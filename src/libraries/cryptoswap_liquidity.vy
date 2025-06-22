# pragma version 0.4.1
# @license MIT

"""
@notice Library for liquidity management to cryptoswap pools
@author denissosnowsky
@dev This library is used to add, remove and get liquidity from cryptoswap pools
Vyper cannot convert dynamic arrays to fixed size arrays, so we need to use a fixed size array for pool's liquidity functions
For this, we create a separate function for each number of coins in a pool
@dev This library is used in stableswap_adapter.vy
"""

# max number of coins in a pool
MAX_COINS: constant(uint256) = 3


# ------------------------------------------------------------------
#                          ADD LIQUIDITY FUNCTIONS
# ------------------------------------------------------------------

@payable
@internal
def _add_liquidity(
    pool: address,
    amounts: DynArray[uint256, MAX_COINS],
    min_mint_amount: uint256,
    use_eth: bool,
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool
    @param pool address of the pool contract
    @param amounts array of amounts of coins to add
    @param min_mint_amount minimum amount of lp tokens to mint
    @param use_eth whether to use ETH for the exchange
    """
    if len(amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(amounts), 2), bound=2):
            amounts_2[i] = amounts[i]
        return self._add_liquidity_2(pool, amounts_2, min_mint_amount, use_eth)

    elif len(amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(amounts), 3), bound=3):
            amounts_3[i] = amounts[i]
        return self._add_liquidity_3(pool, amounts_3, min_mint_amount, use_eth)
    else:
        raise "cryptoswap_adapter: invalid number of amounts"


@payable
@internal
def _add_liquidity_2(
    pool: address, amounts: uint256[2], min_mint_amount: uint256, use_eth: bool
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 2 coin
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            use_eth,
            method_id=method_id("add_liquidity(uint256[2],uint256,bool)"),
        ),
        value=msg.value,
        max_outsize=32,
    )
    return response


@payable
@internal
def _add_liquidity_3(
    pool: address, amounts: uint256[3], min_mint_amount: uint256, use_eth: bool
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 3 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            use_eth,
            method_id=method_id("add_liquidity(uint256[3],uint256,bool)"),
        ),
        value=msg.value,
        max_outsize=32,
    )
    return response


# ------------------------------------------------------------------
#                GET LIQUIDITY OUT AMOUNT FUNCTIONS
# ------------------------------------------------------------------

@internal
@view
def _get_lp_amount_after_deposit(
    pool: address, amounts: DynArray[uint256, MAX_COINS], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing amounts
    @param pool address of the pool contract
    @param amounts array of amounts of coins to add
    @return lp_amount amount of lp tokens after depositing amounts
    """
    if len(amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(amounts), 2), bound=2):
            amounts_2[i] = amounts[i]
        return self._get_lp_amount_after_deposit_2(pool, amounts_2)

    elif len(amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(amounts), 3), bound=3):
            amounts_3[i] = amounts[i]
        return self._get_lp_amount_after_deposit_3(pool, amounts_3, deposit)
    else:
        raise "cryptoswap_adapter: invalid number of amounts"


@internal
@view
def _get_lp_amount_after_deposit_2(
    pool: address, amounts: uint256[2]
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 2 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            method_id=method_id("calc_token_amount(uint256[2])"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


@internal
@view
def _get_lp_amount_after_deposit_3(
    pool: address, amounts: uint256[3], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 3 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[3],bool)"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


# ------------------------------------------------------------------
#               REMOVE BALANCED LIQUIDITY FUNCTIONS
# ------------------------------------------------------------------

@internal
def _remove_liquidity(
    pool: address,
    lp_amount: uint256,
    min_amounts: DynArray[uint256, MAX_COINS],
    use_eth: bool,
):
    """
    @notice Remove liquidity from a pool
    """
    if len(min_amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(min_amounts), 2), bound=2):
            amounts_2[i] = min_amounts[i]
        self._remove_balanced_liquidity_2(pool, lp_amount, amounts_2, use_eth)

    elif len(min_amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 3), bound=3):
            amounts_3[i] = min_amounts[i]
        self._remove_balanced_liquidity_3(pool, lp_amount, amounts_3, use_eth)
    else:
        raise "cryptoswap_adapter: invalid number of amounts"


@internal
def _remove_balanced_liquidity_2(
    pool: address, lp_amount: uint256, min_amounts: uint256[2], use_eth: bool
):
    """
    @notice Remove balanced liquidity from a pool with 2 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            use_eth,
            method_id=method_id("remove_liquidity(uint256,uint256[2],bool)"),
        ),
    )


@internal
def _remove_balanced_liquidity_3(
    pool: address, lp_amount: uint256, min_amounts: uint256[3], use_eth: bool
):
    """
    @notice Remove balanced liquidity from a pool with 3 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            use_eth,
            method_id=method_id("remove_liquidity(uint256,uint256[3],bool)"),
        ),
    )
