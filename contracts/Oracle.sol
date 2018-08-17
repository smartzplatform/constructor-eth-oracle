pragma solidity ^0.4.20;

import '../library/contracts/ownership/multiowned.sol';

contract Oracle is multiowned {

    event DataUpdate (uint256 ts);
    event Withdraw (address receiver, uint256 amount);
    event ChangePrice (uint256 price);

    uint256 public price;
    uint256 public lastDataUpdate;
    uint256 public nonce;

    uint256 internal data;

    constructor(address[] _owners, uint _signaturesRequired, uint256 _price)
        public
        multiowned(_owners, _signaturesRequired)
    {
        price = _price;
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

    function updateData(uint256 _data, uint256 _nonce)
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
        returns (uint256)
    {
        require(msg.value == price);
        return data;
    }
}
