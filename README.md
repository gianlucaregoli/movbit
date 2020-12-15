## MovBit
#### De-centralized blockchain-based streaming application

- Recommended virtual env
- Install nodeJs (differentiate between Mac and Linux)
```
npm install -g truffle
npm install -g ganache-cli
npm install -g ttab
pip install -r requirements.txt
```
If use Linux, run in the folder:
```
sed -i -e 's/truffle migrate/sudo truffle migrate/g' './MovBitBackEnd.py'
rm MovBitBackEnd.py-e
```

If use Mac, run directly:
```
python3 app.py
```