import os
import web3
import random
import datetime
import cryptocompare
import pandas as pd
import MovBitBackEnd as deploy
from web3 import Web3, HTTPProvider
from flask import Flask, redirect, url_for, render_template, request, jsonify, g

os.chdir(os.getcwd())
app = Flask(__name__)

# Connect to ganache-cli port
blockchain_address = 'http://127.0.0.1:8545'
w3 = Web3(HTTPProvider(blockchain_address))

# Define variable available for all requests and create the mapping of the ganache accounts
app.tokenContract = 0
app.crowdContract = 0
app.wallet = 0
app.cap = 0
app.goal = 0
app.cloTime = 0
app.balances = {}
app.name = ''
accounts = []
for i in range(10):
    accounts.append(w3.eth.accounts[i])
app.name_accounts = ['Producer','Collaborator 1', 'Collaborator 2', 'Investor 1', 'Investor 2',\
                    'Investor 3', 'Investor 4', 'Consumer 1', 'Consumer 2', 'Consumer 3']
app.accounts = {app.name_accounts[i]:accounts[i] for i in range(10)}

exchange_rate = cryptocompare.get_price('ETH',curr='USD')['ETH']['USD'] # used to have real time eth/dollar exchange rate

## FUNCTIONS
# Convert from usual date-time format to unix one which is read by the MovBitCrowdsale contract 
def convertToUnix(s):
    date,time = s.split(" ")
    day,month,year = date.split("/")
    hour,minute = time.split(":")
    return int(datetime.datetime(int(year),int(month),int(day),\
         int(hour), int(minute)).timestamp())

# Convert from unix date-time format to usal one
def convertToDate(s):
    timestamp = datetime.datetime.fromtimestamp(int(s))
    date = timestamp.strftime("%d/%m/%Y %H:%M")
    return date

# Update balances of the accounts table
def updateBalances():
    for name in app.name_accounts:
        app.balances[name] = w3.eth.getBalance(app.accounts[name])

# assignAddress is called when the producer deploys the contracts by filling the input and clicking START on the home page:
# the scope of it is importing in this file some input of the producer and the addresses of the deployed contracts.
# This function calls importAccount and connectContracts in the MovBitBackEnd.py so refers to this last file to better 
# understand what they does.
def assignAddress():
    tokenAddress,crowdAddress,wallet,cap,goal,cloTime, name = deploy.importAccount()
    tokenContract = deploy.connectContracts(tokenAddress,'MovBitFreeToken')
    crowdContract = deploy.connectContracts(crowdAddress,'MovBitCrowdsale')
    assert str(type(tokenContract))=="<class 'web3._utils.datatypes.Contract'>"
    assert str(type(crowdContract))=="<class 'web3._utils.datatypes.Contract'>"
    app.tokenContract = tokenContract
    app.crowdContract = crowdContract
    app.wallet = str(wallet)
    app.cap = cap
    app.goal = goal
    app.cloTime = cloTime
    app.name = name

## APP REQUESTS
# Connect the home page
@app.route("/")
def home():
    return render_template("index.html", content='Testing')
# Connect the Start Project page where the producer inserts the input of the contracts
@app.route("/screenwriter.html")
def home_1():
    return render_template("screenwriter.html", content = "Testing", rate=exchange_rate)
# Connect the About page
@app.route("/about.html")
def about():
    return render_template("about.html", content = "Testing")
# Connect the Free Tokens page where the producer handles the tokens to the collaborators
@app.route("/freetoken.html")
def freetoken():
    return render_template("freetoken.html", content="Testing", rate=exchange_rate)
# Connect the Invest page of the investor
@app.route("/investor.html")
def investor():
    return render_template("investor.html", content="Testing", rate=exchange_rate, goal=app.goal/(10**18), 
                                            movie=app.name, clDate=convertToDate(app.cloTime))
# Connect the Watch page where the consumer buys the film
@app.route("/consumer.html")
def consumer():
    return render_template("consumer.html", content="Testing", movie=app.name)
# Connect the Producer Dashboard page
@app.route("/ethraised.html")
def ethRaised():
    return render_template("ethraised.html", content="Testing", movie=app.name,
                                             clDate=convertToDate(app.cloTime))
# Connect the Accounts page where reported the ganache accounts
@app.route("/accounts.html")
def accountsBalances():
    updateBalances()
    df_balances = pd.DataFrame.from_dict(app.balances, orient="index").reset_index()
    df_balances = df_balances.rename(columns={'index':'Account', 0:'Balance (ETH)'})
    df_balances['Balance (ETH)'] = df_balances['Balance (ETH)'].astype(float)/(10**18)        
    df_balances = df_balances.to_html(classes='table table-striped table-hover', header='true', justify='left')
    return render_template("accounts.html", content="Testing", data=df_balances)

