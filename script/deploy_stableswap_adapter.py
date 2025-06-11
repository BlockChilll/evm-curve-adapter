from moccasin.boa_tools import VyperContract
from moccasin.config import get_active_network

from src import stableswap_adapter


def deploy_stableswap_adapter() -> VyperContract:
    active_network = get_active_network()
    meta_registry = active_network.manifest_named("meta_registry")

    stableswap_adapter_contract = stableswap_adapter.deploy(meta_registry)

    print(f"Deployed StableswapAdapter contract at {stableswap_adapter_contract.address}")
    return stableswap_adapter_contract

def moccasin_main() -> VyperContract:
    return deploy_stableswap_adapter()

if __name__ == "__main__":
    moccasin_main()