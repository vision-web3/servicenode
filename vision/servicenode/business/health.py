"""Business logic for managing the service node itself.

"""
import json
import logging

from vision.common.blockchains.enums import Blockchain

from vision.servicenode.business.base import Interactor
from vision.servicenode.business.base import InteractorError
from vision.servicenode.configuration import get_blockchain_config
from vision.servicenode.database import access as database_access

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class HealthInteractorError(InteractorError):
    """Exception class for all health interactor errors.

    """
    pass


class HealthInteractor(Interactor):
    """Interactor for managing all health related information.

    """
    @classmethod
    def get_error_class(cls) -> type[InteractorError]:
        # Docstring inherited
        return HealthInteractorError

    def get_blockchain_nodes_health_status(
            self) -> list[dict[str, int | list[str]]]:
        """Gets the health status across all supported blockchains by the
        service node.

        Raises
        -------
        HealthInteractorError
            If the health status cannot be retrieved for any reason.

        """
        nodes_health = []
        try:
            for blockchain in Blockchain:
                blockchain_config = get_blockchain_config(blockchain)
                if not blockchain_config['active']:
                    continue
                nodes_health_data = database_access.read_node_health_data(
                    blockchain)
                if nodes_health_data is None:
                    continue
                nodes_health.append({
                    'blockchain': blockchain.name,
                    'unhealthy_total': nodes_health_data.unhealthy_total,
                    'unhealthy_endpoints': json.loads(
                        str(nodes_health_data.unhealthy_endpoints)),
                    'healthy_total': nodes_health_data.healthy_total
                })
            return nodes_health
        except HealthInteractorError:
            raise
        except Exception:
            raise self._create_error('unable to get the node health status',
                                     blockchain=blockchain)
