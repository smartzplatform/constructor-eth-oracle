pragma solidity ^0.4.20;

import '../library/contracts/ownership/multiowned.sol';

contract Oracle is multiowned {

    event DataUpdate (uint256 ts);
    event Withdraw (address receiver, uint256 amount);
    event ChangePrice (uint256 price);

    uint256 public Price;
    uint256 public LastDataUpdate;
    uint256 public Nonce;

    uint256 internal Data;

    constructor(address[] owners, uint signaturesRequired, uint256 price)
        public
        multiowned(owners, signaturesRequired)
    {
        Price = price;
        LastDataUpdate = 0;
        Nonce = 0;
    }

    modifier onlyForNonce(uint256 nonce)
    {
        require(Nonce == nonce);
        _;
    }

    function newNonce()
        private
    {
        Nonce = Nonce + 1;
    }


    function setPrice(uint256 price, uint256 nonce)
        public
        onlyForNonce(nonce)
        onlymanyowners(keccak256(msg.data))
    {
        Price = price;
        ChangePrice(price);
        newNonce();
    }

    function updateData(uint256 data, uint256 nonce)
        public
        onlyForNonce(nonce)
        onlymanyowners(keccak256(msg.data))
    {
        Data = data;
        LastDataUpdate = now;
        DataUpdate(LastDataUpdate);
        newNonce();
    }

    function withdraw(address receiver, uint256 amount)
        public
        onlymanyowners(keccak256(msg.data))
    {
        require(amount <= address(this).balance);
        receiver.transfer(amount);
        Withdraw(receiver, amount);
    }


    function getData()
        public
        payable
        returns (uint256)
    {
        require(msg.value == Price);
        return Data;
    }
}
