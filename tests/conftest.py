import boa
import pytest
from eth_account import Account
from eth_utils import to_wei
from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network

BALANCE = to_wei(1000, "ether")
ZERO = "0x0000000000000000000000000000000000000000"

# ------------------------------------------------------------------
#                          SESSION SCOPE
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def active_network():
    return get_active_network()

# ------------------------------------------------------------------
#                          FUNCTION SCOPE
# ------------------------------------------------------------------

@pytest.fixture(scope="function")
def meta_registry(active_network):
    return active_network.manifest_named("meta_registry")

@pytest.fixture(scope="function")
def minter(active_network):
    return active_network.manifest_named("minter")

@pytest.fixture(scope="function")
def crv(active_network):
    return active_network.manifest_named("CRV")

@pytest.fixture(scope="function")
def dai(active_network):
    return active_network.manifest_named("DAI")

@pytest.fixture(scope="function")
def usdc(active_network):
    return active_network.manifest_named("USDC")

@pytest.fixture(scope="function")
def usdt(active_network):
    return active_network.manifest_named("USDT")

@pytest.fixture(scope="function")
def musd(active_network):
    return active_network.manifest_named("MUSD")

@pytest.fixture(scope="function")
def three_crv(active_network):
    return active_network.manifest_named("THREE_CRV")

@pytest.fixture(scope="function")
def wbtc(active_network):
    return active_network.manifest_named("WBTC")

@pytest.fixture(scope="function")
def stg(active_network):
    return active_network.manifest_named("STG")

@pytest.fixture(scope="function")
def eth(active_network):
    return active_network.manifest_named("ETH")

@pytest.fixture(scope="function")
def three_pool_contract(active_network):
    return active_network.manifest_named("three_pool_contract")

@pytest.fixture(scope="function")
def three_pool_gauge(active_network):
    return active_network.manifest_named("three_pool_gauge")

@pytest.fixture(scope="function")
def three_pool_lp_token(active_network):
    return active_network.manifest_named("three_pool_lp_token")

@pytest.fixture(scope="function")
def musd_three_pool_contract(active_network):
    return active_network.manifest_named("musd_three_pool_contract")

@pytest.fixture(scope="function")
def musd_three_pool_gauge(active_network):
    return active_network.manifest_named("musd_three_pool_gauge")

@pytest.fixture(scope="function")
def musd_three_pool_lp_token(active_network):
    return active_network.manifest_named("musd_three_pool_lp_token")

@pytest.fixture(scope="function")
def musd_three_pool_zapper(active_network):
    return active_network.manifest_named("musd_three_pool_zapper")

@pytest.fixture(scope="function")
def usdc_wbtc_eth_pool_contract(active_network):
    return active_network.manifest_named("usdc_wbtc_eth_pool_contract")

@pytest.fixture(scope="function")
def usdc_wbtc_eth_pool_gauge(active_network):
    return active_network.manifest_named("usdc_wbtc_eth_pool_gauge")

@pytest.fixture(scope="function")
def usdc_wbtc_eth_pool_lp_token(active_network):
    return active_network.manifest_named("usdc_wbtc_eth_pool_lp_token")

@pytest.fixture(scope="function")
def stg_usdc_pool_contract(active_network):
    return active_network.manifest_named("stg_usdc_pool_contract")

@pytest.fixture(scope="function")
def stg_usdc_pool_gauge(active_network):
    return active_network.manifest_named("stg_usdc_pool_gauge")

@pytest.fixture(scope="function")
def stg_usdc_pool_lp_token(active_network):
    return active_network.manifest_named("stg_usdc_pool_lp_token")

@pytest.fixture(scope="function")
def alice():
    entropy = 13
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    return account.address

@pytest.fixture(scope="function")
def stableswap_adapter(active_network, alice) -> VyperContract:
    with boa.env.prank(alice):
        return active_network.manifest_named("stableswap_adapter")

@pytest.fixture(scope="function")
def cryptoswap_adapter(active_network, alice) -> VyperContract:
    with boa.env.prank(alice):
        return active_network.manifest_named("cryptoswap_adapter")