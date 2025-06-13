"""
Unit tests for the StableswapAdapter contract.
Should be run with eth-forked network only
"""

import boa
from eth_utils import from_wei, to_wei

BASE_TYPE = 1
META_TYPE = 2
ZERO = "0x0000000000000000000000000000000000000000"
RANDOM_ADDRESS = boa.env.generate_address("random")
BALANCE = to_wei(1000, "ether")
DAI_WHALE = "0xf6e72Db5454dd049d0788e411b06CfAF16853042"
MUSD_WHALE = "0x30647a72Dc82d7Fbb1123EA74716aB8A317Eac19"
THREE_CRV_WHALE = "0xe74b28c2eAe8679e3cCc3a94d5d0dE83CCB84705"


# ------------------------------------------------------------------
#                      REGISTER_POOL FUNCTION TESTS
# ------------------------------------------------------------------

def test_stableswap_adapter_deploy(stableswap_adapter, alice):
    assert stableswap_adapter.address is not None

    print(f"StableswapAdapter owner: {stableswap_adapter.owner()}")
    assert stableswap_adapter.owner() == alice

def test_cannot_set_pool_not_registered_in_meta_registry(stableswap_adapter, alice):
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: pool is not registered in meta registry"):
            stableswap_adapter.register_pool(RANDOM_ADDRESS, ZERO)

def test_cannot_set_pool_not_owner(stableswap_adapter):
    with boa.reverts("ownable: caller is not the owner"):
        stableswap_adapter.register_pool(RANDOM_ADDRESS, ZERO)

def test_cannot_set_pool_already_registered(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: pool already registered"):
            stableswap_adapter.register_pool(three_pool_contract, ZERO)

def test_set_pool_data_successfully(stableswap_adapter, alice, three_pool_contract, three_pool_gauge, three_pool_lp_token, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd_three_pool_zapper):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    assert stableswap_adapter.get_pools_count() == 1

    pool_info = stableswap_adapter.get_pool_info(three_pool_contract)
    assert pool_info.contract == three_pool_contract.address
    assert pool_info.pool_type == BASE_TYPE
    assert pool_info.gauge == three_pool_gauge.address
    assert pool_info.zapper == ZERO
    assert pool_info.lp_token == three_pool_lp_token.address
    assert pool_info.n_coins == 3

    with boa.env.prank(alice):
        stableswap_adapter.register_pool(musd_three_pool_contract, musd_three_pool_zapper.address)
        assert stableswap_adapter.get_pools_count() == 2

        pool_info = stableswap_adapter.get_pool_info(musd_three_pool_contract)
        assert pool_info.contract == musd_three_pool_contract.address
        assert pool_info.pool_type == META_TYPE
        assert pool_info.gauge == musd_three_pool_gauge.address
        assert pool_info.zapper == musd_three_pool_zapper.address
        assert pool_info.lp_token == musd_three_pool_lp_token.address
        assert pool_info.n_coins == 2

def test_cannot_set_zero_zap_address_for_meta_pool(stableswap_adapter, alice, musd_three_pool_contract):
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: zapper address is required for metapools"):
            stableswap_adapter.register_pool(musd_three_pool_contract, ZERO)

def test_emits_register_log(stableswap_adapter, alice, three_pool_contract, three_pool_gauge, three_pool_lp_token):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    logs = stableswap_adapter.get_logs()
    assert logs[0].pool == three_pool_contract.address
    assert logs[0].pool_type == BASE_TYPE
    assert logs[0].gauge == three_pool_gauge.address
    assert logs[0].zapper == ZERO
    assert logs[0].lp_token == three_pool_lp_token.address
    assert logs[0].n_coins == 3


# ------------------------------------------------------------------
#                      ADD_LIQUIDITY FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_add_liquidity_with_wrong_coins_amount(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: invalid number of amounts"):
            stableswap_adapter.add_liquidity(three_pool_contract, [1, 2, 3, 4], 0)

def test_cannot_add_liquidity_with_wrong_pool_address(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: pool address mismatch"):
            stableswap_adapter.add_liquidity(RANDOM_ADDRESS, [], 0)

def test_can_add_liquidity_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, three_pool_lp_token, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)
    assert usdc.balanceOf(alice) == BALANCE
    assert dai.balanceOf(alice) == BALANCE
    assert usdt.balanceOf(alice) == BALANCE

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(stableswap_adapter, AMOUNT_TO_ADD_2)
        usdt.approve(stableswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = stableswap_adapter.add_liquidity(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3], 0)

        print(f"mint_amount in eth: {from_wei(mint_amount, 'ether')}") # 577.063511051232718447
        print(f"mint_amount in wei: {mint_amount}") # 577063511051232718447

    assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
    assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
    assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3
    assert three_pool_lp_token.balanceOf(alice) == mint_amount


def test_can_add_liquidity_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)
    assert musd.balanceOf(alice) == BALANCE
    assert three_crv.balanceOf(alice) == BALANCE

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)

        print(f"mint_amount in eth: {from_wei(mint_amount, 'ether')}") # 299.151184845285355847
        print(f"mint_amount in wei: {mint_amount}") # 299151184845285355847

    assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
    assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

    assert musd_three_pool_lp_token.balanceOf(alice) == mint_amount

