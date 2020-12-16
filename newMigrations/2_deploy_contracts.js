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
const name=0;
const symbol=0;
const decimals=0;
const closingTime=0;
const ethRate=0;
const cap=0;
const goal=0;
const wallet=0;

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




