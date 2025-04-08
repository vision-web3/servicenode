import hashlib
import json
import logging
import typing
import urllib.parse

from web3.middleware import Web3Middleware

from vision.servicenode.configuration import get_blockchains_rpc_nodes
from vision.servicenode.database.access import update_node_health_data

_logger = logging.getLogger(__name__)


class NodeHealthMiddleware(Web3Middleware):
    """Middleware to monitor the health of the blockchain nodes.

    This middleware is used to monitor the health of the blockchain nodes
    that are being used by the service node. It is used to keep track of the
    health of the nodes and to flush the data to the database.
    """
    _health_data: typing.Dict[str, typing.Dict[str, typing.Any]] = {}

    def add_blockchain_endpoint(self, endpoint_uri: str):
        """Add a blockchain endpoint to the health data.

        Parameters
        ----------
        endpoint_uri : str
            The endpoint URI to be added to the health data.
        """
        rpc_nodes = get_blockchains_rpc_nodes()
        for blockchain, nodes in rpc_nodes.items():
            if endpoint_uri in nodes[0]:
                if endpoint_uri not in self._health_data:
                    self._health_data[endpoint_uri] = {
                        'blockchain': blockchain,
                        'is_healthy': True,
                    }
                break

    @classmethod
    def flush_health_data(self):
        """Flush the health data to the database.

        """
        node_health_data: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for endpoint, data in self._health_data.items():
            blockchain = data['blockchain']
            if blockchain not in node_health_data:
                node_health_data[blockchain] = {
                    'unhealthy_total': 0,
                    'unhealthy_endpoints': [],
                    'healthy_total': 0,
                }
            if data['is_healthy']:
                node_health_data[blockchain]['healthy_total'] += 1
            else:
                node_health_data[blockchain]['unhealthy_total'] += 1
                node_health_data[blockchain]['unhealthy_endpoints'].append(
                    endpoint)

        for blockchain, blockchain_health_data in node_health_data.items():
            update_node_health_data(
                blockchain, blockchain_health_data['unhealthy_total'],
                json.dumps(blockchain_health_data['unhealthy_endpoints']),
                blockchain_health_data['healthy_total'])

    def __obfuscate_endpoint_path(self, url: str) -> str:
        """Obfuscate the path of the URL to be used as a key in the health
        data dictionary.

        Parameters
        ----------
        url : str
            URL to be obfuscated.

        Returns
        -------
        str
            Obfuscated URL

        @dev If you have a URL like `http://nodeprovider.xzy/v1/<api key>`
        the obfuscated URL will be `http://nodeprovider.xzy/<sha256 of path>`.
        If you provider has a different format, you can change the
        implementation here.
        """
        parsed_url = urllib.parse.urlparse(url)
        if len(parsed_url.path) > 0:
            h = hashlib.sha256()
            h.update(parsed_url.path.encode())
            obfuscated_url = \
                f"{parsed_url.scheme}://{parsed_url.netloc}{h.hexdigest()}"
        else:
            obfuscated_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return obfuscated_url

    def wrap_make_request(self, make_request):
        def middleware(method, params):
            try:
                response = make_request(method, params)
                _logger.info(self._w3.provider.endpoint_uri)
            except Exception as e:
                obfuscated_endpoint = self.__obfuscate_endpoint_path(
                    self._w3.provider.endpoint_uri)
                if obfuscated_endpoint in self._health_data:
                    self._health_data[obfuscated_endpoint]['is_healthy'] = False
                raise e
            return response

        return middleware
