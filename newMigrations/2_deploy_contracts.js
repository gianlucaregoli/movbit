var MovBitToken = artifacts.require("MovBitToken");
var MovBitFreeToken = artifacts.require("MovBitFreeToken");
var MovBitCrowdsale = artifacts.require("MovBitCrowdsale");

// Input variables
const name=0;
const symbol=0;
const decimals=0;
const closingTime=0;
const ethRate=0;
const cap=0;
const goal=0;
const wallet=0;

// Migration
module.exports = function(deployer,network,accounts) {
    return deployer.deploy(MovBitFreeToken, name, symbol, decimals).then(function(instance){
        FreeTokenInstance = instance;
        const openingTime = Date.now()/1000|0+15;
        return deployer.deploy(MovBitCrowdsale, 
                               openingTime, closingTime,
                               ethRate, wallet, cap, 
                               FreeTokenInstance.addToken(), goal);

    });
};




