const expectThrow = require('../node_modules/openzeppelin-solidity/test/helpers/expectThrow').expectThrow;
const expectEvent = require('../node_modules/openzeppelin-solidity/test/helpers/expectEvent');

const BigNumber = web3.BigNumber;
const chai =require('chai');
chai.use(require('chai-bignumber')(BigNumber));
chai.use(require('chai-as-promised')); // Order is important
chai.should();

const zeroAddr = '0x0000000000000000000000000000000000000000';

const Oracle = artifacts.require("Oracle");

//const getBalance = (address) => new Promise((resolve, reject) => web3.eth.getBalance((err, res) => if (err) reject(err) else resolve(parseFloat(res.toString(10)))));
const now = () => ((new Date().getTime() / 1000) | 0);
const withDefault = (value, def) => (value === undefined || value === null) ? def : value;

const contructorArgs = (args) => [
    withDefault(args.owners, [zeroAddr]),
    withDefault(args.singsRequired, 0),
    withDefault(args.price, web3.toWei('1')),
];

contract('Oracle', function(accounts) {
    const accts = {
        anyone: accounts[0],
        owner: accounts[1],
        owners: accounts.slice(1, 4)
    };

    const newInstance = async (args) => await Oracle.new(...contructorArgs(args), {from: accts.owner});

    const defaultArgs = {
        owners: accts.owners,
        singsRequired: 2,
        price: web3.toWei('1')
    };

    it('updateData', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});
        await inst.getData.call({from: accts.anyone, value: web3.toWei('1')})
            .should.eventually.be.bignumber.equal(data);

        await inst.nonce({from: accts.anyone})
            .should.eventually.be.bignumber.equal(nonce + 1);
    });

    it('updateData with invalid nonce', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let fakeNonce = 21313441;

        expectThrow(inst.updateData(data, fakeNonce, {from: accts.owners[1]}));
    });

    it('updateData with invalid owner', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        expectThrow(inst.updateData(data, nonce, {from: accts.anyone}));
    });


    it('setPrice', async function() {
        let inst = await newInstance(defaultArgs);
        let price = web3.toWei('5');

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.setPrice(price, nonce, {from: accts.owners[0]});
        await inst.setPrice(price, nonce, {from: accts.owners[1]});
        await inst.price({from: accts.anyone})
            .should.eventually.be.bignumber.equal(price);
    });

    it('setPrice with invalid nonce', async function() {
        let inst = await newInstance(defaultArgs);
        let price = web3.toWei('5');

        let fakeNonce = 21313441;

        await expectThrow(inst.setPrice(price, fakeNonce, {from: accts.owners[1]}));
    });

    it('setPrice with invalid owner', async function() {
        let inst = await newInstance(defaultArgs);
        let price = web3.toWei('5');

        let nonce = await inst.nonce({from: accts.anyone});

        await expectThrow(inst.setPrice(price, nonce, {from: accts.anyone}));
    });


    it('getData', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});
        await inst.getData.call({from: accts.anyone, value: web3.toWei('1')})
            .should.eventually.be.bignumber.equal(data);
    });

    it('getData with not enough payment', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});

        await expectThrow(inst.getData.call({from: accts.anyone, value: web3.toWei('0.99999')}))
    });

    it('getData with over payment', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});

        await expectThrow(inst.getData.call({from: accts.anyone, value: web3.toWei('1.00001')}))
    });


    it('withdraw', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});

        await inst.getData({from: accts.anyone, value: web3.toWei('1')});

        await inst.withdraw(accts.anyone, web3.toWei('1'), {from: accts.owners[1]});
        await expectEvent.inTransaction(inst.withdraw(accts.anyone, web3.toWei('1'), {from: accts.owners[2]}), 'Withdraw');
    });

    it('withdraw over balance', async function() {
        let inst = await newInstance(defaultArgs);
        let data = (Math.random() * 100000) | 0;

        let nonce = await inst.nonce({from: accts.anyone});

        await inst.updateData(data, nonce, {from: accts.owners[0]});
        await inst.updateData(data, nonce, {from: accts.owners[1]});

        await inst.getData({from: accts.anyone, value: web3.toWei('1')});

        await inst.withdraw(accts.anyone, web3.toWei('2'), {from: accts.owners[1]});
        await expectThrow(inst.withdraw(accts.anyone, web3.toWei('2'), {from: accts.owners[2]}));
    });
});
