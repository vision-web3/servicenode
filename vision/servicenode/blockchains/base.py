"""Base classes for all blockchain clients and errors.

"""
import abc
import dataclasses
import logging
import typing
import uuid

import semantic_version  # type: ignore
from hexbytes import HexBytes
from vision.common.blockchains.base import BlockchainHandler
from vision.common.blockchains.base import BlockchainUtilities
from vision.common.blockchains.base import BlockchainUtilitiesError
from vision.common.blockchains.base import NodeConnections
from vision.common.blockchains.base import VersionedContractAbi
from vision.common.blockchains.enums import Blockchain
from vision.common.blockchains.enums import ContractAbi
from vision.common.blockchains.factory import get_blockchain_utilities
from vision.common.blockchains.factory import initialize_blockchain_utilities
from vision.common.blockchains.tasks import \
    _dependent_transaction_submission_task
from vision.common.entities import TransactionStatus
from vision.common.exceptions import ErrorCreator
from vision.common.types import BlockchainAddress
from vision.common.types import ContractFunctionArgs

from vision.servicenode.configuration import config
from vision.servicenode.configuration import get_blockchain_config
from vision.servicenode.exceptions import ServiceNodeError
from vision.servicenode.protocol import is_supported_protocol_version

_logger = logging.getLogger(__name__)


class BlockchainClientError(ServiceNodeError):
    """Exception class for all blockchain client errors.

    """
    pass


class InsufficientBalanceError(BlockchainClientError):
    """Exception class for all blockchain client errors caused by an
    insufficient balance.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('insufficient balance', **kwargs)


class InvalidSignatureError(BlockchainClientError):
    """Exception class for all blockchain client errors caused by an
    invalid signature.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('invalid signature', **kwargs)


