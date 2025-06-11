"""
Unit tests for the StableswapAdapter contract.
Should be run with eth-forked network only
"""

import boa
import pytest
from eth.codecs.abi.exceptions import EncodeError

BASE_TYPE = 1
META_TYPE = 2
ZERO = "0x0000000000000000000000000000000000000000"
RANDOM_ADDRESS = boa.env.generate_address("random")

# register_pool function

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
    with boa.env.prank(alice):
        stableswap_adapter.register_pool(three_pool_contract, ZERO)
        with boa.reverts("stableswap_adapter: pool already registered"):
            stableswap_adapter.register_pool(three_pool_contract, ZERO)

def test_set_pool_data_successfully(stableswap_adapter, alice, three_pool_contract, three_pool_gauge, three_pool_lp_token, musd_three_pool_contract, musd_three_pool_gauge, musd_three_pool_lp_token, musd_three_pool_zapper):
    with boa.env.prank(alice):
        stableswap_adapter.register_pool(three_pool_contract, ZERO)
        assert stableswap_adapter.get_pools_count() == 1

        pool_info = stableswap_adapter.get_pool_info(three_pool_contract)
        assert pool_info.contract == three_pool_contract.address
        assert pool_info.pool_type == BASE_TYPE
        assert pool_info.gauge == three_pool_gauge.address
        assert pool_info.zapper == ZERO
        assert pool_info.lp_token == three_pool_lp_token.address

        stableswap_adapter.register_pool(musd_three_pool_contract, musd_three_pool_zapper.address)
        assert stableswap_adapter.get_pools_count() == 2

        pool_info = stableswap_adapter.get_pool_info(musd_three_pool_contract)
        assert pool_info.contract == musd_three_pool_contract.address
        assert pool_info.pool_type == META_TYPE
        assert pool_info.gauge == musd_three_pool_gauge.address
        assert pool_info.zapper == musd_three_pool_zapper.address
        assert pool_info.lp_token == musd_three_pool_lp_token.address

def test_cannot_set_zero_zap_address_for_meta_pool(stableswap_adapter, alice, musd_three_pool_contract):
    with boa.env.prank(alice):
        with boa.reverts("stableswap_adapter: zapper address is required for metapools"):
            stableswap_adapter.register_pool(musd_three_pool_contract, ZERO)

def test_emits_register_log(stableswap_adapter, alice, three_pool_contract, three_pool_gauge, three_pool_lp_token):
    with boa.env.prank(alice):
        stableswap_adapter.register_pool(three_pool_contract, ZERO)

        logs = stableswap_adapter.get_logs()
        assert logs[0].pool == three_pool_contract.address
        assert logs[0].pool_type == BASE_TYPE
        assert logs[0].gauge == three_pool_gauge.address
        assert logs[0].zapper == ZERO
        assert logs[0].lp_token == three_pool_lp_token.address
