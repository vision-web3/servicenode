import unittest.mock

import pytest
import sqlalchemy
import sqlalchemy.exc
from vision.common.blockchains.enums import Blockchain

from tests.database.conftest import populate_transfer_database
from vision.servicenode.database.access import read_transfer_nonce
from vision.servicenode.database.enums import TransferStatus
from vision.servicenode.database.models import Transfer


@pytest.mark.parametrize(
    ("statuses", "blockchain_ids", "nonces"),
    [([TransferStatus.CONFIRMED, TransferStatus.CONFIRMED
       ], [Blockchain.ETHEREUM, Blockchain.ETHEREUM], [0, 1])])
@unittest.mock.patch('vision.servicenode.database.access.get_session')
def test_read_nonce_with_success_nonces_equal_nonce_received(
        mocked_get_session, db_initialized_session, statuses, blockchain_ids,
        nonces):
    mocked_get_session.return_value = db_initialized_session
    populate_transfer_database(db_initialized_session, blockchain_ids,
                               statuses, nonces)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.nonce == 0)).fetchall()[0][0]

    assert (transfer.nonce == read_transfer_nonce(transfer.id))