def test_emits_add_liquidity_log(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == musd_three_pool_contract.address
    assert log.amounts == [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2]
    assert log.min_mint_amount == 0
    assert log.mint_amount == mint_amount

# ------------------------------------------------------------------
#            GET_LP_AMOUNT_AFTER_DEPOSIT/WITHDRAW FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_lp_amount_after_deposit_successfully(stableswap_adapter, alice, three_pool_contract, musd_three_pool_contract, musd_three_pool_gauge):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT
    
    lp_amount: int = stableswap_adapter.get_lp_amount_after_deposit(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3])
    assert lp_amount > 0

    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    lp_amount_2: int = stableswap_adapter.get_lp_amount_after_deposit(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2])
    assert lp_amount_2 > 0

def test_get_lp_amount_after_withdraw_successfully(stableswap_adapter, alice, three_pool_contract, musd_three_pool_contract, musd_three_pool_gauge):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT
    
    lp_amount: int = stableswap_adapter.get_lp_amount_after_withdraw(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3])
    assert lp_amount > 0

    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    lp_amount_2: int = stableswap_adapter.get_lp_amount_after_withdraw(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2])
    assert lp_amount_2 > 0

# ------------------------------------------------------------------
#                 REMOVE_LIQUIDITY FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_remove_liquidity_with_wrong_coins_amount(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: invalid number of amounts"):
            stableswap_adapter.remove_liquidity(three_pool_contract, 0, [1, 2, 3, 4])

def test_cannot_remove_liquidity_with_wrong_pool_address(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: pool address mismatch"):
            stableswap_adapter.remove_liquidity(RANDOM_ADDRESS, 0, [])

def test_can_remove_liquidity_balanced_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, three_pool_lp_token, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(stableswap_adapter, AMOUNT_TO_ADD_2)
        usdt.approve(stableswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = stableswap_adapter.add_liquidity(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3], 0)

        assert three_pool_lp_token.balanceOf(alice) == mint_amount
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3

        three_pool_lp_token.approve(stableswap_adapter, mint_amount)

        dai_balance_before: int = dai.balanceOf(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)
        usdt_balance_before: int = usdt.balanceOf(alice)

        stableswap_adapter.remove_liquidity(three_pool_contract, mint_amount, [0, 0, 0])

        dai_balance_after: int = dai.balanceOf(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)
        usdt_balance_after: int = usdt.balanceOf(alice)

        dai_withdraw_amount: int = dai_balance_after - dai_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before
        usdt_withdraw_amount: int = usdt_balance_after - usdt_balance_before

        assert three_pool_lp_token.balanceOf(alice) == 0
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + dai_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + usdc_withdraw_amount
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3 + usdt_withdraw_amount

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == three_pool_contract.address
    assert log.min_amounts == [0, 0, 0]
    assert log.amount == mint_amount

def test_can_remove_liquidity_balanced_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)

        assert musd_three_pool_lp_token.balanceOf(alice) == mint_amount
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

        musd_three_pool_lp_token.approve(stableswap_adapter, mint_amount)

        musd_balance_before: int = musd.balanceOf(alice)
        three_crv_balance_before: int = three_crv.balanceOf(alice)

        stableswap_adapter.remove_liquidity(musd_three_pool_contract, mint_amount, [0, 0])

        musd_balance_after: int = musd.balanceOf(alice)
        three_crv_balance_after: int = three_crv.balanceOf(alice)

        musd_withdraw_amount: int = musd_balance_after - musd_balance_before
        three_crv_withdraw_amount: int = three_crv_balance_after - three_crv_balance_before

        assert musd_three_pool_lp_token.balanceOf(alice) == 0
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + musd_withdraw_amount
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + three_crv_withdraw_amount

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == musd_three_pool_contract.address
    assert log.min_amounts == [0, 0]
    assert log.amount == mint_amount

