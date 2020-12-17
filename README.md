## MovBit
### Blockchain-based movie production and streaming application

![image](https://drive.google.com/uc?export=view&id=1KoPhMH5x5I7Dh3OMji5oAlhNTezYePhf)

##### What is MovBit
The aim of MovBit is to give space to independent movie directors and screenwriters who are not able to find financial resources for their movies. On MovBit they can find the resources via crowdsale, in which investors can support the idea buying right-to-dividend tokens. Once, the movie is produced, consumers could buy the movie, generating a distributable positive cash flow. 
All the transactions are handled by blockchain-based smart contracts written in Solidity 

##### What you find here
The following repository contains a web-application (that can be launched locally) built with Python `flask` package, that is a simulation prototype of how the whole system would work.

The repo is structured as follow:
- `contracts` contains all the Solidity code;
- `migrations` includes the files necessary for the local deployment of the contracts;
- `newMigrations` stores the template of the deployment file;
- `templates` includes all the html files for the web-app;
- `truffle-config.js` is a required file by truffle for the deployment;
- `MovBitBackEnd.py` contains functions as support to `app.py`;
- `app.py` is the main file.

We recommend to go through the code by looking at `app.py` and its dependencies reported in the comments and referring to `MovBitCrowdsale.sol` in the "contracts" folder for the functions written in Solidity.

The program has been tested on MacOS and Linux, while we recommend to Windows users to download the Docker image at this link:
https://hub.docker.com/repository/docker/simone97/movbit

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
python3 app.py
```
You will be asked to insert your password in one of the bashes opened

If you use Mac, run directly:
```
python3 app.py
```

### Demo

Here you can find a 5 minutes video that explains how the web-app works with an example:
https://www.dropbox.com/s/3xgqpu4kiats9fd/MovBit-Demo.mp4?dl=0