import unittest.mock

from vision.common.blockchains.enums import Blockchain

from vision.servicenode.database.access import read_node_health_data
from vision.servicenode.database.access import update_node_health_data

BLOCKCHAIN_ID: int = 0

INITIAL_UNHEALTHY_TOTAL: int = 0
INITIAL_UNHEALTHY_ENDPOINTS: str = "[]"
INITIAL_HEALTHY_TOTAL: int = 0


@unittest.mock.patch('vision.servicenode.database.access.get_session')
def test_read_node_health_correct_empty(mocked_session, db_initialized_session,
                                        embedded_db_session_maker):
    mocked_session.side_effect = embedded_db_session_maker

    node_health = read_node_health_data(Blockchain(BLOCKCHAIN_ID))
    assert node_health is None


@unittest.mock.patch('vision.servicenode.database.access.get_session')
@unittest.mock.patch('vision.servicenode.database.access.get_session_maker')
def test_read_node_health_data_correct_after_added(mocked_session_maker,
                                                   mocked_session,
                                                   db_initialized_session,
                                                   embedded_db_session_maker):
    mocked_session_maker.return_value = embedded_db_session_maker
    mocked_session.return_value = db_initialized_session
    update_node_health_data(Blockchain(BLOCKCHAIN_ID),
                            unhealthy_total=INITIAL_UNHEALTHY_TOTAL,
                            unhealthy_endpoints=INITIAL_UNHEALTHY_ENDPOINTS,
                            healthy_total=INITIAL_HEALTHY_TOTAL)

    node_health = read_node_health_data(Blockchain(BLOCKCHAIN_ID))

    assert node_health is not None
    assert node_health.blockchain_id == BLOCKCHAIN_ID
    assert node_health.unhealthy_total == INITIAL_UNHEALTHY_TOTAL
    assert node_health.unhealthy_endpoints == INITIAL_UNHEALTHY_ENDPOINTS
    assert node_health.healthy_total == INITIAL_HEALTHY_TOTAL