# ------------------------------------------------------------------
#                 REMOVE_LIQUIDITY_IMBALANCE FUNCTION TESTS
# ------------------------------------------------------------------

def test_can_remove_liquidity_imbalanced_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, three_pool_lp_token, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(stableswap_adapter, AMOUNT_TO_ADD_2)
        usdt.approve(stableswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = stableswap_adapter.add_liquidity(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3], 0)

        assert three_pool_lp_token.balanceOf(alice) == mint_amount
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3

        three_pool_lp_token.approve(stableswap_adapter, mint_amount)

        dai_balance_before: int = dai.balanceOf(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)
        usdt_balance_before: int = usdt.balanceOf(alice)

        stableswap_adapter.remove_liquidity_imbalance(three_pool_contract, [AMOUNT_TO_ADD//int(2), AMOUNT_TO_ADD_2//int(2), AMOUNT_TO_ADD_3//int(2)], mint_amount)

        dai_balance_after: int = dai.balanceOf(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)
        usdt_balance_after: int = usdt.balanceOf(alice)

        dai_withdraw_amount: int = dai_balance_after - dai_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before
        usdt_withdraw_amount: int = usdt_balance_after - usdt_balance_before

        assert dai_withdraw_amount == AMOUNT_TO_ADD//int(2)
        assert usdc_withdraw_amount == AMOUNT_TO_ADD_2//int(2)
        assert usdt_withdraw_amount == AMOUNT_TO_ADD_3//int(2)

        print(f"lp_token balance: {three_pool_lp_token.balanceOf(alice)}")
        assert three_pool_lp_token.balanceOf(alice) < mint_amount
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + dai_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + usdc_withdraw_amount
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3 + usdt_withdraw_amount

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == three_pool_contract.address
    assert log.amounts == [AMOUNT_TO_ADD//int(2), AMOUNT_TO_ADD_2//int(2), AMOUNT_TO_ADD_3//int(2)]
    assert log.burn_amount == mint_amount - three_pool_lp_token.balanceOf(alice)

def test_can_remove_liquidity_imbalanced_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)  

        assert musd_three_pool_lp_token.balanceOf(alice) == mint_amount
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

        musd_three_pool_lp_token.approve(stableswap_adapter, mint_amount)

        musd_balance_before: int = musd.balanceOf(alice)
        three_crv_balance_before: int = three_crv.balanceOf(alice)

        stableswap_adapter.remove_liquidity_imbalance(musd_three_pool_contract, [AMOUNT_TO_ADD//int(2), AMOUNT_TO_ADD_2//int(2)], mint_amount)

        musd_balance_after: int = musd.balanceOf(alice)
        three_crv_balance_after: int = three_crv.balanceOf(alice)

        musd_withdraw_amount: int = musd_balance_after - musd_balance_before
        three_crv_withdraw_amount: int = three_crv_balance_after - three_crv_balance_before

        assert musd_withdraw_amount == AMOUNT_TO_ADD//int(2)
        assert three_crv_withdraw_amount == AMOUNT_TO_ADD_2//int(2)

        print(f"lp_token balance: {musd_three_pool_lp_token.balanceOf(alice)}")
        assert musd_three_pool_lp_token.balanceOf(alice) < mint_amount
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + musd_withdraw_amount
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2 + three_crv_withdraw_amount

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == musd_three_pool_contract.address
    assert log.amounts == [AMOUNT_TO_ADD//int(2), AMOUNT_TO_ADD_2//int(2)]
    assert log.burn_amount == mint_amount - musd_three_pool_lp_token.balanceOf(alice)

# ------------------------------------------------------------------
#                 REMOVE_LIQUIDITY_ONE_COIN FUNCTION TESTS
# ------------------------------------------------------------------

def test_can_remove_liquidity_one_coin_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, three_pool_lp_token, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(stableswap_adapter, AMOUNT_TO_ADD_2)
        usdt.approve(stableswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = stableswap_adapter.add_liquidity(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3], 0)

        assert three_pool_lp_token.balanceOf(alice) == mint_amount
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3

        three_pool_lp_token.approve(stableswap_adapter, mint_amount)

        dai_balance_before: int = dai.balanceOf(alice)
        usdc_balance_before: int = usdc.balanceOf(alice)
        usdt_balance_before: int = usdt.balanceOf(alice)

        stableswap_adapter.remove_liquidity_one_coin(three_pool_contract, 0, mint_amount, 0)

        dai_balance_after: int = dai.balanceOf(alice)
        usdc_balance_after: int = usdc.balanceOf(alice)
        usdt_balance_after: int = usdt.balanceOf(alice)

        dai_withdraw_amount: int = dai_balance_after - dai_balance_before
        usdc_withdraw_amount: int = usdc_balance_after - usdc_balance_before
        usdt_withdraw_amount: int = usdt_balance_after - usdt_balance_before

        print(f"dai_withdraw_amount: {dai_withdraw_amount}")
        assert dai_withdraw_amount > AMOUNT_TO_ADD # 600143313752894079944
        assert usdc_withdraw_amount == 0
        assert usdt_withdraw_amount == 0

        print(f"lp_token balance: {three_pool_lp_token.balanceOf(alice)}")
        assert three_pool_lp_token.balanceOf(alice) == 0
        assert dai.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + dai_withdraw_amount
        assert usdc.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2
        assert usdt.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_3

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]
    
    assert log.pool == three_pool_contract.address
    assert log.coin_index == 0
    assert log.lp_amount == mint_amount
    assert log.min_amount == 0
    assert log.out_amount == dai_withdraw_amount

def test_can_remove_liquidity_one_coin_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)
        
        assert musd_three_pool_lp_token.balanceOf(alice) == mint_amount
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

        musd_three_pool_lp_token.approve(stableswap_adapter, mint_amount)
        
        musd_balance_before: int = musd.balanceOf(alice)
        three_crv_balance_before: int = three_crv.balanceOf(alice)

        stableswap_adapter.remove_liquidity_one_coin(musd_three_pool_contract, 0, mint_amount, 0)

        musd_balance_after: int = musd.balanceOf(alice)
        three_crv_balance_after: int = three_crv.balanceOf(alice)   

        musd_withdraw_amount: int = musd_balance_after - musd_balance_before
        three_crv_withdraw_amount: int = three_crv_balance_after - three_crv_balance_before

        assert musd_withdraw_amount > AMOUNT_TO_ADD
        assert three_crv_withdraw_amount == 0

        print(f"lp_token balance: {musd_three_pool_lp_token.balanceOf(alice)}")
        assert musd_three_pool_lp_token.balanceOf(alice) == 0
        assert musd.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD + musd_withdraw_amount
        assert three_crv.balanceOf(alice) == BALANCE - AMOUNT_TO_ADD_2

    logs = stableswap_adapter.get_logs()    
    log = logs[len(logs) - 1]
    
    assert log.pool == musd_three_pool_contract.address
    assert log.coin_index == 0
    assert log.lp_amount == mint_amount
    assert log.min_amount == 0
    assert log.out_amount == musd_withdraw_amount

# ------------------------------------------------------------------
#        GET_LP_AMOUNT_AFTER_REMOVE_ONE_COIN FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_lp_amount_after_remove_one_coin_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)

    AMOUNT_TO_ADD: int = int(100e18) # DAI
    AMOUNT_TO_ADD_2: int = int(200e6) # USDC
    AMOUNT_TO_ADD_3: int = int(300e6) # USDT

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_TO_ADD)
        usdc.approve(stableswap_adapter, AMOUNT_TO_ADD_2)
        usdt.approve(stableswap_adapter, AMOUNT_TO_ADD_3)

        mint_amount: int = stableswap_adapter.add_liquidity(three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2, AMOUNT_TO_ADD_3], 0)

        out_amount: int = stableswap_adapter.get_lp_amount_after_remove_one_coin(three_pool_contract, 0, mint_amount)

        assert out_amount > AMOUNT_TO_ADD

def test_get_lp_amount_after_remove_one_coin_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_TO_ADD: int = int(100e18) # MUSD
    AMOUNT_TO_ADD_2: int = int(200e18) # THREE_CRV

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_TO_ADD)
        three_crv.approve(stableswap_adapter, AMOUNT_TO_ADD_2)

        mint_amount: int = stableswap_adapter.add_liquidity(musd_three_pool_contract, [AMOUNT_TO_ADD, AMOUNT_TO_ADD_2], 0)

        out_amount: int = stableswap_adapter.get_lp_amount_after_remove_one_coin(musd_three_pool_contract, 0, mint_amount)

        assert out_amount > AMOUNT_TO_ADD

