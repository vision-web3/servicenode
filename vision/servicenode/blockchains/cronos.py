"""Module for Cronos-specific clients and errors. Since Cronos is
Ethereum-compatible, the client implementation inherits from the
vision.servicenode.blockchains.ethereum module.

"""
from vision.common.blockchains.enums import Blockchain

from vision.servicenode.blockchains.base import BlockchainClientError
from vision.servicenode.blockchains.ethereum import EthereumClient
from vision.servicenode.blockchains.ethereum import EthereumClientError


class CronosClientError(EthereumClientError):
    """Exception class for all Cronos client errors.

    """
    pass


class CronosClient(EthereumClient):
    """Cronos-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.CRONOS

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return CronosClientError
