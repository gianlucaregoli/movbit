## MovBit
### Blockchain-based movie production and streaming application

![image](https://drive.google.com/uc?export=view&id=1KoPhMH5x5I7Dh3OMji5oAlhNTezYePhf)

##### What is MovBit
The aim of MovBit is to give space to independent movie directors and screenwriters who are not able to find financial resources for their movies. On MovBit they can find the resources via crowdsale, in which investors can support the idea buying right-to-dividend tokens. Once, the movie is produced, consumers could buy the movie, generating a distributable positive cash flow. 
All the transactions are handled by blockchain-based smart contracts written in Solidity 

##### What you find here
The following repository contains a web-application (that can be launched locally) built with Python `flask` package, that is a simulation prototype of how the whole system would work. 

The program has been tested on MacOS and Linux, while we recommend to Windows users to download the Docker image at this link:

### How to install it

- We recommend to create a `virtual env`
- Install Node.js (more info here: https://nodejs.org/en/download/package-manager/)
- Run the following commands to install the necessary packages:
```
npm install -g truffle
npm install -g ganache-cli
npm install -g ttab
pip install -r requirements.txt
```

### Usage
If you use Linux, run in the folder:
```
sed -i -e 's/truffle migrate/sudo truffle migrate/g' './MovBitBackEnd.py'
rm MovBitBackEnd.py-e
python3 app.py
```
You will be asked to insert your password in one of the bashes opened

If you use Mac, run directly:
```
python3 app.py
```