# inputDeploy is the bridge between the gui and the actual deployment of the contracts through truffle:
# it first converts the formats and the types of the inputs coming from the producer to the right format
# asked by the MovBitCrowdsale contract. The exchange value against ether of each token has been fixed to 1,
# so token value is one Wei, and also the number of decimals is fixed to 18: we have handled all the number conversions.
# Then it calls "transact" (located in MovBitBackEnd.py) to run the deployment and assignAddress to have
# back some information as described above. Finally, it assigns to the Crowdsale contract the role of minter:
# this is necessary for the crowdsale to work (more information on 2_deploy_contracts.js and MovBitCrowdsale.sol)
@app.route("/screenwriter.html", methods=['GET','POST'])
def inputDeploy():
    tName = request.form['inputName']
    tSymbol = request.form['inputSymbol']
    cloTime = request.form['inputClosingTime']
    cap = request.form['inputCap']
    goal = request.form['inputGoal']
    name_account = request.form['inputWallet']
    wallet = app.accounts[str(name_account)]

    cap = float(cap) * (10**18)
    goal = float(goal) * (10**18)
    cloTime = convertToUnix(cloTime)

    w3.eth.defaultAccount = str(wallet)
    deploy.updateInput(str(tName), str(tSymbol), 18 , int(cloTime), 1, int(cap), int(goal), str(wallet))
    deploy.transact()

    assignAddress()
    add_Minter = app.tokenContract.functions.openSell(app.crowdContract.address)
    add_Minter.transact({"from": wallet})

    return render_template("screenwriter.html", show_modal=True, rate=exchange_rate)

# NOTE: all the form of the web app has an input even though in few of them is not necessary;
# this is due to the fact that we were not able to connect flask route with the html buttons but
# only to the input field. This should be improved!

# Below all the try-except that permits to the producer to send free tokens to his collaborators.
# For more information about the smart contract functions refers to MovBitCrowdsale.sol
@app.route("/freetoken.html", methods=['GET','POST'])
def addBeneficiary():
    # Add collaborator to the mapping with the assigned tokens
    try:
        address = app.accounts[str(request.form['inputAddress1'])]
        amount = request.form['inputEther1']

        realAmount = float(amount) * (10**18)
        add_Royalties = app.crowdContract.functions.add_royalties(str(address),int(realAmount))
        tx_hash = add_Royalties.transact({"from": app.wallet})
        print(tx_hash)
        return render_template('freetoken.html', show_result = True, message = 'The beneficiary has been added to the mapping!',
        rate=exchange_rate)
    except:
        print('Not adding!')
    # Remove tokens already assigned to a collaborator
    try:
        address_ = app.accounts[str(request.form['inputAddress2'])]
        amount_ = request.form['inputEther2']

        realAmount_ = - float(amount_) * (10**18)
        add_Royalties = app.crowdContract.functions.add_royalties(str(address_),int(realAmount_))
        tx_hash = add_Royalties.transact({"from": app.wallet})
        print(tx_hash)
        return render_template('freetoken.html', show_result = True, message = 'The beneficiary has been removed correctly!',
        rate=exchange_rate)
    except:
        print('Not removing!')
    # Check the amount of tokens assigned to a collaborator
    try:
        address = app.accounts[str(request.form['inputAddress3'])]
        balance = app.crowdContract.functions.Royalties(address).call()
        print(balance)
        return render_template('freetoken.html', show_result = True, message = 'The tokens assigned are: {}'.format(balance/(10**18)),
        rate=exchange_rate)
    except:
        print('No check!')
    # Actually pay out all the free tokens assigned
    try:
        address = app.accounts[str(request.form['inputAddress7'])]
        if address == str(app.wallet):
            pay_out_free = app.crowdContract.functions.pay_out_free()
            tx_hash = pay_out_free.transact({"from": app.wallet})
            print(tx_hash)
            return render_template('freetoken.html', show_result = True, message = 'All the beneficiaries received the tokens!',
            rate=exchange_rate)
    except:
        print('Not pay out free!')
    # Check the balance of the inserted accounts
    try:
        address = app.accounts[str(request.form['inputAddress4'])]
        balance = app.crowdContract.functions.balanceOf(str(address)).call()
        print(balance)
        return render_template('freetoken.html', show_result = True, message = 'The tokens in the selected account are: {}'.format(balance/(10**18)),
        rate=exchange_rate)
    except:
        print('No check!')
    # The producer, once finieshed to remunerate the collaborators, call this function to start the actual crowdsale
    try:
        address = app.accounts[str(request.form['inputAddress8'])]
        if address == str(app.wallet):
            allow_Crowdsale = app.crowdContract.functions.allowCrowdsale()
            tx_hash = allow_Crowdsale.transact({"from": app.wallet})
            print(tx_hash)
            return render_template('freetoken.html', show_crowdsale = True, rate=exchange_rate)
    except:
        print('Not allow crowdsale')

    return render_template("freetoken.html", show_warning = True, message='Try again!', rate=exchange_rate)

