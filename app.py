from flask import Flask, redirect, url_for, render_template, request, jsonify, g
import web3
from web3 import Web3, HTTPProvider
import MovBitBackEnd as deploy
import os
import datetime
import pandas as pd
import cryptocompare
import random

os.chdir(os.getcwd())

blockchain_address = 'http://127.0.0.1:8545'
w3 = Web3(HTTPProvider(blockchain_address))

app = Flask(__name__)

#Define variable available for all request
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

exchange_rate = cryptocompare.get_price('ETH',curr='USD')['ETH']['USD']

## FUNCTIONS

def convertToUnix(s):
    date,time = s.split(" ")
    day,month,year = date.split("/")
    hour,minute = time.split(":")
    return int(datetime.datetime(int(year),int(month),int(day),\
         int(hour), int(minute)).timestamp())

def convertToDate(s):
    timestamp = datetime.datetime.fromtimestamp(int(s))
    date = timestamp.strftime("%d/%m/%Y %H:%M")
    return date

def updateBalances():
    # app.balances = {}
    for name in app.name_accounts:
        app.balances[name] = w3.eth.getBalance(app.accounts[name])
    print(app.balances)

## APP
@app.route("/" , methods=['GET', 'POST'])
def home():
    return render_template("index.html", content='Testing')

@app.route("/screenwriter.html")
def home_1():
    return render_template("screenwriter.html", content = "Testing", rate=exchange_rate)

@app.route("/about.html")
def about():
    return render_template("about.html", content = "Testing")

@app.route("/freetoken.html")
def freetoken():
    return render_template("freetoken.html", content="Testing", rate=exchange_rate)

@app.route("/investor.html")
def investor():
    return render_template("investor.html", content="Testing", rate=exchange_rate, goal=app.goal/(10**18), 
                                            movie=app.name, clDate=convertToDate(app.cloTime))

@app.route("/consumer.html")
def consumer():
    return render_template("consumer.html", content="Testing", movie=app.name)

@app.route("/ethraised.html")
def ethRaised():
    return render_template("ethraised.html", content="Testing", movie=app.name,
                                             clDate=convertToDate(app.cloTime))

@app.route("/accounts.html")
def accountsBalances():
    updateBalances()
    df_balances = pd.DataFrame.from_dict(app.balances, orient="index").reset_index()
    df_balances = df_balances.rename(columns={'index':'Account', 0:'Balance (ETH)'})
    df_balances['Balance (ETH)'] = df_balances['Balance (ETH)'].astype(float)/(10**18)        
    df_balances = df_balances.to_html(classes='table table-striped table-hover', header='true', justify='left')
    return render_template("accounts.html", content="Testing", data=df_balances)


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
    print(accounts,cap,goal,cloTime, name)

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

@app.route("/freetoken.html", methods=['GET','POST'])
def addBeneficiary():
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

    try:
        address = app.accounts[str(request.form['inputAddress3'])]
        balance = app.crowdContract.functions.Royalties(address).call()
        print(balance)
        return render_template('freetoken.html', show_result = True, message = 'The tokens assigned are: {}'.format(balance/(10**18)),
        rate=exchange_rate)
    except:
        print('No check!')

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

    try:
        address = app.accounts[str(request.form['inputAddress4'])]
        balance = app.crowdContract.functions.balanceOf(str(address)).call()
        print(balance)
        return render_template('freetoken.html', show_result = True, message = 'The tokens in the selected account are: {}'.format(balance/(10**18)),
        rate=exchange_rate)
    except:
        print('No check!')

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


@app.route("/investor.html", methods=['GET','POST'])
def invest():
    try:
        address = app.accounts[str(request.form['inputAddress10'])]
        amount = request.form['inputEther10']
        amount = float(amount)*(10**18)
        
        buy_toks = app.crowdContract.functions.buyTokens(address)
        tx_hash = buy_toks.transact({"from": address, "value": int(amount)})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Transaction Done!',
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Not allow buy tokens')

    try:
        address = app.accounts[str(request.form['inputAddress11'])]
        
        claim_Refund = app.crowdContract.functions.claimRefund(address)
        tx_hash = claim_Refund.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Refund Done!',
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Not allow refund')

    try:
        address = app.accounts[str(request.form['inputAddress12'])]
        
        finalize_Crowdsale = app.crowdContract.functions.finalize()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'The contract has been finalized!',
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Finalize not allowed')

    try:
        address = app.accounts[str(request.form['inputAddress13'])]
        
        fix_Balance = app.crowdContract.functions.fixTimeBalance()
        tx_hash = fix_Balance.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'The balance has been fixed!',
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Balance already fixed')

    try:
        address = app.accounts[str(request.form['inputAddress14'])]
        
        claim_Dividend = app.crowdContract.functions.claimDividend(address)
        tx_hash = claim_Dividend.transact({"from": address})
        print(tx_hash)
        return render_template('investor.html', show_result = True, message = 'Dividend claimed!',
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Dividend not claimed')

    try:
        address = app.accounts[str(request.form['inputAddress15'])]
        
        freeToken = app.crowdContract.functions.freeTokenAmount().call()
        totalToken = app.crowdContract.functions.totalAmountToken().call()
        ratio = round(freeToken/totalToken,2)
        return render_template('investor.html', show_result = True, message = 'Free tokens/total tokens ratio is: {}'.format(ratio),
        rate=exchange_rate, goal=app.goal/(10**18))
    except:
        print('Free token ratio not found')

    
    return render_template('investor.html', show_warning = True, message = 'Try again!', rate=exchange_rate, goal=app.goal/(10**18))

@app.route("/consumer.html", methods=['GET','POST'])
def watch():
    try:
        address = app.accounts[str(request.form['inputAddress20'])]
        price = 5*(10**18)
        
        buy_film = app.crowdContract.functions.buyFilm()
        tx_hash = buy_film.transact({"from": address,"value": int(price)})
        print(tx_hash)
        return render_template('consumer.html', show_result = True, show_video = True, message = 'Start watch the movie!')
    except:
        print('Not purchased')

    return render_template('consumer.html', show_warning = True, message = 'Try again!')


@app.route("/ethraised.html", methods=['GET','POST'])
def crowdsaleControl():
    try:
        address = app.accounts[str(request.form['inputAddress16'])]
        wei_raised = app.crowdContract.functions.weiRaised().call()
        return render_template('ethraised.html', show_result = True, show_video = True, message = f'ETH Raised: {round(int(wei_raised)/(10**18),3)}')
    except:
        print('Not wei Raised!')

    try:
        address = app.accounts[str(request.form['inputAddress31'])]
        finalize_Crowdsale = app.crowdContract.functions.finalize()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('ethraised.html', show_result = True, message = 'The contract has been finalized!')
    except:
        print('Finalize not allowed')

    try:
        address = app.accounts[str(request.form['inputAddress32'])]
        finalize_Crowdsale = app.crowdContract.functions.filmUploaded()
        tx_hash = finalize_Crowdsale.transact({"from": address})
        print(tx_hash)
        return render_template('ethraised.html', show_result = True, message = 'Our community can now buy your movie!')
    except:
        print('Film not uploaded yet!')

    return render_template('ethraised.html', show_warning = True, message = 'Try again!')



if __name__ == "__main__":
    app.run(debug=True)