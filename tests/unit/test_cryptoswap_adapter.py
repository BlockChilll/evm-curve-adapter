"""
Unit tests for the CryptoswapAdapter contract.
Should be run with eth-forked network only
"""

import boa
from eth_abi import encode
from eth_utils import from_wei, function_signature_to_4byte_selector, to_wei

ZERO = "0x0000000000000000000000000000000000000000"
RANDOM_ADDRESS = boa.env.generate_address("random")
BALANCE = to_wei(1000, "ether")
WBTC_BALANCE = int(1000e8)
WBTC_WHALE = "0x5Ee5bf7ae06D1Be5997A1A72006FE6C607eC6DE8"
STG_WHALE = "0x65bb797c2B9830d891D87288F029ed8dACc19705"

# ------------------------------------------------------------------
#                      REGISTER_POOL FUNCTION TESTS
# ------------------------------------------------------------------

def test_cryptoswap_adapter_deploy(cryptoswap_adapter, alice):
    assert cryptoswap_adapter.address is not None

    print(f"CryptoswapAdapter owner: {cryptoswap_adapter.owner()}")
    assert cryptoswap_adapter.owner() == alice

def test_cannot_set_pool_not_registered_in_meta_registry(cryptoswap_adapter, alice):
    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool is not registered in meta registry"):
            cryptoswap_adapter.register_pool(RANDOM_ADDRESS)

def test_cannot_set_pool_not_owner(cryptoswap_adapter):
    with boa.reverts("ownable: caller is not the owner"):
        cryptoswap_adapter.register_pool(RANDOM_ADDRESS)

def test_cannot_set_pool_with_more_than_3_coins(cryptoswap_adapter, alice):
    four_token_pool: str = "0x79a8C46DeA5aDa233ABaFFD40F3A0A2B1e5A4F27"

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool has more than 3 coins"):
            cryptoswap_adapter.register_pool(four_token_pool)

