import json
import unittest.mock

from vision.servicenode.business.health import HealthInteractorError
from vision.servicenode.restapi import HealthInteractor


@unittest.mock.patch('vision.servicenode.restapi.ok_response',
                     lambda data: data)
def test_health_nodes_correct(test_client):
    with unittest.mock.patch.object(HealthInteractor,
                                    'get_blockchain_nodes_health_status',
                                    return_value=[]):
        response = test_client.get('/health/nodes')

    assert response.status_code == 200
    assert json.loads(response.text) == []


def test_health_nodes_error_getting_data(test_client):
    with unittest.mock.patch.object(HealthInteractor,
                                    'get_blockchain_nodes_health_status',
                                    side_effect=HealthInteractorError):
        response = test_client.get('/health/nodes')

    assert response.status_code == 500
