/**  
 * This file guides Truffle through setting the inputs coming from the producer and giving the right deployment order of the contracts. 
 * Particularly, MovBitFreeToken is deployed first, as seen at line 22, while MovBitCrowdsale is deployed later, line 26: 
 * this order is given by the token address, one of the input of MovBitCrowdsale contract, which comes in existance only  
 * when deploying MovBitFreeToken. As it can be seen at line 27, the opening date-time of the crowdsale is set as default
 * at the time when the deployment is called plus 15 seconds. This has been our choice to solve a problem given by the fact that,
 * contrary on what was happening in Remix console, if not called the openSell function in MovBitFreeToken contract that
 * makes MovBitCrowdsale minter before the opening time, the last contract would not work and so the entire crowdsale would be gone.
 * In the folder newMigrations there is the template of this file.
 * The updateInput function in MovBitBackEnd.py file handles both the replacement of the existing 2_deploy_contracts.js in migrations folder
 * with the template and the insertion of the inputs of the producer.
*/

var MovBitToken = artifacts.require("MovBitToken");
var MovBitFreeToken = artifacts.require("MovBitFreeToken");
var MovBitCrowdsale = artifacts.require("MovBitCrowdsale");

// Input variables
const name="MovBit";
const symbol="MVB";
const decimals=18;
const closingTime=1608146820;
const ethRate=1;
const cap=100000000000000000000n;
const goal=10000000000000000000n;
const wallet="0x24EeDAC411658AffF10Ed26A5922f276eDa39860";

// Deployment (migration)
module.exports = function(deployer,network) {
    return deployer.deploy(MovBitFreeToken, name, symbol, decimals).then(function(instance){
        FreeTokenInstance = instance;
        const openingTime = Date.now()/1000|0+15;
        return deployer.deploy(MovBitCrowdsale, 
                               openingTime, closingTime,
                               ethRate, wallet, cap, 
                               FreeTokenInstance.addToken(), goal);
    });
};




