# pragma version 0.4.1
# @license MIT

"""
@notice Library for liquidity management to stableswap pools
@author denissosnowsky
@dev This library is used to add, remove and get liquidity from stableswap pools
Vyper cannot convert dynamic arrays to fixed size arrays, so we need to use a fixed size array for pool's liquidity functions
For this, we create a separate function for each number of coins in a pool
@dev This library is used in stableswap_adapter.vy
"""

# max number of coins in a pool
MAX_COINS: constant(uint256) = 8


# ------------------------------------------------------------------
#                          ADD LIQUIDITY FUNCTIONS
# ------------------------------------------------------------------

@internal
def _add_liquidity(
    pool: address,
    amounts: DynArray[uint256, MAX_COINS],
    min_mint_amount: uint256,
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool
    @param pool address of the pool contract
    @param amounts array of amounts of coins to add
    @param min_mint_amount minimum amount of lp tokens to mint
    """
    if len(amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(amounts), 2), bound=2):
            amounts_2[i] = amounts[i]
        return self._add_liquidity_2(pool, amounts_2, min_mint_amount)

    elif len(amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(amounts), 3), bound=3):
            amounts_3[i] = amounts[i]
        return self._add_liquidity_3(pool, amounts_3, min_mint_amount)

    elif len(amounts) == 4:
        amounts_4: uint256[4] = [0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 4), bound=4):
            amounts_4[i] = amounts[i]
        return self._add_liquidity_4(pool, amounts_4, min_mint_amount)

    elif len(amounts) == 5:
        amounts_5: uint256[5] = [0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 5), bound=5):
            amounts_5[i] = amounts[i]
        return self._add_liquidity_5(pool, amounts_5, min_mint_amount)

    elif len(amounts) == 6:
        amounts_6: uint256[6] = [0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 6), bound=6):
            amounts_6[i] = amounts[i]
        return self._add_liquidity_6(pool, amounts_6, min_mint_amount)

    elif len(amounts) == 7:
        amounts_7: uint256[7] = [0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 7), bound=7):
            amounts_7[i] = amounts[i]
        return self._add_liquidity_7(pool, amounts_7, min_mint_amount)

    elif len(amounts) == 8:
        amounts_8: uint256[8] = [0, 0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 8), bound=8):
            amounts_8[i] = amounts[i]
        return self._add_liquidity_8(pool, amounts_8, min_mint_amount)
    else:
        raise "stableswap_adapter: invalid number of amounts"


@internal
def _add_liquidity_2(
    pool: address, amounts: uint256[2], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 2 coin
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[2],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_3(
    pool: address, amounts: uint256[3], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 3 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[3],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_4(
    pool: address, amounts: uint256[4], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 4 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[4],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_5(
    pool: address, amounts: uint256[5], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 5 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[5],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_6(
    pool: address, amounts: uint256[6], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 6 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[6],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_7(
    pool: address, amounts: uint256[7], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 7 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[7],uint256)"),
        ),
        max_outsize=32,
    )
    return response


@internal
def _add_liquidity_8(
    pool: address, amounts: uint256[8], min_mint_amount: uint256
) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 8 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            min_mint_amount,
            method_id=method_id("add_liquidity(uint256[8],uint256)"),
        ),
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
        return self._get_lp_amount_after_deposit_2(pool, amounts_2, deposit)

    elif len(amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(amounts), 3), bound=3):
            amounts_3[i] = amounts[i]
        return self._get_lp_amount_after_deposit_3(pool, amounts_3, deposit)

    elif len(amounts) == 4:
        amounts_4: uint256[4] = [0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 4), bound=4):
            amounts_4[i] = amounts[i]
        return self._get_lp_amount_after_deposit_4(pool, amounts_4, deposit)

    elif len(amounts) == 5:
        amounts_5: uint256[5] = [0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 5), bound=5):
            amounts_5[i] = amounts[i]
        return self._get_lp_amount_after_deposit_5(pool, amounts_5, deposit)

    elif len(amounts) == 6:
        amounts_6: uint256[6] = [0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 6), bound=6):
            amounts_6[i] = amounts[i]
        return self._get_lp_amount_after_deposit_6(pool, amounts_6, deposit)

    elif len(amounts) == 7:
        amounts_7: uint256[7] = [0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 7), bound=7):
            amounts_7[i] = amounts[i]
        return self._get_lp_amount_after_deposit_7(pool, amounts_7, deposit)

    elif len(amounts) == 8:
        amounts_8: uint256[8] = [0, 0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 8), bound=8):
            amounts_8[i] = amounts[i]
        return self._get_lp_amount_after_deposit_8(pool, amounts_8, deposit)

    else:
        raise "stableswap_adapter: invalid number of amounts"


@internal
@view
def _get_lp_amount_after_deposit_2(
    pool: address, amounts: uint256[2], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 2 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[2],bool)"),
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


@internal
@view
def _get_lp_amount_after_deposit_4(
    pool: address, amounts: uint256[4], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 4 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[4],bool)"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


@internal
@view
def _get_lp_amount_after_deposit_5(
    pool: address, amounts: uint256[5], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 5 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[5],bool)"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


@internal
@view
def _get_lp_amount_after_deposit_6(
    pool: address, amounts: uint256[6], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 6 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[6],bool)"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


@internal
@view
def _get_lp_amount_after_deposit_7(
    pool: address, amounts: uint256[7], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 7 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[7],bool)"),
        ),
        max_outsize=32,
        is_static_call=True,
    )
    return convert(response, uint256)


@internal
@view
def _get_lp_amount_after_deposit_8(
    pool: address, amounts: uint256[8], deposit: bool
) -> uint256:
    """
    @notice Get the amount of lp tokens after depositing 8 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(
            amounts,
            deposit,
            method_id=method_id("calc_token_amount(uint256[8],bool)"),
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
    pool: address, lp_amount: uint256, min_amounts: DynArray[uint256, MAX_COINS]
):
    """
    @notice Remove liquidity from a pool
    """
    if len(min_amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(min_amounts), 2), bound=2):
            amounts_2[i] = min_amounts[i]
        self._remove_balanced_liquidity_2(pool, lp_amount, amounts_2)

    elif len(min_amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 3), bound=3):
            amounts_3[i] = min_amounts[i]
        self._remove_balanced_liquidity_3(pool, lp_amount, amounts_3)

    elif len(min_amounts) == 4:
        amounts_4: uint256[4] = [0, 0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 4), bound=4):
            amounts_4[i] = min_amounts[i]
        self._remove_balanced_liquidity_4(pool, lp_amount, amounts_4)

    elif len(min_amounts) == 5:
        amounts_5: uint256[5] = [0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 5), bound=5):
            amounts_5[i] = min_amounts[i]
        self._remove_balanced_liquidity_5(pool, lp_amount, amounts_5)

    elif len(min_amounts) == 6:
        amounts_6: uint256[6] = [0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 6), bound=6):
            amounts_6[i] = min_amounts[i]
        self._remove_balanced_liquidity_6(pool, lp_amount, amounts_6)

    elif len(min_amounts) == 7:
        amounts_7: uint256[7] = [0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 7), bound=7):
            amounts_7[i] = min_amounts[i]
        self._remove_balanced_liquidity_7(pool, lp_amount, amounts_7)

    elif len(min_amounts) == 8:
        amounts_8: uint256[8] = [0, 0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(min_amounts), 8), bound=8):
            amounts_8[i] = min_amounts[i]
        self._remove_balanced_liquidity_8(pool, lp_amount, amounts_8)
    else:
        raise "stableswap_adapter: invalid number of amounts"