def test_cannot_set_pool_already_registered(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool already registered"):
            cryptoswap_adapter.register_pool(usdc_wbtc_eth_pool_contract)

def test_set_pool_data_successfully(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc_wbtc_eth_pool_gauge, usdc_wbtc_eth_pool_lp_token, stg_usdc_pool_contract, stg_usdc_pool_gauge, stg_usdc_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    assert cryptoswap_adapter.get_pools_count() == 1

    pool_info = cryptoswap_adapter.get_pool_info(usdc_wbtc_eth_pool_contract)
    assert pool_info.contract == usdc_wbtc_eth_pool_contract.address
    assert pool_info.gauge == usdc_wbtc_eth_pool_gauge.address
    assert pool_info.lp_token == usdc_wbtc_eth_pool_lp_token.address
    assert pool_info.n_coins == 3

    with boa.env.prank(alice):
        cryptoswap_adapter.register_pool(stg_usdc_pool_contract)
        assert cryptoswap_adapter.get_pools_count() == 2

        pool_info = cryptoswap_adapter.get_pool_info(stg_usdc_pool_contract)
        assert pool_info.contract == stg_usdc_pool_contract.address
        assert pool_info.gauge == stg_usdc_pool_gauge.address
        assert pool_info.lp_token == stg_usdc_pool_lp_token.address
        assert pool_info.n_coins == 2

def test_emits_register_log(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc_wbtc_eth_pool_gauge, usdc_wbtc_eth_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    logs = cryptoswap_adapter.get_logs()
    assert logs[0].pool == usdc_wbtc_eth_pool_contract.address
    assert logs[0].gauge == usdc_wbtc_eth_pool_gauge.address
    assert logs[0].lp_token == usdc_wbtc_eth_pool_lp_token.address
    assert logs[0].n_coins == 3

# ------------------------------------------------------------------
#                      EXCHANGE FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_exchange_with_wrong_pool_address(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool address mismatch"):
            cryptoswap_adapter.exchange(RANDOM_ADDRESS, 0, 1, AMOUNT_IN, 0, False)

def test_cannot_exchange_with_wrong_index_in(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: index in out of bounds"):
            cryptoswap_adapter.exchange(usdc_wbtc_eth_pool_contract, 3, 1, AMOUNT_IN, 0, False)

def test_cannot_exchange_with_wrong_index_out(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: index out out of bounds"):
            cryptoswap_adapter.exchange(usdc_wbtc_eth_pool_contract, 0, 3, AMOUNT_IN, 0, False)

def test_cannot_exchange_with_same_index_in_and_out(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: index in and index out cannot be the same"):
            cryptoswap_adapter.exchange(usdc_wbtc_eth_pool_contract, 0, 0, AMOUNT_IN, 0, False)

def test_can_successfully_exchange_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)
    assert usdc.balanceOf(alice) == BALANCE
    assert wbtc.balanceOf(alice) == WBTC_BALANCE

    AMOUNT_IN: int = int(1e18) # ETH

    usdc_balance_before: int = usdc.balanceOf(alice) # 0 index
    eth_balance_before: int = boa.env.get_balance(alice) # 2 index
    
    with boa.env.prank(alice):
        cryptoswap_adapter.exchange(usdc_wbtc_eth_pool_contract, 2, 0, AMOUNT_IN, 0, True, value=AMOUNT_IN)

    usdc_balance_after: int = usdc.balanceOf(alice)
    eth_balance_after: int = boa.env.get_balance(alice)

    eth_in_amount: int = eth_balance_before - eth_balance_after
    usdc_out_amount: int = usdc_balance_after - usdc_balance_before

    print(f"eth_in_amount: {eth_in_amount}")                # 1_000000000000000000
    print(f"usdc_out_amount: {usdc_out_amount}")            # 2265_528592
    print(f"eth_balance_before: {eth_balance_before}")      # 1000_000000000000000000
    print(f"eth_balance_after: {eth_balance_after}")        # 999_000000000000000000
    print(f"usdc_balance_before: {usdc_balance_before}")    # 1000000000000000_000000
    print(f"usdc_balance_after: {usdc_balance_after}")      # 1000000000002265_528592

    print(f"usdc_out_amount: {usdc_out_amount}") # 2265_528592
    assert usdc_out_amount > 0

    assert eth_in_amount == AMOUNT_IN
    assert eth_balance_after == eth_balance_before - AMOUNT_IN
    assert usdc_balance_after > usdc_balance_before

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == usdc_wbtc_eth_pool_contract.address
    assert log.index_in == 2
    assert log.index_out == 0
    assert log.amount_in == AMOUNT_IN
    assert log.min_amount_out == 0
    assert log.out_amount == usdc_out_amount

def test_can_successfully_exchange_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)
    assert usdc.balanceOf(alice) == BALANCE
    assert stg.balanceOf(alice) == BALANCE

    AMOUNT_IN: int = int(1e18)

    usdc_balance_before: int = usdc.balanceOf(alice) # 1 index
    stg_balance_before: int = stg.balanceOf(alice) # 0 index
    
    with boa.env.prank(alice):
        stg.approve(cryptoswap_adapter, AMOUNT_IN)
        cryptoswap_adapter.exchange(stg_usdc_pool_contract, 0, 1, AMOUNT_IN, 0, False)

    usdc_balance_after: int = usdc.balanceOf(alice)
    stg_balance_after: int = stg.balanceOf(alice)

    stg_in_amount: int = stg_balance_before - stg_balance_after
    usdc_out_amount: int = usdc_balance_after - usdc_balance_before

    print(f"stg_in_amount: {stg_in_amount}")                # 1_000000000000000000
    print(f"usdc_out_amount: {usdc_out_amount}")            # 0_150065
    print(f"stg_balance_before: {stg_balance_before}")      # 1000_000000000000000000
    print(f"stg_balance_after: {stg_balance_after}")        # 999_000000000000000000
    print(f"usdc_balance_before: {usdc_balance_before}")    # 1000000000000000_000000
    print(f"usdc_balance_after: {usdc_balance_after}")      # 1000000000000000_150065

    print(f"usdc_out_amount: {usdc_out_amount}") # 0_150065
    assert usdc_out_amount > 0

    assert stg_in_amount == AMOUNT_IN
    assert stg_balance_after == stg_balance_before - AMOUNT_IN
    assert usdc_balance_after > usdc_balance_before

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == stg_usdc_pool_contract.address
    assert log.index_in == 0
    assert log.index_out == 1
    assert log.amount_in == AMOUNT_IN
    assert log.min_amount_out == 0
    assert log.out_amount == usdc_out_amount


# ------------------------------------------------------------------
#              GET_EXCHANGE_AMOUNT_OUT FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_exchange_amount_out_successfully_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, eth):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_IN: int = int(1e18) # ETH

    out_amount: int = cryptoswap_adapter.get_exchange_amount_out(usdc_wbtc_eth_pool_contract, 2, 0, AMOUNT_IN)

    print(f"out_amount: {out_amount}")
    assert out_amount > 0

def test_get_exchange_amount_out_successfully_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)

    AMOUNT_IN: int = int(1e18)

    out_amount: int = cryptoswap_adapter.get_exchange_amount_out(stg_usdc_pool_contract, 0, 1, AMOUNT_IN)

    assert out_amount > 0


# ------------------------------------------------------------------
#                      ADD_LIQUIDITY FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_add_liquidity_with_wrong_coins_amount(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: invalid number of amounts"):
            cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [1, 2], 0, False)

def test_cannot_add_liquidity_with_wrong_pool_address(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool address mismatch"):
            cryptoswap_adapter.add_liquidity(RANDOM_ADDRESS, [], 0, False)

def test_can_add_liquidity_successfully_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        print(f"mint_amount in eth: {from_wei(mint_amount, 'ether')}") # 7853.1540450392375489
        print(f"mint_amount in wei: {mint_amount}") # 7853_154045039237548900

    assert boa.env.get_balance(alice) == BALANCE - AMOUNT_TO_ADD
    assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
    assert wbtc.balanceOf(alice) == WBTC_BALANCE - AMOUNT_TO_ADD_3
    assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == mint_amount


def test_can_add_liquidity_successfully_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc, stg_usdc_pool_lp_token):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # STG
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

        print(f"mint_amount in eth: {from_wei(mint_amount, 'ether')}") # 7853.1540450392375489
        print(f"mint_amount in wei: {mint_amount}") # 7853_154045039237548900

    assert stg.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
    assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
    assert stg_usdc_pool_lp_token.balanceOf(alice) == mint_amount


def test_emits_add_liquidity_log(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg_usdc_pool_gauge, stg_usdc_pool_lp_token, stg, usdc):    
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # STG
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == stg_usdc_pool_contract.address
    assert log.amounts == [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2]
    assert log.min_mint_amount == 0
    assert log.mint_amount == mint_amount


# ------------------------------------------------------------------
#            GET_LP_AMOUNT_AFTER_DEPOSIT/WITHDRAW FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_lp_amount_after_deposit_successfully(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, stg_usdc_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_TO_ADD: int = int(1e18) # ETH
    AMOUNT_TO_ADD_2: int = int(2e6) # USDC
    AMOUNT_TO_ADD_3: int = int(3e8) # WBTC
    
    lp_amount: int = cryptoswap_adapter.get_lp_amount_after_deposit(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD])
    assert lp_amount > 0

    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    lp_amount_2: int = cryptoswap_adapter.get_lp_amount_after_deposit(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2])
    assert lp_amount_2 > 0

