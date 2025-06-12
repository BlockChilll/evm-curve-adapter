import boa
import pytest
from eth_account import Account
from eth_utils import to_wei
from moccasin.config import get_active_network

BALANCE = to_wei(1000, "ether")
ZERO = "0x0000000000000000000000000000000000000000"

# ------------------------------------------------------------------
#                          SESSION SCOPE
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def active_network():
    return get_active_network()

@pytest.fixture(scope="session")
def meta_registry(active_network):
    return active_network.manifest_named("meta_registry")

@pytest.fixture(scope="session")
def three_pool_contract(active_network):
    return active_network.manifest_named("three_pool_contract")

@pytest.fixture(scope="session")
def three_pool_gauge(active_network):
    return active_network.manifest_named("three_pool_gauge")

@pytest.fixture(scope="session")
def three_pool_lp_token(active_network):
    return active_network.manifest_named("three_pool_lp_token")

@pytest.fixture(scope="session")
def musd_three_pool_contract(active_network):
    return active_network.manifest_named("musd_three_pool_contract")

@pytest.fixture(scope="session")
def musd_three_pool_gauge(active_network):
    return active_network.manifest_named("musd_three_pool_gauge")

@pytest.fixture(scope="session")
def musd_three_pool_lp_token(active_network):
    return active_network.manifest_named("musd_three_pool_lp_token")

@pytest.fixture(scope="session")
def musd_three_pool_zapper(active_network):
    return active_network.manifest_named("musd_three_pool_zapper")

@pytest.fixture(scope="session")
def dai(active_network):
    return active_network.manifest_named("DAI")

@pytest.fixture(scope="session")
def usdc(active_network):
    return active_network.manifest_named("USDC")

@pytest.fixture(scope="session")
def usdt(active_network):
    return active_network.manifest_named("USDT")

@pytest.fixture(scope="session")
def musd(active_network):
    return active_network.manifest_named("MUSD")

@pytest.fixture(scope="session")
def three_crv(active_network):
    return active_network.manifest_named("THREE_CRV")

@pytest.fixture(scope="session")
def alice():
    entropy = 13
    account = Account.create(entropy)
    boa.env.set_balance(account.address, BALANCE)
    return account.address

# ------------------------------------------------------------------
#                          FUNCTION SCOPE
# ------------------------------------------------------------------

@pytest.fixture(scope="function")
def stableswap_adapter(active_network, alice):
    with boa.env.prank(alice):
        return active_network.manifest_named("stableswap_adapter")