@internal
def _remove_balanced_liquidity_2(
    pool: address, lp_amount: uint256, min_amounts: uint256[2]
):
    """
    @notice Remove balanced liquidity from a pool with 2 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[2])"),
        ),
    )


@internal
def _remove_balanced_liquidity_3(
    pool: address, lp_amount: uint256, min_amounts: uint256[3]
):
    """
    @notice Remove balanced liquidity from a pool with 3 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[3])"),
        ),
    )


@internal
def _remove_balanced_liquidity_4(
    pool: address, lp_amount: uint256, min_amounts: uint256[4]
):
    """
    @notice Remove balanced liquidity from a pool with 4 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[4])"),
        ),
    )


@internal
def _remove_balanced_liquidity_5(
    pool: address, lp_amount: uint256, min_amounts: uint256[5]
):
    """
    @notice Remove balanced liquidity from a pool with 5 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[5])"),
        ),
    )


@internal
def _remove_balanced_liquidity_6(
    pool: address, lp_amount: uint256, min_amounts: uint256[6]
):
    """
    @notice Remove balanced liquidity from a pool with 6 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[6])"),
        ),
    )


@internal
def _remove_balanced_liquidity_7(
    pool: address, lp_amount: uint256, min_amounts: uint256[7]
):
    """
    @notice Remove balanced liquidity from a pool with 7 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[7])"),
        ),
    )