def test_get_lp_amount_after_withdraw_successfully(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, stg_usdc_pool_contract, usdc_wbtc_eth_pool_lp_token, stg_usdc_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)

    AMOUNT_TO_ADD: int = int(1e18) # ETH
    AMOUNT_TO_ADD_2: int = int(2e6) # USDC
    AMOUNT_TO_ADD_3: int = int(3e8) # WBTC
    
    lp_amount: int = cryptoswap_adapter.get_lp_amount_after_withdraw(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD])
    assert lp_amount > 0

    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    lp_amount_2: int = cryptoswap_adapter.get_lp_amount_after_withdraw(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2])
    assert lp_amount_2 > 0


# ------------------------------------------------------------------
#                 REMOVE_LIQUIDITY FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_remove_liquidity_with_wrong_coins_amount(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: invalid number of amounts"):
            cryptoswap_adapter.remove_liquidity(usdc_wbtc_eth_pool_contract, 0, [1, 2], False)

def test_cannot_remove_liquidity_with_wrong_pool_address(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("cryptoswap_adapter: pool address mismatch"):
            cryptoswap_adapter.remove_liquidity(RANDOM_ADDRESS, 0, [], False)

def test_can_remove_liquidity_balanced_successfully_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == mint_amount
        assert boa.env.get_balance(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert wbtc.balanceOf(alice) == WBTC_BALANCE - AMOUNT_TO_ADD_3

        usdc_wbtc_eth_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        eth_balance_before: int = boa.env.get_balance(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)
        wbtc_balance_before: int = wbtc.balanceOf(alice)

        cryptoswap_adapter.remove_liquidity(usdc_wbtc_eth_pool_contract, mint_amount, [0, 0, 0], True)

        eth_balance_after: int = boa.env.get_balance(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)
        wbtc_balance_after: int = wbtc.balanceOf(alice)

        eth_withdraw_amount: int = eth_balance_after - eth_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before
        wbtc_withdraw_amount: int = wbtc_balance_after - wbtc_balance_before

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == 0
        assert boa.env.get_balance(alice) == BALANCE - AMOUNT_TO_ADD + eth_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + usdc_withdraw_amount
        assert wbtc.balanceOf(alice) == WBTC_BALANCE - AMOUNT_TO_ADD_3 + wbtc_withdraw_amount

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == usdc_wbtc_eth_pool_contract.address
    assert log.min_amounts == [0, 0, 0]
    assert log.amount == mint_amount


def test_can_remove_liquidity_balanced_successfully_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc, stg_usdc_pool_lp_token):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

        assert stg_usdc_pool_lp_token.balanceOf(alice) == mint_amount
        assert stg.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

        stg_usdc_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        stg_balance_before: int = stg.balanceOf(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)

        cryptoswap_adapter.remove_liquidity(stg_usdc_pool_contract, mint_amount, [0, 0], False)

        stg_balance_after: int = stg.balanceOf(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)

        stg_withdraw_amount: int = stg_balance_after - stg_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before

        assert stg_usdc_pool_lp_token.balanceOf(alice) == 0
        assert stg.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + stg_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + usdc_withdraw_amount

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == stg_usdc_pool_contract.address
    assert log.min_amounts == [0, 0]
    assert log.amount == mint_amount


# ------------------------------------------------------------------
#                 REMOVE_LIQUIDITY_ONE_COIN FUNCTION TESTS
# ------------------------------------------------------------------

def test_can_remove_liquidity_one_coin_successfully_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == mint_amount
        assert boa.env.get_balance(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert wbtc.balanceOf(alice) == WBTC_BALANCE - AMOUNT_TO_ADD_3

        usdc_wbtc_eth_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        eth_balance_before: int = boa.env.get_balance(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)
        wbtc_balance_before: int = wbtc.balanceOf(alice)

        cryptoswap_adapter.remove_liquidity_one_coin(usdc_wbtc_eth_pool_contract, 2, mint_amount, 0, True)

        eth_balance_after: int = boa.env.get_balance(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)
        wbtc_balance_after: int = wbtc.balanceOf(alice)

        eth_withdraw_amount: int = eth_balance_after - eth_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before
        wbtc_withdraw_amount: int = wbtc_balance_after - wbtc_balance_before

        print(f"eth_withdraw_amount: {eth_withdraw_amount}")
        assert eth_withdraw_amount > AMOUNT_TO_ADD # 2153_446618988284534479
        assert usdc_withdraw_amount == 0
        assert wbtc_withdraw_amount == 0

        print(f"lp_token balance: {usdc_wbtc_eth_pool_lp_token.balanceOf(alice)}")
        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == 0
        assert boa.env.get_balance(alice) == BALANCE - AMOUNT_TO_ADD + eth_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert wbtc.balanceOf(alice) == WBTC_BALANCE - AMOUNT_TO_ADD_3

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == usdc_wbtc_eth_pool_contract.address
    assert log.coin_index == 2
    assert log.lp_amount == mint_amount
    assert log.min_amount == 0
    assert log.out_amount == eth_withdraw_amount


def test_can_remove_liquidity_one_coin_successfully_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc, stg_usdc_pool_lp_token):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # STG
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

        assert stg_usdc_pool_lp_token.balanceOf(alice) == mint_amount
        assert stg.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

        stg_usdc_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        stg_balance_before: int = stg.balanceOf(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)

        cryptoswap_adapter.remove_liquidity_one_coin(stg_usdc_pool_contract, 0, mint_amount, 0, False)

        stg_balance_after: int = stg.balanceOf(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)

        stg_withdraw_amount: int = stg_balance_after - stg_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before

        print(f"stg_withdraw_amount: {stg_withdraw_amount}")
        assert stg_withdraw_amount > AMOUNT_TO_ADD # 1471_096290666945427765
        assert usdc_withdraw_amount == 0

        print(f"lp_token balance: {stg_usdc_pool_lp_token.balanceOf(alice)}")
        assert stg_usdc_pool_lp_token.balanceOf(alice) == 0
        assert stg.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + stg_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == stg_usdc_pool_contract.address
    assert log.coin_index == 0
    assert log.lp_amount == mint_amount
    assert log.min_amount == 0
    assert log.out_amount == stg_withdraw_amount

# ------------------------------------------------------------------
#        GET_LP_AMOUNT_AFTER_REMOVE_ONE_COIN FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_lp_amount_after_remove_one_coin_successfully_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        out_amount: int = cryptoswap_adapter.get_lp_amount_after_remove_one_coin(usdc_wbtc_eth_pool_contract, 2, mint_amount)

        assert out_amount > AMOUNT_TO_ADD

def test_get_lp_amount_after_remove_one_coin_successfully_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc, stg_usdc_pool_lp_token):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # STG
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

        out_amount: int = cryptoswap_adapter.get_lp_amount_after_remove_one_coin(stg_usdc_pool_contract, 0, mint_amount)

        assert out_amount > AMOUNT_TO_ADD


