import time
from smartz.api.constructor_engine import ConstructorInstance


class Constructor(ConstructorInstance):

    def get_version(self):
        return {
            "result": "success",
            "version": 2,
            "blockchain": "ethereum"
        }

    def get_params(self):
        json_schema = {
            "type": "object",
            "required": [
                "dataType", "price", "owners", "signs_count"
            ],

            "additionalProperties": True,

            "properties": {
                "dataType": {
                    "title": "Type of data",
                    "description": "Type of data which will be stored.",
                    "type": "string",
                    "enum": ['string', 'address', 'uint', 'int', 'bytes'],
                    "default": "string"
                },

                "price": {
                    "title": "Price of data",
                    "description": "Ether amount required for one getData function call",
                    "$ref": "#/definitions/ethCount",
                },

                "owners": {
                    "title": "List of owners",
                    "description": "List of oracle owners for multisig",
                    "type": "array",
                    "items": {"$ref": "#/definitions/address"},
                    "minItems": 1,
                    "maxItems": 250
                },

                "signs_count": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 2,
                    "maximum": 250,
                    "title": "Signatures quorum",
                    "description": "Number of signatures required to withdraw funds or modify signatures"
                },
            },

            "dependencies": {
                "dataType": {
                    "oneOf": [{
                        "properties": {
                            "dataType": {
                                "enum": ['uint', 'int']
                            },
                            "integerSize": {
                                "title": "Number of bits",
                                "description": 'Number of bits for choosed type, 8 to 256 with step 8',
                                "type": 'integer',
                                "minimum": 8,
                                "maximum": 256,
                                "default": 256,
                            },
                            "isArray": {
                                "title": "Data is array",
                                "description": "If you check this data will be array",
                                "type": "boolean",
                                "default": False
                            },
                        },
                        "required": ["isArray", "integerSize"]
                    }, {
                        "properties": {
                            "dataType": {
                                "enum": ['bytes']
                            },
                            "bytesSize": {
                                "title": "Number of bytes",
                                "description": 'Number of bytes, 1 to 32',
                                "type": 'integer',
                                "minimum": 1,
                                "maximum": 32,
                                "default": 32,
                            }
                        },
                        "required": ["bytesSize"]
                    }, {
                        "properties": {
                            "dataType": {
                                "enum": ['string']
                            }
                        }
                    }, {
                        "properties": {
                            "dataType": {
                                "enum": ['address']
                            },
                            "isArray": {
                                "title": "Data is array",
                                "description": "If you check this data will be array",
                                "type": "boolean",
                                "default": False
                            },
                        },
                        "required": ["isArray"]
                    }]
                }
            }
        }

        ui_schema = {
            "ui:order": ["dataType", "*", "price", "owners", "signs_count"],

            "signs_count": {
                "ui:widget": "updown",
            },

            "owners": {
                "items": {
                    "ui:placeholder": "Valid Ethereum address"
                },
                "ui:options": {
                    "orderable": False
                }
            },

            "price": {
                "ui:widget": "ethCount"
            },

            "dataType": {
                "ui:widget":"radio",
            },
        }

        return {
            "result": "success",
            "schema": json_schema,
            "ui_schema": ui_schema
        }

    def construct(self, fields_vals):

        source = self.__class__._TEMPLATE

        if fields_vals['signs_count'] > len(fields_vals['owners']):
            return {
                "result": "error",
                "error_descr": "Signatures quorum is greater than total number of owners"
            }

        dataType = fields_vals['dataType']

        if dataType in ['uint', 'int']:
            if fields_vals['integerSize'] % 8 != 0:
                return {
                    "result": "error",
                    "error_descr": "Number of bits must be a multiple of 8"
                }
            dataType += str(fields_vals['integerSize'])
        elif dataType == 'bytes':
            dataType += str(fields_vals['bytesSize'])

        if 'isArray' in fields_vals and fields_vals['isArray'] == True:
            dataType += '[]'

        owners_code = 'address[] memory result = new address[]({});\n'.format(len(fields_vals['owners']))
        owners_code += '\n'.join(
            'result[{}] = address({});'.format(idx, owner) for (idx, owner) in enumerate(fields_vals['owners'])
        )

        source = source \
            .replace('%dataType%', dataType) \
            .replace('%price%', str(fields_vals['price'])) \
            .replace('%owners_code%', owners_code) \
            .replace('%signs_count%', str(fields_vals['signs_count']))

        return {
            "result": "success",
            'source': source,
            'contract_name': "OracleWrapper"
        }

    def post_construct(self, fields_vals, abi_array):

        function_titles = {
            'price': {
                'title': 'Data price',
                'description': 'Cost of one call of getData function',
                'ui:widget': 'ethCount',
                'sorting_order': 10
            },

            'lastDataUpdate': {
                'title': 'Last update time',
                'description': 'Time of last data update',
                'ui:widget': 'unixTime',
                'ui:widget_options': {
                    'format': 'yyyy.mm.dd HH:MM:ss (o)'
                },
                'sorting_order': 20
            },

            'nonce': {
                'title': 'Current nonce',
                'description': 'This nonce need for number of functions',
                'sorting_order': 30
            },

            'm_numOwners': {
                'title': 'Number of owners',
                'description': 'How many owners are added to the contract',
                'sorting_order': 40
            },

            'm_multiOwnedRequired': {
                'title': 'Quorum requirement',
                'description': 'Number of signatures required to perform actions',
                'sorting_order': 50
            },

            'getData': {
                'title': 'Get data',
                'description': 'Get data from oracle',
                'payable_details': {
                    'title': 'Ether amount (must be equal to the data price)',
                    'description': 'This ether amount will be sent with the function call',
                },
                'sorting_order': 60
            },

            'withdraw': {
                'title': 'Withdraw',
                'description': 'Send some amount of Ether to specified address (Need quorum of of owners)',
                'inputs': [{
                    'title': 'Destination address',
                }, {
                    'title': 'Ether amount',
                    'description': 'How ether will be sent',
                    'ui:widget': 'ethCount'
                }],
                'sorting_order': 70
            },

            'setPrice': {
                'title': 'Set price',
                'description': 'Set new price (Need quorum of of owners)',
                'inputs': [{
                    'title': 'New price',
                    'ui:widget': 'ethCount'
                }, {
                    'title': 'Nonce',
                }],
                'sorting_order': 80
            },

            'updateData': {
                'title': 'Update data',
                'description': 'Update data (Need quorum of of owners)',
                'inputs': [{
                    'title': 'New data',
                }, {
                    'title': 'Nonce'
                }],
                'sorting_order': 90
            },

            'changeRequirement': {
                'title': 'Change quorum requirement',
                'description': 'Change number of signatures required to perform actions on this wallet '
                               '(withdraw money, change owners, etc). Quorum of wallet owners must call this function with the same parameters for this action to happen.',
                'inputs': [{
                    'title': 'new requirement',
                    'description': 'new number of signatures required to perform actions on this wallet'
                }],
                'sorting_order': 100
            },

            'hasConfirmed': {
                'title': 'Is operation confirmed?',
                'description': 'Checks if operation confirmed by an owner.',
                'sorting_order': 110
            },

            'revoke': {
                'title': 'Revoke confirmation',
                'description': 'Revoke confirmation of current owner (current account) from operation.',
                'sorting_order': 120
            },

            'amIOwner': {
                'title': 'Am I owner?',
                'description': 'Checks if current account is one of the wallet owners.',
                'sorting_order': 130
            },

            'isOwner': {
                'title': 'Check owner',
                'description': 'Checks if specified account is one of the wallet owners.',
                'inputs': [{
                    'title': 'Address to check',
                }],
                'sorting_order': 140
            },

            'getOwners': {
                'title': 'Owners',
                'description': 'Returns list of all current owners of the wallet.',
                'sorting_order': 150
            },

            'getOwner': {
                'title': 'Get n-th owner',
                'description': 'Returns n-th owner',
                'inputs': [{
                    'title': 'Owner\'s number',
                    'description': 'Owner\'s number, starting from zero.',
                }],
                'sorting_order': 160
            },

            'removeOwner': {
                'title': 'Remove owner',
                'description': 'Removes specified owner. Quorum of wallet owners must call this function with the same parameters for this action to happen.',
                'inputs': [{
                    'title': 'Address',
                    'description': 'Address of the owner to remove.',
                }],
                'sorting_order': 170
            },

            'addOwner': {
                'title': 'Add owner',
                'description': 'Adds a new owner. Quorum of wallet owners must call this function with the same parameters for this action to happen.',
                'inputs': [{
                    'title': 'Address',
                    'description': 'Address of the new (additional) owner.',
                }],
                'sorting_order': 180
            },

            'changeOwner': {
                'title': 'Change owner',
                'description': 'Changes address of existing owner from one to another. Quorum of wallet owners must call this function with the same parameters for this action to happen.',
                'inputs': [{
                    'title': 'Old address',
                }, {
                    'title': 'New address',
                }],
                'sorting_order': 190
            },
        }

        return {
            "result": "success",
            'function_specs': function_titles,
            'dashboard_functions': ['price', 'lastDataUpdate', 'm_numOwners', 'm_multiOwnedRequired']
        }


    # language=Solidity
    _TEMPLATE = """
// Copyright (C) 2017-2018  MixBytes, LLC
// Licensed under the Apache License, Version 2.0 (the "License").
// You may not use this file except in compliance with the License.
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND (express or implied).
// Code taken from https://github.com/ethereum/dapp-bin/blob/master/wallet/wallet.sol
// Audit, refactoring and improvements by github.com/Eenae
// @authors:
// Gav Wood <g@ethdev.com>
// inheritable "property" contract that enables methods to be protected by requiring the acquiescence of either a
// single, or, crucially, each of a number of, designated owners.
// usage:
// use modifiers onlyowner (just own owned) or onlymanyowners(hash), whereby the same hash must be provided by
// some number (specified in constructor) of the set of owners (specified in the constructor, modifiable) before the
// interior is executed.
pragma solidity ^0.4.15;
contract multiowned {
	// TYPES
    // struct for the status of a pending operation.
    struct MultiOwnedOperationPendingState {
        // count of confirmations needed
        uint yetNeeded;
        // bitmap of confirmations where owner #ownerIndex's decision corresponds to 2**ownerIndex bit
        uint ownersDone;
        // position of this operation key in m_multiOwnedPendingIndex
        uint index;
    }
	// EVENTS
    event Confirmation(address owner, bytes32 operation);
    event Revoke(address owner, bytes32 operation);
    event FinalConfirmation(address owner, bytes32 operation);
    // some others are in the case of an owner changing.
    event OwnerChanged(address oldOwner, address newOwner);
    event OwnerAdded(address newOwner);
    event OwnerRemoved(address oldOwner);
    // the last one is emitted if the required signatures change
    event RequirementChanged(uint newRequirement);
	// MODIFIERS
    // simple single-sig function modifier.
    modifier onlyowner {
        require(isOwner(msg.sender));
        _;
    }
    // multi-sig function modifier: the operation must have an intrinsic hash in order
    // that later attempts can be realised as the same underlying operation and
    // thus count as confirmations.
    modifier onlymanyowners(bytes32 _operation) {
        if (confirmAndCheck(_operation)) {
            _;
        }
        // Even if required number of confirmations has't been collected yet,
        // we can't throw here - because changes to the state have to be preserved.
        // But, confirmAndCheck itself will throw in case sender is not an owner.
    }
    modifier validNumOwners(uint _numOwners) {
        require(_numOwners > 0 && _numOwners <= c_maxOwners);
        _;
    }
    modifier multiOwnedValidRequirement(uint _required, uint _numOwners) {
        require(_required > 0 && _required <= _numOwners);
        _;
    }
    modifier ownerExists(address _address) {
        require(isOwner(_address));
        _;
    }
    modifier ownerDoesNotExist(address _address) {
        require(!isOwner(_address));
        _;
    }
    modifier multiOwnedOperationIsActive(bytes32 _operation) {
        require(isOperationActive(_operation));
        _;
    }
	// METHODS
    // constructor is given number of sigs required to do protected "onlymanyowners" transactions
    // as well as the selection of addresses capable of confirming them (msg.sender is not added to the owners!).
    function multiowned(address[] _owners, uint _required)
        public
        validNumOwners(_owners.length)
        multiOwnedValidRequirement(_required, _owners.length)
    {
        assert(c_maxOwners <= 255);
        m_numOwners = _owners.length;
        m_multiOwnedRequired = _required;
        for (uint i = 0; i < _owners.length; ++i)
        {
            address owner = _owners[i];
            // invalid and duplicate addresses are not allowed
            require(0 != owner && !isOwner(owner) /* not isOwner yet! */);
            uint currentOwnerIndex = checkOwnerIndex(i + 1 /* first slot is unused */);
            m_owners[currentOwnerIndex] = owner;
            m_ownerIndex[owner] = currentOwnerIndex;
        }
        assertOwnersAreConsistent();
    }
    /// @notice replaces an owner `_from` with another `_to`.
    /// @param _from address of owner to replace
    /// @param _to address of new owner
    // All pending operations will be canceled!
    function changeOwner(address _from, address _to)
        external
        ownerExists(_from)
        ownerDoesNotExist(_to)
        onlymanyowners(keccak256(msg.data))
    {
        assertOwnersAreConsistent();
        clearPending();
        uint ownerIndex = checkOwnerIndex(m_ownerIndex[_from]);
        m_owners[ownerIndex] = _to;
        m_ownerIndex[_from] = 0;
        m_ownerIndex[_to] = ownerIndex;
        assertOwnersAreConsistent();
        OwnerChanged(_from, _to);
    }
    /// @notice adds an owner
    /// @param _owner address of new owner
    // All pending operations will be canceled!
    function addOwner(address _owner)
        external
        ownerDoesNotExist(_owner)
        validNumOwners(m_numOwners + 1)
        onlymanyowners(keccak256(msg.data))
    {
        assertOwnersAreConsistent();
        clearPending();
        m_numOwners++;
        m_owners[m_numOwners] = _owner;
        m_ownerIndex[_owner] = checkOwnerIndex(m_numOwners);
        assertOwnersAreConsistent();
        OwnerAdded(_owner);
    }
    /// @notice removes an owner
    /// @param _owner address of owner to remove
    // All pending operations will be canceled!
    function removeOwner(address _owner)
        external
        ownerExists(_owner)
        validNumOwners(m_numOwners - 1)
        multiOwnedValidRequirement(m_multiOwnedRequired, m_numOwners - 1)
        onlymanyowners(keccak256(msg.data))
    {
        assertOwnersAreConsistent();
        clearPending();
        uint ownerIndex = checkOwnerIndex(m_ownerIndex[_owner]);
        m_owners[ownerIndex] = 0;
        m_ownerIndex[_owner] = 0;
        //make sure m_numOwners is equal to the number of owners and always points to the last owner
        reorganizeOwners();
        assertOwnersAreConsistent();
        OwnerRemoved(_owner);
    }
    /// @notice changes the required number of owner signatures
    /// @param _newRequired new number of signatures required
    // All pending operations will be canceled!
    function changeRequirement(uint _newRequired)
        external
        multiOwnedValidRequirement(_newRequired, m_numOwners)
        onlymanyowners(keccak256(msg.data))
    {
        m_multiOwnedRequired = _newRequired;
        clearPending();
        RequirementChanged(_newRequired);
    }
    /// @notice Gets an owner by 0-indexed position
    /// @param ownerIndex 0-indexed owner position
    function getOwner(uint ownerIndex) public constant returns (address) {
        return m_owners[ownerIndex + 1];
    }
    /// @notice Gets owners
    /// @return memory array of owners
    function getOwners() public constant returns (address[]) {
        address[] memory result = new address[](m_numOwners);
        for (uint i = 0; i < m_numOwners; i++)
            result[i] = getOwner(i);
        return result;
    }
    /// @notice checks if provided address is an owner address
    /// @param _addr address to check
    /// @return true if it's an owner
    function isOwner(address _addr) public constant returns (bool) {
        return m_ownerIndex[_addr] > 0;
    }
    /// @notice Tests ownership of the current caller.
    /// @return true if it's an owner
    // It's advisable to call it by new owner to make sure that the same erroneous address is not copy-pasted to
    // addOwner/changeOwner and to isOwner.
    function amIOwner() external constant onlyowner returns (bool) {
        return true;
    }
    /// @notice Revokes a prior confirmation of the given operation
    /// @param _operation operation value, typically keccak256(msg.data)
    function revoke(bytes32 _operation)
        external
        multiOwnedOperationIsActive(_operation)
        onlyowner
    {
        uint ownerIndexBit = makeOwnerBitmapBit(msg.sender);
        var pending = m_multiOwnedPending[_operation];
        require(pending.ownersDone & ownerIndexBit > 0);
        assertOperationIsConsistent(_operation);
        pending.yetNeeded++;
        pending.ownersDone -= ownerIndexBit;
        assertOperationIsConsistent(_operation);
        Revoke(msg.sender, _operation);
    }
    /// @notice Checks if owner confirmed given operation
    /// @param _operation operation value, typically keccak256(msg.data)
    /// @param _owner an owner address
    function hasConfirmed(bytes32 _operation, address _owner)
        external
        constant
        multiOwnedOperationIsActive(_operation)
        ownerExists(_owner)
        returns (bool)
    {
        return !(m_multiOwnedPending[_operation].ownersDone & makeOwnerBitmapBit(_owner) == 0);
    }
    // INTERNAL METHODS
    function confirmAndCheck(bytes32 _operation)
        private
        onlyowner
        returns (bool)
    {
        if (512 == m_multiOwnedPendingIndex.length)
            // In case m_multiOwnedPendingIndex grows too much we have to shrink it: otherwise at some point
            // we won't be able to do it because of block gas limit.
            // Yes, pending confirmations will be lost. Dont see any security or stability implications.
            // TODO use more graceful approach like compact or removal of clearPending completely
            clearPending();
        var pending = m_multiOwnedPending[_operation];
        // if we're not yet working on this operation, switch over and reset the confirmation status.
        if (! isOperationActive(_operation)) {
            // reset count of confirmations needed.
            pending.yetNeeded = m_multiOwnedRequired;
            // reset which owners have confirmed (none) - set our bitmap to 0.
            pending.ownersDone = 0;
            pending.index = m_multiOwnedPendingIndex.length++;
            m_multiOwnedPendingIndex[pending.index] = _operation;
            assertOperationIsConsistent(_operation);
        }
        // determine the bit to set for this owner.
        uint ownerIndexBit = makeOwnerBitmapBit(msg.sender);
        // make sure we (the message sender) haven't confirmed this operation previously.
        if (pending.ownersDone & ownerIndexBit == 0) {
            // ok - check if count is enough to go ahead.
            assert(pending.yetNeeded > 0);
            if (pending.yetNeeded == 1) {
                // enough confirmations: reset and run interior.
                delete m_multiOwnedPendingIndex[m_multiOwnedPending[_operation].index];
                delete m_multiOwnedPending[_operation];
                FinalConfirmation(msg.sender, _operation);
                return true;
            }
            else
            {
                // not enough: record that this owner in particular confirmed.
                pending.yetNeeded--;
                pending.ownersDone |= ownerIndexBit;
                assertOperationIsConsistent(_operation);
                Confirmation(msg.sender, _operation);
            }
        }
    }
    // Reclaims free slots between valid owners in m_owners.
    // TODO given that its called after each removal, it could be simplified.
    function reorganizeOwners() private {
        uint free = 1;
        while (free < m_numOwners)
        {
            // iterating to the first free slot from the beginning
            while (free < m_numOwners && m_owners[free] != 0) free++;
            // iterating to the first occupied slot from the end
            while (m_numOwners > 1 && m_owners[m_numOwners] == 0) m_numOwners--;
            // swap, if possible, so free slot is located at the end after the swap
            if (free < m_numOwners && m_owners[m_numOwners] != 0 && m_owners[free] == 0)
            {
                // owners between swapped slots should't be renumbered - that saves a lot of gas
                m_owners[free] = m_owners[m_numOwners];
                m_ownerIndex[m_owners[free]] = free;
                m_owners[m_numOwners] = 0;
            }
        }
    }
    function clearPending() private onlyowner {
        uint length = m_multiOwnedPendingIndex.length;
        // TODO block gas limit
        for (uint i = 0; i < length; ++i) {
            if (m_multiOwnedPendingIndex[i] != 0)
                delete m_multiOwnedPending[m_multiOwnedPendingIndex[i]];
        }
        delete m_multiOwnedPendingIndex;
    }
    function checkOwnerIndex(uint ownerIndex) private pure returns (uint) {
        assert(0 != ownerIndex && ownerIndex <= c_maxOwners);
        return ownerIndex;
    }
    function makeOwnerBitmapBit(address owner) private constant returns (uint) {
        uint ownerIndex = checkOwnerIndex(m_ownerIndex[owner]);
        return 2 ** ownerIndex;
    }
    function isOperationActive(bytes32 _operation) private constant returns (bool) {
        return 0 != m_multiOwnedPending[_operation].yetNeeded;
    }
    function assertOwnersAreConsistent() private constant {
        assert(m_numOwners > 0);
        assert(m_numOwners <= c_maxOwners);
        assert(m_owners[0] == 0);
        assert(0 != m_multiOwnedRequired && m_multiOwnedRequired <= m_numOwners);
    }
    function assertOperationIsConsistent(bytes32 _operation) private constant {
        var pending = m_multiOwnedPending[_operation];
        assert(0 != pending.yetNeeded);
        assert(m_multiOwnedPendingIndex[pending.index] == _operation);
        assert(pending.yetNeeded <= m_multiOwnedRequired);
    }
   	// FIELDS
    uint constant c_maxOwners = 250;
    // the number of owners that must confirm the same operation before it is run.
    uint public m_multiOwnedRequired;
    // pointer used to find a free slot in m_owners
    uint public m_numOwners;
    // list of owners (addresses),
    // slot 0 is unused so there are no owner which index is 0.
    // TODO could we save space at the end of the array for the common case of <10 owners? and should we?
    address[256] internal m_owners;
    // index on the list of owners to allow reverse lookup: owner address => index in m_owners
    mapping(address => uint) internal m_ownerIndex;
    // the ongoing operations.
    mapping(bytes32 => MultiOwnedOperationPendingState) internal m_multiOwnedPending;
    bytes32[] internal m_multiOwnedPendingIndex;
}


contract Oracle is multiowned {

    event DataUpdate (uint256 ts);
    event Withdraw (address receiver, uint256 amount);
    event ChangePrice (uint256 price);

    uint256 public price;
    uint256 public lastDataUpdate;
    uint256 public nonce;

    %dataType% internal data;

    function Oracle(uint _signaturesRequired, uint256 _price)
        public
        multiowned(getInitialOwners(), _signaturesRequired)
    {
        price = _price;
    }

    function getInitialOwners() private pure returns (address[]) {
        %owners_code%
        return result;
    }

    modifier onlyForNonce(uint256 _nonce)
    {
        require(nonce == _nonce);
        _;
    }

    function newNonce()
        private
    {
        nonce = nonce + 1;
    }


    function setPrice(uint256 _price, uint256 _nonce)
        public
        onlyForNonce(_nonce)
        onlymanyowners(keccak256(msg.data))
    {
        price = _price;
        ChangePrice(_price);
        newNonce();
    }

    function updateData(%dataType% _data, uint256 _nonce)
        public
        onlyForNonce(_nonce)
        onlymanyowners(keccak256(msg.data))
    {
        data = _data;
        lastDataUpdate = now;
        DataUpdate(lastDataUpdate);
        newNonce();
    }

    function withdraw(address _receiver, uint256 _amount)
        public
        onlymanyowners(keccak256(msg.data))
    {
        require(_amount <= address(this).balance);
        _receiver.transfer(_amount);
        Withdraw(_receiver, _amount);
    }

    function getData()
        public
        payable
        returns (%dataType%)
    {
        require(msg.value == price);
        return data;
    }
}

contract OracleWrapper is Oracle(
    %signs_count%,
    %price%
) { }
    """