@internal
def _remove_balanced_liquidity_8(
    pool: address, lp_amount: uint256, min_amounts: uint256[8]
):
    """
    @notice Remove balanced liquidity from a pool with 8 coins
    """
    raw_call(
        pool,
        abi_encode(
            lp_amount,
            min_amounts,
            method_id=method_id("remove_liquidity(uint256,uint256[8])"),
        ),
    )


# ------------------------------------------------------------------
#              REMOVE IMBALANCED LIQUIDITY FUNCTIONS
# ------------------------------------------------------------------

@internal
def _remove_imbalanced_liquidity(
    pool: address,
    amounts: DynArray[uint256, MAX_COINS],
    max_burn_amount: uint256,
):
    """
    @notice Remove imbalanced liquidity from a pool
    """
    if len(amounts) == 2:
        amounts_2: uint256[2] = [0, 0]
        for i: uint256 in range(min(len(amounts), 2), bound=2):
            amounts_2[i] = amounts[i]
        self._remove_imbalanced_liquidity_2(pool, amounts_2, max_burn_amount)

    elif len(amounts) == 3:
        amounts_3: uint256[3] = [0, 0, 0]
        for i: uint256 in range(min(len(amounts), 3), bound=3):
            amounts_3[i] = amounts[i]
        self._remove_imbalanced_liquidity_3(pool, amounts_3, max_burn_amount)

    elif len(amounts) == 4:
        amounts_4: uint256[4] = [0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 4), bound=4):
            amounts_4[i] = amounts[i]
        self._remove_imbalanced_liquidity_4(pool, amounts_4, max_burn_amount)

    elif len(amounts) == 5:
        amounts_5: uint256[5] = [0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 5), bound=5):
            amounts_5[i] = amounts[i]
        self._remove_imbalanced_liquidity_5(pool, amounts_5, max_burn_amount)

    elif len(amounts) == 6:
        amounts_6: uint256[6] = [0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 6), bound=6):
            amounts_6[i] = amounts[i]
        self._remove_imbalanced_liquidity_6(pool, amounts_6, max_burn_amount)

    elif len(amounts) == 7:
        amounts_7: uint256[7] = [0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 7), bound=7):
            amounts_7[i] = amounts[i]
        self._remove_imbalanced_liquidity_7(pool, amounts_7, max_burn_amount)

    elif len(amounts) == 8:
        amounts_8: uint256[8] = [0, 0, 0, 0, 0, 0, 0, 0]
        for i: uint256 in range(min(len(amounts), 8), bound=8):
            amounts_8[i] = amounts[i]
        self._remove_imbalanced_liquidity_8(pool, amounts_8, max_burn_amount)


@internal
def _remove_imbalanced_liquidity_2(
    pool: address, amounts: uint256[2], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 2 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[2],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_3(
    pool: address, amounts: uint256[3], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 3 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[3],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_4(
    pool: address, amounts: uint256[4], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 4 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[4],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_5(
    pool: address, amounts: uint256[5], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 5 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[5],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_6(
    pool: address, amounts: uint256[6], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 6 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[6],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_7(
    pool: address, amounts: uint256[7], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 7 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[7],uint256)"
            ),
        ),
    )


@internal
def _remove_imbalanced_liquidity_8(
    pool: address, amounts: uint256[8], max_burn_amount: uint256
):
    """
    @notice Remove imbalanced liquidity from a pool with 8 coins
    """
    raw_call(
        pool,
        abi_encode(
            amounts,
            max_burn_amount,
            method_id=method_id(
                "remove_liquidity_imbalance(uint256[8],uint256)"
            ),
        ),
    )
