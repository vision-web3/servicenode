import unittest.mock

import sqlalchemy
import sqlalchemy.exc
from vision.common.blockchains.enums import Blockchain

from vision.servicenode.database.access import update_node_health_data
from vision.servicenode.database.models import NodesHealth

BLOCKCHAIN_ID: int = 0

INITIAL_UNHEALTHY_TOTAL: int = 0
INITIAL_UNHEALTHY_ENDPOINTS: str = "[]"
INITIAL_HEALTHY_TOTAL: int = 0

UPDATED_UNHEALTHY_TOTAL: int = 1
UPDATED_UNHEALTHY_ENDPOINTS: str = "['123']"
UPDATED_HEALTHY_TOTAL: int = 2


@unittest.mock.patch('vision.servicenode.database.access.get_session_maker')
def test_update_node_health_correct_newly_added(mocked_session,
                                                db_initialized_session,
                                                embedded_db_session_maker):
    mocked_session.return_value = embedded_db_session_maker
    update_node_health_data(Blockchain(BLOCKCHAIN_ID),
                            unhealthy_total=INITIAL_UNHEALTHY_TOTAL,
                            unhealthy_endpoints=INITIAL_UNHEALTHY_ENDPOINTS,
                            healthy_total=INITIAL_HEALTHY_TOTAL)

    nodes_health = db_initialized_session.execute(
        sqlalchemy.select(NodesHealth, BLOCKCHAIN_ID)).one_or_none()[0]

    assert nodes_health.blockchain_id == BLOCKCHAIN_ID
    assert nodes_health.unhealthy_total == INITIAL_UNHEALTHY_TOTAL
    assert nodes_health.unhealthy_endpoints == INITIAL_UNHEALTHY_ENDPOINTS
    assert nodes_health.healthy_total == INITIAL_HEALTHY_TOTAL


@unittest.mock.patch('vision.servicenode.database.access.get_session_maker')
def test_update_node_health_correct_updated(mocked_session,
                                            db_initialized_session,
                                            embedded_db_session_maker):
    mocked_session.return_value = embedded_db_session_maker
    update_node_health_data(Blockchain(BLOCKCHAIN_ID),
                            unhealthy_total=INITIAL_UNHEALTHY_TOTAL,
                            unhealthy_endpoints=INITIAL_UNHEALTHY_ENDPOINTS,
                            healthy_total=INITIAL_HEALTHY_TOTAL)

    update_node_health_data(Blockchain(BLOCKCHAIN_ID),
                            unhealthy_total=UPDATED_UNHEALTHY_TOTAL,
                            unhealthy_endpoints=UPDATED_UNHEALTHY_ENDPOINTS,
                            healthy_total=UPDATED_HEALTHY_TOTAL)

    nodes_health = db_initialized_session.execute(
        sqlalchemy.select(NodesHealth, BLOCKCHAIN_ID)).one_or_none()[0]

    assert nodes_health.blockchain_id == BLOCKCHAIN_ID
    assert nodes_health.unhealthy_total == UPDATED_UNHEALTHY_TOTAL
    assert nodes_health.unhealthy_endpoints == UPDATED_UNHEALTHY_ENDPOINTS
    assert nodes_health.healthy_total == UPDATED_HEALTHY_TOTAL