# ------------------------------------------------------------------
#                DEPOSIT_LP_FOR_CRV FUNCTION TESTS
# ------------------------------------------------------------------

def test_can_successfully_deposit_lp_for_crv_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token, usdc_wbtc_eth_pool_gauge):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == mint_amount
        print(f"usdc_wbtc_eth_pool_lp_token.balanceOf(alice): {usdc_wbtc_eth_pool_lp_token.balanceOf(alice)}")

        usdc_wbtc_eth_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        cryptoswap_adapter.deposit_lp_for_crv(usdc_wbtc_eth_pool_contract, mint_amount)

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == 0
        assert usdc_wbtc_eth_pool_gauge.balanceOf(alice) == mint_amount

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == usdc_wbtc_eth_pool_contract.address
    assert log.lp_amount == mint_amount


def test_can_successfully_deposit_lp_for_crv_twocrypto_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract, stg, usdc, stg_usdc_pool_lp_token, stg_usdc_pool_gauge):
    register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract)
    mint_stg_usdc_pool_tokens(alice, stg, usdc)

    AMOUNT_TO_ADD: int = int(100e18) # STG
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        stg.approve(cryptoswap_adapter, AMOUNT_TO_ADD)

        mint_amount: int = cryptoswap_adapter.add_liquidity(stg_usdc_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0, False)

        assert stg_usdc_pool_lp_token.balanceOf(alice) == mint_amount
        print(f"stg_usdc_pool_lp_token.balanceOf(alice): {stg_usdc_pool_lp_token.balanceOf(alice)}")

        stg_usdc_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        cryptoswap_adapter.deposit_lp_for_crv(stg_usdc_pool_contract, mint_amount)

        assert stg_usdc_pool_lp_token.balanceOf(alice) == 0
        assert stg_usdc_pool_gauge.balanceOf(alice) == mint_amount

    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == stg_usdc_pool_contract.address
    assert log.lp_amount == mint_amount