class UnresolvableTransferSubmissionError(BlockchainClientError):
    """Exception to be raised if there has been an unresolvable error
    during a single-chain transfer or cross-chain transferFrom
    submission.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('unresolvable transfer/transferFrom submission error',
                         **kwargs)


class BlockchainClient(BlockchainHandler, ErrorCreator[BlockchainClientError]):
    """Base class for all blockchain clients.

    Attributes
    ----------
    protocol_version : semantic_version.Version
        The version of the Vision protocol that the blockchain client
        instance is compliant with.

    """
    def __init__(self):
        """Construct a blockchain client instance.

        Raises
        ------
        BlockchainClientError
            If the corresponding blockchain utilities cannot be
            initialized.

        """
        self.protocol_version: typing.Final[
            semantic_version.Version] = semantic_version.Version(
                config['protocol'])
        assert is_supported_protocol_version(self.protocol_version)
        blockchain_node_url = self._get_config()['provider']
        fallback_blockchain_nodes_urls = self._get_config().get(
            'fallback_providers', [])
        average_block_time = self._get_config()['average_block_time']
        required_transaction_confirmations = \
            self._get_config()['confirmations']
        transaction_network_id = self._get_config().get('chain_id')
        private_key = self._get_config()['private_key']
        private_key_password = self._get_config()['private_key_password']
        try:
            initialize_blockchain_utilities(
                self.get_blockchain(), [blockchain_node_url],
                fallback_blockchain_nodes_urls, average_block_time,
                required_transaction_confirmations, transaction_network_id,
                default_private_key=(private_key, private_key_password),
                celery_tasks_enabled=True)
        except BlockchainUtilitiesError:
            raise self._create_error(
                f'unable to initialize the {self.get_blockchain_name()} '
                'utilities')

    @abc.abstractmethod
    def get_own_address(self) -> BlockchainAddress:
        """Get the service node's own address on the blockchain.

        Returns
        -------
        BlockchainAddress
            The service node's own address.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def is_node_registered(self) -> bool:
        """Determine if the service node is registered at the Vision Hub
        on the blockchain.

        Returns
        -------
        bool
            True if the service node is registered, else False.

        Raises
        ------
        BlockchainClientError
            If it cannot be determined if the service node is
            registered.

        """
        pass  # pragma: no cover

    def is_protocol_version_supported_by_forwarder_contract(self) -> bool:
        """Determine if the configured protocol version is supported by
        the configured Forwarder contract.

        Returns
        -------
        bool
            True if the Forwarder contract supports the protocol
            version.

        """
        return self._get_utilities().is_protocol_version_supported_by_contract(
            self._get_config()['forwarder'],
            self._versioned_vision_forwarder_abi)  # pragma: no cover

    def is_protocol_version_supported_by_hub_contract(self) -> bool:
        """Determine if the configured protocol version is supported by
        the configured Hub contract.

        Returns
        -------
        bool
            True if the Hub contract supports the protocol version.

        """
        return self._get_utilities().is_protocol_version_supported_by_contract(
            self._get_config()['hub'],
            self._versioned_vision_hub_abi)  # pragma: no cover

    def is_valid_address(self, address: str) -> bool:
        """Determine if an address string is a valid address on the
        blockchain.

        Parameters
        ----------
        address : str
            The address string to check.

        Returns
        -------
        bool
            True if the given address string is a valid address on the
            blockchain, else False.

        """
        return self._get_utilities().is_valid_address(
            address)  # pragma: no cover

    @abc.abstractmethod
    def is_valid_recipient_address(self, recipient_address: str) -> bool:
        """Determine if an address string is a valid recipient address
        on the blockchain.

        Parameters
        ----------
        recipient_address : str
            The address string to check.

        Returns
        -------
        bool
            True if the given address string is a valid recipient
            address on the blockchain.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class ExternalTokenRecordRequest:
        """Request data for reading an external token record.

        Attributes
        ----------
        token_address : BlockchainAddress
            The address of the token on the blockchain the external
            token record is read from.
        external_blockchain : Blockchain
            The blockchain to read the external token record for.

        """
        token_address: BlockchainAddress
        external_blockchain: Blockchain

    @dataclasses.dataclass
    class ExternalTokenRecordResponse:
        """Response data from reading an external token record.

        Attributes
        ----------
        is_registration_active : bool
            True if the external token registration is active.
        external_token_address : BlockchainAddress
            The registered external address of the token.

        """
        is_registration_active: bool
        external_token_address: BlockchainAddress

    @abc.abstractmethod
    def read_external_token_record(
            self, request: ExternalTokenRecordRequest) \
            -> ExternalTokenRecordResponse:
        """Read an external token record from the Vision Hub.

        Parameters
        ----------
        request : ExternalTokenRecordRequest
            The request data.

        Returns
        -------
        ExternalTokenRecordResponse
            The response data.

        Raises
        ------
        BlockchainClientError
            If the external token record cannot be read.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def read_minimum_deposit(self) -> int:
        """Read the service node's minimum deposit at the Vision Hub on
        the blockchain.

        Returns
        -------
        int
            The service node's minimum deposit.

        Raises
        ------
        BlockchainClientError
            If the service node's minimum deposit cannot be read.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def read_node_url(self) -> str:
        """Read the service node's URL that is registered at the Vision
        Hub on the blockchain.

        Returns
        -------
        str
            The service node's registered URL.

        Raises
        ------
        BlockchainClientError
            If the service node's registered URL cannot be read.

        """
        pass  # pragma: no cover

    def read_own_vsn_balance(self) -> int:
        """Read the service node's own VSN token balance on the
        blockchain.

        Returns
        -------
        int
            The service node's own VSN token balance.

        Raises
        ------
        BlockchainClientError
            If the service node's own VSN token balance cannot be read.

        """
        try:
            return self._get_utilities().get_balance(
                self.get_own_address(),
                token_address=self._get_config()['vsn_token'])
        except Exception:
            raise self._create_error(
                'unable to read the own VSN token balance')

    @abc.abstractmethod
    def register_node(self, node_url: str, node_deposit: int,
                      withdrawal_address: BlockchainAddress) -> None:
        """Register the service node at the Vision Hub on the blockchain.

        Parameters
        ----------
        node_url : str
            The service node's URL to be registered.
        node_deposit : int
            The service node's deposit to be locked (must be at least
            the minimum required service node deposit at the Vision
            Hub).
        withdrawal_address : BlockchainAddress
            The address where the deposit will be returned after the
            service node has been unregistered.

        Raises
        ------
        BlockchainClientError
            If the service node cannot be registered.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferSubmissionStartRequest:
        """Request data for starting a single-chain transfer submission.

        Attributes
        ----------
        internal_transfer_id : int
            The internal unique ID of the transfer record.
        sender_address : str
            The sender's blockchain address.
        recipient_address : str
            The recipient's blockchain address.
        token_address : str
            The transferred token's blockchain address.
        amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        fee : int
            The fee in 10^-8 VSN a user has to pay for the token
            transfer.
        sender_nonce : int
            The unique nonce of the sender for the token transfer.
        valid_until : int
            The timestamp until when the token transfer is valid (in
            seconds since the epoch).
        signature : str
            The sender's token transfer signature.

        """
        internal_transfer_id: int
        sender_address: str
        recipient_address: str
        token_address: str
        amount: int
        fee: int
        sender_nonce: int
        valid_until: int
        signature: str

    @abc.abstractmethod
    def start_transfer_submission(
            self, request: TransferSubmissionStartRequest) -> uuid.UUID:
        """Start a single-chain transfer submission. The transaction is
        automatically resubmitted with higher transaction fees until it
        is included in a block.

        Parameters
        ----------
        request : TransferSubmissionStartRequest
            The request data.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID.

        Raises
        ------
        InsufficientBalanceError
            If the sender's balance is insufficient.
        InvalidSignatureError
            If the sender's signature is invalid.
        BlockchainClientError
            If the transfer submission cannot be processed or started
            for any other reason.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferFromSubmissionStartRequest:
        """Request data for starting a cross-chain transferFrom
        submission.

        Attributes
        ----------
        internal_transfer_id : int
            The internal unique ID of the transfer record.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.
        sender_address : str
            The sender's address on the source blockchain.
        recipient_address : str
            The recipient's address on the destination blockchain.
        source_token_address : str
            The transferred token's address on the source blockchain.
        destination_token_address : str
            The transferred token's address on the destination
            blockchain.
        amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        fee : int
            The fee in 10^-8 VSN a user has to pay for the token
            transfer.
        sender_nonce : int
            The unique nonce of the sender for the token transfer on the
            source blockchain.
        valid_until : int
            The timestamp until when the token transfer is valid on the
            source blockchain (in seconds since the epoch).
        signature : str
            The sender's token transfer signature.

        """
        internal_transfer_id: int
        destination_blockchain: Blockchain
        sender_address: str
        recipient_address: str
        source_token_address: str
        destination_token_address: str
        amount: int
        fee: int
        sender_nonce: int
        valid_until: int
        signature: str

    @abc.abstractmethod
    def start_transfer_from_submission(
            self, request: TransferFromSubmissionStartRequest) -> uuid.UUID:
        """Start a cross-chain transferFrom submission. The transaction
        is automatically resubmitted with higher transaction fees until
        it is included in a block.

        Parameters
        ----------
        request : TransferFromSubmissionStartRequest
            The request data.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID.

        Raises
        ------
        InsufficientBalanceError
            If the sender's balance is insufficient.
        InvalidSignatureError
            If the sender's signature is invalid.
        BlockchainClientError
            If the transferFrom submission cannot be processed or
            started for any other reason.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferSubmissionStatusResponse:
        """Response data from retrieving the status of a single-chain
        transfer or cross-chain transferFrom submission.

        Attributes
        ----------
        transaction_submission_completed : bool
            True if and only if the transaction submission has been
            completed (i.e. the transaction is either confirmed or
            reverted).
        transaction_status : TransactionStatus or None
            The status of the submitted (and eventually included)
            transaction (available if the transaction submission has
            been completed).
        transaction_id : str or None
            The ID/hash of the submitted (and eventually included)
            transaction (available if the transaction submission has
            been completed).
        on_chain_transfer_id : int or None
            The Vision transfer ID on the source blockchain (available
            if the transaction has been confirmed).

        """
        transaction_submission_completed: bool
        transaction_status: TransactionStatus | None = None
        transaction_id: str | None = None
        on_chain_transfer_id: int | None = None

    def get_transfer_submission_status(
            self, internal_transaction_id: uuid.UUID,
            destination_blockchain: Blockchain) \
            -> TransferSubmissionStatusResponse:
        """Retrieve the status of a single-chain transfer or cross-chain
        transferFrom submission.

        Parameters
        ----------
        internal_transaction_id : uuid.UUID
            The unique internal transaction ID.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.

        Returns
        -------
        TransferSubmissionStatusResponse
            The response data.

        Raises
        ------
        UnresolvableTransferSubmissionError
            If there has been an unresolvable error during the
            transfer/transferFrom submission.
        BlockchainClientError
            If the Vision transfer ID on the source blockchain cannot be
            read.

        """
        try:
            status_response = \
                self._get_utilities().get_transaction_submission_status(
                    internal_transaction_id)
        except BlockchainUtilitiesError:
            raise self._create_unresolvable_transfer_submission_error(
                internal_transaction_id=internal_transaction_id)
        _logger.info(
            'transfer/transferFrom transaction submission status',
            extra=vars(status_response)
            | {'internal_transaction_id': internal_transaction_id})
        if not status_response.transaction_submission_completed:
            return BlockchainClient.TransferSubmissionStatusResponse(False)
        transaction_status = status_response.transaction_status
        assert transaction_status in [
            TransactionStatus.CONFIRMED, TransactionStatus.REVERTED
        ]
        transaction_id = status_response.transaction_id
        assert transaction_id is not None
        on_chain_transfer_id = (None if transaction_status
                                is not TransactionStatus.CONFIRMED else
                                self._read_on_chain_transfer_id(
                                    transaction_id, destination_blockchain))
        return BlockchainClient.TransferSubmissionStatusResponse(
            True, transaction_status=transaction_status,
            transaction_id=transaction_id,
            on_chain_transfer_id=on_chain_transfer_id)

    @abc.abstractmethod
    def unregister_node(self) -> None:
        """Unregister the service node at the Vision Hub on the
        blockchain.

        Raises
        ------
        BlockchainClientError
            If the service node cannot be unregistered.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def update_node_url(self, node_url: str) -> None:
        """Update the service node's URL that is registered at the
        Vision Hub on the blockchain.

        Parameters
        ----------
        node_url : str
            The service node's new URL to be registered.

        Raises
        ------
        BlockchainClientError
            If the service node's registered URL cannot be updated.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def is_unbonding(self) -> bool:
        """Determine if the service node is in the unbonding period and
        has not yet withdrawn its deposit.

        Returns
        -------
        bool
            True if service node is in the unbonding period and has not
            yet withdrawn its deposit.

        Raises
        ------
        BlockchainClientError
            If the unbonding status cannot be checked.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def cancel_unregistration(self) -> None:
        """Cancel the service node unregistration.

        Raises
        ------
        BlockchainClientError
            If the unregistration cannot be cancelled.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def calculate_commitment(self, abi_types: list[str],
                             values: list[typing.Any]) -> HexBytes:
        """Calculate the commitment hash for the given ABI types and
        values.

        Parameters
        ----------
        abi_types : list[str]
            The ABI types of the values.
        values : list[typing.Any]
            The values to be hashed.

        Returns
        -------
        web3.HexBytes
            The commitment hash.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_commitment_wait_period(self, blockchain: Blockchain) -> int:
        """Get the commitment wait period for the service node.

        Returns
        -------
        int
            The commitment wait period in blocks.

        Raises
        ------
        BlockchainClientError
            If the commitment wait period cannot be obtained.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_validator_fee_factor(self, blockchain: Blockchain) -> int:
        """Get the validator fee factor of the given blockchain.

        Returns
        -------
            The validator fee factor.

        Raises
        ------
        BlockchainClientError
            If the validator fee factor cannot be obtained.

        """
        pass  # pragma: no cover

    def _create_insufficient_balance_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=InsufficientBalanceError, **kwargs)

    def _create_invalid_signature_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=InvalidSignatureError, **kwargs)

    def _create_unresolvable_transfer_submission_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=UnresolvableTransferSubmissionError,
            **kwargs)

    def _get_config(self) -> dict[str, typing.Any]:
        return get_blockchain_config(self.get_blockchain())  # pragma: no cover

    def _get_utilities(self) -> BlockchainUtilities:
        return get_blockchain_utilities(
            self.get_blockchain())  # pragma: no cover

    @abc.abstractmethod
    def _read_on_chain_transfer_id(self, transaction_id: str,
                                   destination_blockchain: Blockchain) -> int:
        """Read the Vision transfer ID on the source blockchain.

        Parameters
        ----------
        transaction_id : str
            The ID/hash of the transaction.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.

        Returns
        -------
        int
            The Vision transfer ID on the source blockchain.

        Raises
        ------
        BlockchainClientError
            If the Vision transfer ID on the source blockchain cannot be
            read.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class _TransactionSubmissionStartRequest:
        """Request data for starting a transaction submission.

        Attributes
        ----------
        versioned_contract_abi : VersionedContractAbi
            The version and the ABI of the contract to invoke a function
            on in the transaction.
        function_selector : str
            The selector of the contract function to be invoked in the
            transaction.
        function_args : ContractFunctionArgs
            The arguments of the contract function to be invoked in the
            transaction.
        gas : int or None
            The gas to be provided for the transaction. Depending on the
            blockchain, it may not be necessary to specify the gas
            explicitly or it may be possible to estimate the required gas
            automatically.
        amount : int or None
            The amount of native coins to be sent in the transaction
            (specified in the blockchain's smallest coin denomination).
        nonce : int
            The unique transaction nonce of the account controlled by
            the default private key.

        """
        versioned_contract_abi: VersionedContractAbi
        function_selector: str
        function_args: ContractFunctionArgs
        gas: int | None
        amount: int | None
        nonce: int

    def _start_transaction_submission(
            self, request: _TransactionSubmissionStartRequest,
            node_connections: NodeConnections) -> uuid.UUID:
        """Start a transaction submission. The transaction is
        automatically resubmitted with higher transaction fees until it
        is included in a block.

        Parameters
        ----------
        request : _TransactionSubmissionStartRequest
            The request data for starting a transaction submission.
        node_connections : NodeConnections
            The NodeConnections instance to be used when interacting
            with blockchain nodes.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID, which can be used later
            to retrieve the status of the transaction submission.

        Raises
        ------
        vision.common.blockchains.base.MaxTotalFeePerGasExceededError
            If the maximum total fee per gas would be exceeded for the
            transaction to be submitted.
        vision.common.blockchains.base.TransactionNonceTooLowError
            If the transaction has been submitted with a nonce too low.
        BlockchainUtilitiesError
            If the transaction submission cannot be started for any
            other reason.

        """
        contract_abi = request.versioned_contract_abi.contract_abi
        if contract_abi is ContractAbi.VISION_HUB:
            contract_address = self._get_config()['hub']
        elif contract_abi is ContractAbi.VISION_TOKEN:
            contract_address = self._get_config()['vsn_token']
        else:
            raise NotImplementedError
        min_adaptable_fee_per_gas = \
            self._get_config()['min_adaptable_fee_per_gas']
        max_total_fee_per_gas = self._get_config().get('max_total_fee_per_gas')
        if max_total_fee_per_gas == 0:
            # Since YAML Tag directives do not support the `or` operation
            max_total_fee_per_gas = None
        adaptable_fee_increase_factor = \
            self._get_config()['adaptable_fee_increase_factor']
        blocks_until_resubmission = \
            self._get_config()['blocks_until_resubmission']
        request_ = BlockchainUtilities.TransactionSubmissionStartRequest(
            contract_address, request.versioned_contract_abi,
            request.function_selector, request.function_args, request.gas,
            min_adaptable_fee_per_gas, max_total_fee_per_gas, request.amount,
            request.nonce, adaptable_fee_increase_factor,
            blocks_until_resubmission)
        return self._get_utilities().start_transaction_submission(
            request_, node_connections)

    @dataclasses.dataclass
    class _DependingTransactionSubmissionStartRequest:
        """Request data for starting a depending transaction submission.

        Attributes
        ----------
        prerequisite_transaction: _TransactionSubmissionStartRequest
            Transaction submission request data for the transaction to be
            send before the depending transaction.
        dependent_transaction: _TransactionSubmissionStartRequest
            Transaction submission request data for the depending
            transaction.
        blocks_to_wait: int
            The number of blocks to wait before submitting the depending
            transaction.
        """
        # Forward Reference: Python postpones the evaluation for Python >v3.10
        # automatically
        prerequisite_transaction: \
            "BlockchainClient._TransactionSubmissionStartRequest"
        dependent_transaction: \
            "BlockchainClient._TransactionSubmissionStartRequest"
        blocks_to_wait: int

    def _start_depending_transactions_submission(
            self, request: _DependingTransactionSubmissionStartRequest,
            node_connections: NodeConnections) -> uuid.UUID:
        """Start a depending transaction submission. The dependent
        transaction is automatically submitted as soon as the prerequisite
        transaction is included and reaches a given number of blocks.

        Parameters
        ----------
        request : _DependingTransactionSubmissionStartRequest
            The request data for starting a depending transaction
            submission.
        node_connections : NodeConnections
            The NodeConnections instance to be used when interacting
            with blockchain nodes.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID, which can be used later
            to retrieve the status of the transaction submission.
        """
        contract_abi = \
            request.prerequisite_transaction \
            .versioned_contract_abi.contract_abi
        if contract_abi is ContractAbi.VISION_HUB:
            contract_address = self._get_config()['hub']
        elif contract_abi is ContractAbi.VISION_TOKEN:
            contract_address = self._get_config()['vsn_token']
        else:
            raise NotImplementedError
        min_adaptable_fee_per_gas = \
            self._get_config()['min_adaptable_fee_per_gas']
        max_total_fee_per_gas = self._get_config().get('max_total_fee_per_gas')
        if max_total_fee_per_gas == 0:
            # Since YAML Tag directives do not support the `or` operation
            max_total_fee_per_gas = None
        adaptable_fee_increase_factor = \
            self._get_config()['adaptable_fee_increase_factor']
        blocks_until_resubmission = \
            self._get_config()['blocks_until_resubmission']
        prerequisite_request = \
            BlockchainUtilities.TransactionSubmissionStartRequest(
                contract_address,
                request.prerequisite_transaction.versioned_contract_abi,
                request.prerequisite_transaction.function_selector,
                request.prerequisite_transaction.function_args,
                request.prerequisite_transaction.gas,
                min_adaptable_fee_per_gas,
                max_total_fee_per_gas, request.prerequisite_transaction.amount,
                request.prerequisite_transaction.nonce,
                adaptable_fee_increase_factor, blocks_until_resubmission)

        prerequisite_internal_id = self._get_utilities(
        ).start_transaction_submission(prerequisite_request, node_connections)

        dependent_request = \
            BlockchainUtilities.TransactionSubmissionStartRequest(
                contract_address,
                request.dependent_transaction.versioned_contract_abi,
                request.dependent_transaction.function_selector,
                request.dependent_transaction.function_args,
                request.dependent_transaction.gas, min_adaptable_fee_per_gas,
                max_total_fee_per_gas, request.dependent_transaction.amount,
                request.dependent_transaction.nonce,
                adaptable_fee_increase_factor,
                blocks_until_resubmission)

        return _dependent_transaction_submission_task.delay(
            blockchain_id=self.get_blockchain().value,
            prerequisite_internal_id=str(prerequisite_internal_id),
            blocks_to_wait=request.blocks_to_wait,
            average_block_time=self._get_config()['average_block_time'],
            request=dependent_request.to_dict())

    @property
    def _versioned_vision_forwarder_abi(self) -> VersionedContractAbi:
        return VersionedContractAbi(ContractAbi.VISION_FORWARDER,
                                    self.protocol_version)

    @property
    def _versioned_vision_hub_abi(self) -> VersionedContractAbi:
        return VersionedContractAbi(ContractAbi.VISION_HUB,
                                    self.protocol_version)

    @property
    def _versioned_vision_token_abi(self) -> VersionedContractAbi:
        return VersionedContractAbi(ContractAbi.VISION_TOKEN,
                                    self.protocol_version)
