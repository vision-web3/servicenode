"""Module for Celo-specific clients and errors. Since Celo is
Ethereum-compatible, the client implementation inherits from the
vision.servicenode.blockchains.ethereum module.

"""
from vision.common.blockchains.enums import Blockchain

from vision.servicenode.blockchains.base import BlockchainClientError
from vision.servicenode.blockchains.ethereum import EthereumClient
from vision.servicenode.blockchains.ethereum import EthereumClientError


class CeloClientError(EthereumClientError):
    """Exception class for all Celo client errors.

    """
    pass


class CeloClient(EthereumClient):
    """Celo-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.CELO

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return CeloClientError