# Below all the try-except that permits to the investor to buy tokens, claim refund and claim the dividend.
@app.route("/investor.html", methods=['GET','POST'])
def invest():
    # Buy tokens
    try:
        address = app.accounts[str(request.form['inputAddress10'])]
        amount = request.form['inputEther10']
        amount = float(amount)*(10**18)
        
        buy_toks = app.crowdContract.functions.buyTokens(address)
        tx_hash = buy_toks.transact({"from": address, "value": int(amount)})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Transaction Done!',
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Not allow buy tokens')
    # Claim refund if the goal is not reached
    try:
        address = app.accounts[str(request.form['inputAddress11'])]
        
        claim_Refund = app.crowdContract.functions.claimRefund(address)
        tx_hash = claim_Refund.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Refund Done!',
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Not allow refund')
    # Finalize the contract and two possible paths:
    # - goal reached and all the ether inside the crodwsale contract goes to the account of the producer
    # - goal not reached and investors can claim their ether back
    try:
        address = app.accounts[str(request.form['inputAddress12'])]
        
        finalize_Crowdsale = app.crowdContract.functions.finalize()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'The contract has been finalized!',
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Finalize not allowed')
    # Fix the amount of ether inside the crowdsale contract in a certain point in time and based on this amount
    # investors have their dividend (this functions can be called once a year by anyone)
    try:
        address = app.accounts[str(request.form['inputAddress13'])]
        
        fix_Balance = app.crowdContract.functions.fixTimeBalance()
        tx_hash = fix_Balance.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'The balance has been fixed!',
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Balance already fixed')
    # Claim dividend one a year
    try:
        address = app.accounts[str(request.form['inputAddress14'])]
        
        claim_Dividend = app.crowdContract.functions.claimDividend(address)
        tx_hash = claim_Dividend.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Dividend claimed!',
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Dividend not claimed')
    # Check the proportion of free tokens against the total amount of tokens that has been bought
    try:
        address = app.accounts[str(request.form['inputAddress15'])]
        
        freeToken = app.crowdContract.functions.freeTokenAmount().call()
        totalToken = app.crowdContract.functions.totalAmountToken().call()
        ratio = round(freeToken/totalToken,2)
        return render_template('investor.html', show_result = True, message = 'Free tokens/total tokens ratio is: {}'.format(ratio),
        rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Free token ratio not found')

    return render_template('investor.html', show_warning = True, message = 'Try again!', 
                rate=exchange_rate, goal=app.goal/(10**18), movie=app.name,clDate=convertToDate(app.cloTime))

# Below the try-except that permits to the consumer to buy the Film
@app.route("/consumer.html", methods=['GET','POST'])
def watch():
    try:
        address = app.accounts[str(request.form['inputAddress20'])]
        price = 5*(10**18)
        
        buy_film = app.crowdContract.functions.buyFilm()
        tx_hash = buy_film.transact({"from": address,"value": int(price)})
        print(tx_hash)
        return render_template('consumer.html', show_result = True, show_video = True, message = 'Start watch the movie!',
                                movie=app.name)
    except:
        print('Not purchased')

    return render_template('consumer.html', show_warning = True, message = 'Try again!',
                            movie=app.name)

# Below the try-except that permits to the producer to check how the ether raised is going and confirm that the film has been uploaded
@app.route("/ethraised.html", methods=['GET','POST'])
def crowdsaleControl():
    # Check the amount of ether raised
    try:
        address = app.accounts[str(request.form['inputAddress16'])]
        wei_raised = app.crowdContract.functions.weiRaised().call()
        return render_template('ethraised.html', show_result = True, show_video = True,
                             message = f'ETH Raised: {round(int(wei_raised)/(10**18),3)}',
                             movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Not wei Raised!')
    # Also the producer can finalize the contract
    try:
        address = app.accounts[str(request.form['inputAddress31'])]
        finalize_Crowdsale = app.crowdContract.functions.finalize()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('ethraised.html', show_result = True, message = 'The contract has been finalized!',
                                            movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Finalize not allowed')
    # The producer allow consumer to buy film confirming that it has been uploaded on the platform
    try:
        address = app.accounts[str(request.form['inputAddress32'])]
        finalize_Crowdsale = app.crowdContract.functions.filmUploaded()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('ethraised.html', show_result = True, message = 'Our community can now buy your movie!',
                                    movie=app.name,clDate=convertToDate(app.cloTime))
    except:
        print('Film not uploaded yet!')

    return render_template('ethraised.html', show_warning = True, message = 'Try again!',
                            movie=app.name,clDate=convertToDate(app.cloTime))

if __name__ == "__main__":
    app.run()