# ------------------------------------------------------------------
#                      EXCHANGE FUNCTION TESTS
# ------------------------------------------------------------------

def test_cannot_exchange_with_wrong_pool_address(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: pool address mismatch"):
            stableswap_adapter.exchange(RANDOM_ADDRESS, 0, 1, AMOUNT_IN, 0)

def test_cannot_exchange_with_wrong_index_in(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: index in out of bounds"):
            stableswap_adapter.exchange(three_pool_contract, 3, 1, AMOUNT_IN, 0)

def test_cannot_exchange_with_wrong_index_out(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: index out out of bounds"):
            stableswap_adapter.exchange(three_pool_contract, 0, 3, AMOUNT_IN, 0)

def test_cannot_exchange_with_same_index_in_and_out(stableswap_adapter, alice, three_pool_contract):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_IN: int = int(100e18)

    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: index in and index out cannot be the same"):
            stableswap_adapter.exchange(three_pool_contract, 0, 0, AMOUNT_IN, 0)

def test_can_successfully_exchange_base_pool(stableswap_adapter, alice, three_pool_contract, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)
    mint_three_pool_tokens(alice, dai, usdc, usdt)
    
    AMOUNT_IN: int = int(10e18) # DAI

    dai_balance_before: int = dai.balanceOf(alice) # 0 index
    usdc_balance_before: int = usdc.balanceOf(alice) # 1 index

    with boa.env.prank(alice):
        dai.approve(stableswap_adapter, AMOUNT_IN)
        stableswap_adapter.exchange(three_pool_contract, 0, 1, AMOUNT_IN, 0)

    dai_balance_after: int = dai.balanceOf(alice)
    usdc_balance_after: int = usdc.balanceOf(alice)

    dai_in_amount: int = dai_balance_before - dai_balance_after
    usdc_out_amount: int = usdc_balance_after - usdc_balance_before

    print(f"usdc_out_amount: {usdc_out_amount}") # 9999304
    assert usdc_out_amount > 0

    assert dai_in_amount == AMOUNT_IN
    assert dai_balance_after == dai_balance_before - AMOUNT_IN
    assert usdc_balance_after > usdc_balance_before

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == three_pool_contract.address
    assert log.index_in == 0
    assert log.index_out == 1
    assert log.amount_in == AMOUNT_IN
    assert log.min_amount_out == 0
    assert log.out_amount == usdc_out_amount

def test_can_successfully_exchange_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)
    mint_musd_three_pool_tokens(alice, musd, three_crv)

    AMOUNT_IN: int = int(10e18) # MUSD

    musd_balance_before: int = musd.balanceOf(alice) # 0 index
    three_crv_balance_before: int = three_crv.balanceOf(alice) # 1 index

    with boa.env.prank(alice):
        musd.approve(stableswap_adapter, AMOUNT_IN)
        stableswap_adapter.exchange(musd_three_pool_contract, 0, 1, AMOUNT_IN, 0)

    musd_balance_after: int = musd.balanceOf(alice)
    three_crv_balance_after: int = three_crv.balanceOf(alice)

    musd_in_amount: int = musd_balance_before - musd_balance_after
    three_crv_out_amount: int = three_crv_balance_after - three_crv_balance_before

    print(f"three_crv_out_amount: {three_crv_out_amount}") 
    assert three_crv_out_amount > 0

    assert musd_in_amount == AMOUNT_IN
    assert musd_balance_after == musd_balance_before - AMOUNT_IN
    assert three_crv_balance_after > three_crv_balance_before

    logs = stableswap_adapter.get_logs()
    log = logs[len(logs) - 1]

    assert log.pool == musd_three_pool_contract.address
    assert log.index_in == 0
    assert log.index_out == 1
    assert log.amount_in == AMOUNT_IN
    assert log.min_amount_out == 0
    assert log.out_amount == three_crv_out_amount

# ------------------------------------------------------------------
#              GET_EXCHANGE_AMOUNT_OUT FUNCTION TESTS
# ------------------------------------------------------------------

def test_get_exchange_amount_out_successfully_base_pool(stableswap_adapter, alice, three_pool_contract, dai, usdc, usdt):
    register_three_pool(stableswap_adapter, alice, three_pool_contract)

    AMOUNT_IN: int = int(10e18) # DAI

    out_amount: int = stableswap_adapter.get_exchange_amount_out(three_pool_contract, 0, 1, AMOUNT_IN)

    print(f"out_amount: {out_amount}") # 9999304
    assert out_amount > 0

def test_get_exchange_amount_out_successfully_meta_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd, three_crv):
    register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge)

    AMOUNT_IN: int = int(10e18) # MUSD

    out_amount: int = stableswap_adapter.get_exchange_amount_out(musd_three_pool_contract, 0, 1, AMOUNT_IN)

    assert out_amount > 0

    
