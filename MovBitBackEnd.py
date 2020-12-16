import os
import json
import shutil
import time
import subprocess
import re
from web3 import Web3, HTTPProvider
os.chdir(os.getcwd())

# Open a new bash window and run ganache-cli
os.system("ttab -w ganache-cli")
time.sleep(5) #necessary to give ganache the time to start before conneting to the port
# Connect to ganache-cli port
blockchain_address = 'http://127.0.0.1:8545'
# Client instance to interact with the blockchain
w3 = Web3(HTTPProvider(blockchain_address))

# Insert the input coming from the producer in the 2_deploy_contracts in migrations folder: 
# LOOK AT IT FOR MORE INFORMATION ABOUT HOW THE DEPLOYMNET WORKS!!!
def updateInput(name:str, symbol:str, decimals, closingTime:int, ethRate, cap:int, goal:int, wallet:str):
    try:
        os.remove(os.getcwd()+'/input.json')
    except OSError:
        pass

    data = {}
    data['input'] = {'name':name, 'symbol':symbol, 'closingTime':closingTime, 'cap':cap, 'goal':goal}
    with open('./newMigrations/input.json', 'w') as outfile:
        json.dump(data, outfile)
    os.remove(os.getcwd()+'/migrations/2_deploy_contracts.js')
    shutil.copy(os.getcwd()+'/newMigrations/2_deploy_contracts.js', os.getcwd()+'/migrations/2_deploy_contracts.js')
    os.system('cd migrations')
    os.system("sed -i -e 's/name=0/name=\"{}\"/g' './migrations/2_deploy_contracts.js'".format(name))
    os.system("sed -i -e 's/symbol=0/symbol=\"{}\"/g' './migrations/2_deploy_contracts.js'".format(symbol))
    os.system("sed -i -e 's/decimals=0/decimals={}/g' './migrations/2_deploy_contracts.js'".format(decimals))
    os.system("sed -i -e 's/closingTime=0/closingTime={}/g' './migrations/2_deploy_contracts.js'".format(closingTime))
    os.system("sed -i -e 's/ethRate=0/ethRate={}/g' './migrations/2_deploy_contracts.js'".format(ethRate))
    os.system("sed -i -e 's/cap=0/cap={}n/g' './migrations/2_deploy_contracts.js'".format(cap))
    os.system("sed -i -e 's/goal=0/goal={}n/g' './migrations/2_deploy_contracts.js'".format(goal))
    os.system("sed -i -e 's/wallet=0/wallet=\"{}\"/g' './migrations/2_deploy_contracts.js'".format(wallet))

    try:
        os.remove("./migrations/2_deploy_contracts.js-e")
    except OSError:
        pass

# The following function calls truffle which actually run the deployment of the contracts
# It creates also a temporary file with the information of the deployment which are necessary
# in the app.py file
def transact():
    os.system("sudo truffle migrate --reset > tmp")
    print(open('tmp', 'r').read())

# importAccount function imports some information which are going to be used in the web app:
# particularly it stores the address of the contract that generates the tokens, the address of
# the crowdsale contract, the wallet address of the producer and finally
# cap, goal, closing time and name inserted by the producer
def importAccount():
    output = open('tmp')
    s = output.read(40000)
    position1=[m.start() for m in re.finditer('contract address', s)]
    position2=[m.start() for m in re.finditer('account', s)]
    tokenAddress = s[position1[1]+21:position1[1]+21+42]
    crowdAddress = s[position1[2]+21:position1[2]+21+42]
    wallet = s[position2[2]+21:position2[2]+21+42]
    with open('./newMigrations/input.json') as f:
        data = json.load(f)
    cap = data['input']['cap']
    goal = data['input']['goal']
    cloTime = data['input']['closingTime']
    name = data['input']['name']
    return tokenAddress,crowdAddress, wallet, cap, goal, cloTime, name

# the following function connects web3 instance to the contracts
def connectContracts(addressContract,name):
    compiled_contract_path = f'./build/contracts/{name}.json'
    token_address = addressContract
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)
        contract_abi = contract_json['abi']
    return w3.eth.contract(address=token_address, abi=contract_abi)