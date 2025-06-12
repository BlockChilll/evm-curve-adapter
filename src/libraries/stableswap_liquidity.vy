# pragma version 0.4.1
# @license MIT

"""
@notice Library for adding liquidity to stableswap pools
@author denissosnowsky
@dev This library is used to add liquidity to stableswap pools
Vyper cannot convert dynamic arrays to fixed size arrays, so we need to use a fixed size array for pool's add_liquidity function
For this, we create a separate function for each number of coins in a pool
@dev This library is used in stableswap_adapter.vy
"""

# max number of coins in a pool
MAX_COINS: constant(uint256) = 8

@internal
def _add_liquidity(pool: address, amounts: DynArray[uint256, MAX_COINS], min_mint_amount: uint256) -> Bytes[32]:
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
def _add_liquidity_2(pool: address, amounts: uint256[2], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 2 coin
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[2],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_3(pool: address, amounts: uint256[3], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 3 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[3],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_4(pool: address, amounts: uint256[4], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 4 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[4],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_5(pool: address, amounts: uint256[5], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 5 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[5],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_6(pool: address, amounts: uint256[6], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 6 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[6],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_7(pool: address, amounts: uint256[7], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 7 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[7],uint256)")),
        max_outsize=32,
    )
    return response

@internal
def _add_liquidity_8(pool: address, amounts: uint256[8], min_mint_amount: uint256) -> Bytes[32]:
    """
    @notice Add liquidity to a pool with 8 coins
    """
    response: Bytes[32] = raw_call(
        pool,
        abi_encode(amounts, min_mint_amount, method_id=method_id("add_liquidity(uint256[8],uint256)")),
        max_outsize=32,
    )
    return response

