"""Module for BNB-Chain-specific clients and errors. Since the BNB
Smart Chain is Ethereum-compatible, the client implementation inherits
from the vision.servicenode.blockchains.ethereum module.

"""
from vision.common.blockchains.enums import Blockchain

from vision.servicenode.blockchains.base import BlockchainClientError
from vision.servicenode.blockchains.ethereum import EthereumClient
from vision.servicenode.blockchains.ethereum import EthereumClientError


class BnbChainClientError(EthereumClientError):
    """Exception class for all BNB Chain client errors.

    """
    pass


class BnbChainClient(EthereumClient):
    """BNB-Chain-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.BNB_CHAIN

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return BnbChainClientError
