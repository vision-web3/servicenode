import dataclasses
import unittest.mock

import pytest
from vision.common.blockchains.enums import Blockchain

from vision.servicenode.business import health as health_module
from vision.servicenode.business.health import HealthInteractor
from vision.servicenode.business.health import HealthInteractorError


@dataclasses.dataclass
class NodesHealth:
    blockchain: str
    unhealthy_total: int
    unhealthy_endpoints: list[str]
    healthy_total: int


class MockDatabaseAccess:
    def read_node_health_data(self, blockchain):
        return NodesHealth(blockchain=blockchain.name, unhealthy_total=0,
                           unhealthy_endpoints=[], healthy_total=0)


@pytest.fixture(scope='module')
def health_interactor():
    return HealthInteractor()


@pytest.fixture(autouse=True)
def mock_database_access(monkeypatch):
    mock_database_access = MockDatabaseAccess()
    monkeypatch.setattr(health_module, 'database_access', mock_database_access)


@unittest.mock.patch(
    'vision.servicenode.business.health.get_blockchain_config',
    side_effect=HealthInteractorError)
def test_get_blockchain_nodes_health_status_error(mocked_get_blockchain_config,
                                                  health_interactor):
    with pytest.raises(HealthInteractorError):
        health_interactor.get_blockchain_nodes_health_status()


@unittest.mock.patch(
    'vision.servicenode.business.health.get_blockchain_config',
    lambda blockchain: {'active': True})
def test_get_blockchain_nodes_health_status_correct(health_interactor):
    nodes_health = health_interactor.get_blockchain_nodes_health_status()

    all_blockchains = [e.name for e in Blockchain]
    assert len(nodes_health) == len(all_blockchains)

    for node_health in nodes_health:
        assert node_health['blockchain'] in all_blockchains
        assert node_health['unhealthy_total'] == 0
        assert node_health['unhealthy_endpoints'] == []
        assert node_health['healthy_total'] == 0