# ------------------------------------------------------------------
#                      UTIL FUNCTIONS
# ------------------------------------------------------------------

def register_three_pool(stableswap_adapter, alice, three_pool_contract):
    with boa.env.prank(alice):
        stableswap_adapter.register_pool(three_pool_contract, ZERO)

def mint_three_pool_tokens(alice, dai, usdc, usdt):
    # usdc
    with boa.env.prank(usdc.owner()):
        usdc.updateMasterMinter(alice)

    with boa.env.prank(alice):
        usdc.configureMinter(alice, BALANCE)
        usdc.mint(alice, BALANCE)

    # dai
    with boa.env.prank(DAI_WHALE):
        dai.transfer(alice, BALANCE)

    # usdt
    with boa.env.prank(usdt.owner()):
        usdt.transferOwnership(alice)
        
    with boa.env.prank(alice):
        usdt.issue(BALANCE)

def register_musd_three_pool(stableswap_adapter, alice, musd_three_pool_contract, musd_three_pool_gauge):
    with boa.env.prank(alice):
        stableswap_adapter.register_pool(musd_three_pool_contract, musd_three_pool_gauge)

def mint_musd_three_pool_tokens(alice, musd, three_crv):
    # musd
    with boa.env.prank(MUSD_WHALE):
        musd.transfer(alice, BALANCE)

    # three_crv
    with boa.env.prank(THREE_CRV_WHALE):
        three_crv.transfer(alice, BALANCE)