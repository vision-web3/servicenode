import hashlib
import logging
import typing
import urllib.parse

from vision.servicenode.configuration import get_blockchains_rpc_nodes

_logger = logging.getLogger(__name__)


class NodeHealthMiddleware():
    _health_data: typing.Dict[str, typing.Dict[str, typing.Any]] = {}

    def __init__(self, make_request=None, w3=None):
        self.make_request = make_request
        self.w3 = w3
        obfuscated_endpoint = self.__obfuscate_endpoint_path(
            w3.provider.endpoint_uri)
        self.add_blockchain_endpoint(obfuscated_endpoint)

    def add_blockchain_endpoint(self, endpoint_uri: str):
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
        node_health_data: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for endpoint, data in self._health_data.items():
            blockchain = data['blockchain'].name
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
        # TODO: Data needs to be written to DB and we need a model for this
        _logger.info(f"Node health data: {node_health_data}")

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

    def __call__(self, method, params):
        _logger.info(f"health data: {self._health_data}")
        # perform the RPC request, getting the response
        try:
            response = self.make_request(method, params)
        except Exception as e:
            obfuscated_endpoint = self.__obfuscate_endpoint_path(
                self.w3.provider.endpoint_uri)
            if obfuscated_endpoint in self._health_data:
                self._health_data[obfuscated_endpoint]['is_healthy'] = False
            raise e
        # finally return the response
        return response
