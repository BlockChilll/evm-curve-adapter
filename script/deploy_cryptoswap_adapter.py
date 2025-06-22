from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network

from src import cryptoswap_adapter


def deploy_cryptoswap_adapter() -> VyperContract:
    active_network = get_active_network()
    meta_registry = active_network.manifest_named("meta_registry")
    minter = active_network.manifest_named("minter")
    weth20 = active_network.manifest_named("ETH")

    cryptoswap_adapter_contract = cryptoswap_adapter.deploy(meta_registry, minter, weth20)

    print(f"Deployed CryptoswapAdapter contract at {cryptoswap_adapter_contract.address}")
    return cryptoswap_adapter_contract

def moccasin_main() -> VyperContract:
    return deploy_cryptoswap_adapter()

if __name__ == "__main__":
    moccasin_main()