# ------------------------------------------------------------------
#                 CLAIM_CRV_REWARDS FUNCTION TESTS
# ------------------------------------------------------------------

def test_can_successfully_claim_crv_rewards_tricrypto_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract, usdc, wbtc, usdc_wbtc_eth_pool_lp_token, usdc_wbtc_eth_pool_gauge, minter, crv):
    register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract)
    mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc)

    AMOUNT_TO_ADD: int = int(100e18) # ETH
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e8) # WBTC

    with boa.env.prank(alice):
        usdc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_2)
        wbtc.approve(cryptoswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = cryptoswap_adapter.add_liquidity(usdc_wbtc_eth_pool_contract, [AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3, AMOUNT_TO_ADD], 0, True, value=AMOUNT_TO_ADD)

        assert usdc_wbtc_eth_pool_lp_token.balanceOf(alice) == mint_amount
        print(f"usdc_wbtc_eth_pool_lp_token.balanceOf(alice): {usdc_wbtc_eth_pool_lp_token.balanceOf(alice)}")

        usdc_wbtc_eth_pool_lp_token.approve(cryptoswap_adapter, mint_amount)

        cryptoswap_adapter.deposit_lp_for_crv(usdc_wbtc_eth_pool_contract, mint_amount)

        minter.toggle_approve_mint(cryptoswap_adapter)

        crv_balance_before: int = crv.balanceOf(alice)
        print(f"crv_balance_before: {crv_balance_before}")

        # boa.env.time_travel(boa.env.timestamp + 1)

        cryptoswap_adapter.claim_crv_rewards(usdc_wbtc_eth_pool_contract)

        crv_balance_after: int = crv.balanceOf(alice)
        print(f"crv_balance_after: {crv_balance_after}")


    logs = cryptoswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == usdc_wbtc_eth_pool_contract.address

# ------------------------------------------------------------------
#                      UTIL FUNCTIONS
# ------------------------------------------------------------------

def register_usdc_wbtc_eth_pool(cryptoswap_adapter, alice, usdc_wbtc_eth_pool_contract):
    with boa.env.prank(alice):
        cryptoswap_adapter.register_pool(usdc_wbtc_eth_pool_contract)

def register_stg_usdc_pool(cryptoswap_adapter, alice, stg_usdc_pool_contract):
    with boa.env.prank(alice):
        cryptoswap_adapter.register_pool(stg_usdc_pool_contract)

def mint_usdc_wbtc_eth_pool_tokens(alice, usdc, wbtc):
    # usdc
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(alice)

    with boa.env.prank(alice):
        usdc.configureMinter(alice, BALANCE)
        usdc.mint(alice, BALANCE)

    # wbtc
    with boa.env.prank(WBTC_WHALE):
        wbtc.transfer(alice, WBTC_BALANCE)

def mint_stg_usdc_pool_tokens(alice, stg, usdc):
    # usdc
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(alice)

    with boa.env.prank(alice):
        usdc.configureMinter(alice, BALANCE)
        usdc.mint(alice, BALANCE)

    # stg
    with boa.env.prank(STG_WHALE):
        stg.transfer(alice, BALANCE)