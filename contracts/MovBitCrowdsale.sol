pragma solidity ^0.5.0;

import "./source/CappedCrowdsale.sol";
import "./source/RefundableCrowdsale.sol";
import "./source/MintedCrowdsale.sol";
import "./source/ERC20Mintable.sol";
import "./source/ERC20Detailed.sol";
import "./source/ERC20Burnable.sol";
import "./source/Ownable.sol";

contract MovBitToken is ERC20Mintable, ERC20Detailed, ERC20Burnable{
    
    constructor (string memory _name, string memory _symbol, uint8 _decimals) public ERC20Detailed(_name, _symbol, _decimals) {
        _mint(msg.sender, 0);
    }
}

contract MovBitFreeToken is Ownable {
    
    using SafeMath for uint256;
    using SafeMath for int;

    MovBitToken token;
    
    //uint256 public initialSupply;
    address public admin;
    address public addToken;
    
    constructor (string memory _name, string memory _symbol, uint8 _decimals) public {
        token = new MovBitToken(_name, _symbol, _decimals);
        addToken = address(token);
        admin = msg.sender;
    }

    function openSell(address _address) public onlyOwner {
        token.addMinter(_address);
    }
    
}

    //CappedCrowdsale - sets a max boundary for raised funds
    //RefundableCrowdsale - set a min goal to be reached and returns funds if it's not met
    //MintedCrowdsale - assumes the token can be minted by the crowdsale, which does so when receiving purchases.

contract MovBitCrowdsale is CappedCrowdsale, RefundableCrowdsale, MintedCrowdsale, Ownable {

    using SafeMath for int;
    using SafeMath for uint256;
    using Address for address payable;
    
    //MAPPING FOR REFUND DIVIDEND
    mapping(address => uint256) public _deposits;
    
    //Set the state variables for FREE TOKENS ///////////////
    mapping (address => int) public Royalties;
    address[] public indexAddress;
    
    int256 public freeTokensAssign;
    uint256 public freetokenSold;
    
    uint256 public initialSupply;
    address public admin;
    address public addToken;
    bool public endFree;
    /////////////////////////////////////////////////////////

    MovBitToken private tokenContract;
    uint256 exchange_rate;
    uint256 public token_balance;
    
    // FOR DIVIDEND /////////////////////////////////////////
    uint256 public actualBalance;
    uint256 public tokenSold;
    uint256 weiToSend;
    uint256 payment;
    uint256 amountDividend;
    uint256 public timeDividend;
    uint256 public fixBalance;
    uint256 amountToken;
    bool public filmUpload;
    
    uint256 public freeTokenSold;
    
    event Withdrawn(address indexed payee, uint256 weiAmount);
    
    mapping (address => uint256) public claimAddress;
    ///////////////////////////////////////////////////////////
    
    constructor (uint256 openingTime, uint256 closingTime, uint256 rate, address payable wallet, uint256 cap, MovBitToken token, uint256 goal) public 
        Crowdsale(rate, wallet, token)
        CappedCrowdsale(cap)
        TimedCrowdsale(openingTime, closingTime)
        RefundableCrowdsale(goal) {
            require(goal <= cap, "SampleCrowdSale: goal is greater than cap");
            tokenContract = token;
            exchange_rate = rate;
            timeDividend = 0;
            filmUpload = false;
        }
    
    function balance_contract() view public returns(uint256) {
        return address(this).balance;
    }
    
    function balance_account() view public returns(uint256) {
        return msg.sender.balance;
    }
    
    ////////////////////////////////////////////////////////////////////////////
    //Check number of tokens sold
    function depositsOf(address payee) public view returns (uint256) {
        return _deposits[payee];
    }

    //Add address and deposit to the mapping
    function deposit(address payee, uint256 _tokenAmount) internal {
        _deposits[payee] = _deposits[payee].add(_tokenAmount);
    }

    function _postValidatePurchase(address beneficiary, uint256 weiAmount) internal view {
        require(endFree == true, "Free Token PHASE still open, You have to close it!");
        super._postValidatePurchase(beneficiary, weiAmount);
    }

    function _updatePurchasingState(address beneficiary, uint256 weiAmount) internal {
        super._updatePurchasingState(beneficiary, weiAmount);
        uint256 tokensAmount = weiAmount.mul(Crowdsale.rate());
        deposit(beneficiary,tokensAmount);
    }
    
    // HANDLE FREE TOKENS //////////////////////////////////////////////////////
    
    function addTokens(uint256 _amount) public onlyOwner {
        require(endFree == false, "Already closed the free tokens!");
        tokenContract.mint(address(this), _amount);
    }
    
    function burnTokens(uint256 _amount) public onlyOwner {
        require(endFree == false, "Already closed the free tokens!");
        tokenContract.burn(_amount);
    }
    
    function balanceOf(address _address) public view returns (uint256) {
        return tokenContract.balanceOf(_address);
    }

    //Add Royalties
    
    function add_royalties(address _add_id, int _num_tokens) public onlyOwner {
        Royalties[_add_id] += _num_tokens;
        require(Royalties[_add_id]>=0);
        freeTokensAssign += _num_tokens;
        indexAddress.push(_add_id);
    }
    
    //Set to zero some free account tokens that have been set
    
    function set_to_zero (address _add_id) public onlyOwner {
        require(Royalties[_add_id]>=0, "It is already at zero");
        int balance = Royalties[_add_id];
        Royalties[_add_id] -= balance;
        freeTokensAssign -= balance;
    }
    
    //Pay out all the free tokens
    
    function pay_out_free() payable public onlyOwner{
        require(endFree == false, "You cannot send token anymore!");
        tokenContract.mint(address(this),uint256(freeTokensAssign));
        freeTokensAssign -= freeTokensAssign;
        // ADD A REQUIRE NOT TO LOOP IN CASE THE DICTIONARY VALUES ARE ZERO
        for (uint i=0; i<indexAddress.length; i++) { //not good, find a better way to do it
            tokenContract.transfer(indexAddress[i], uint256(Royalties[indexAddress[i]]));
            freetokenSold += uint256(Royalties[indexAddress[i]]);
            deposit(indexAddress[i],uint256(Royalties[indexAddress[i]]));
            Royalties[indexAddress[i]] -= Royalties[indexAddress[i]];
        }
    }
    
    function allowCrowdsale() public onlyOwner {
        require(endFree == false, "Already closed the free token phase!");
        tokenContract.burn(tokenContract.balanceOf(address(this)));
        endFree = true;
    }
    
    function buyFilm() external payable { //insert for the WebApp
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed!");
        require(filmUpload == true, "Film not yet uploaded!");
    }

    function returnAddress() view public returns(address){
        return msg.sender;
    }
    
    function balanceToken() view public returns(uint256){
        return tokenContract.balanceOf(address(this));
    }

    function freeTokenAmount() view public returns(uint256){
        return freetokenSold;
    }

    function totalAmountToken() view public returns(uint256){
        return SafeMath.add(Crowdsale.weiRaised().mul(Crowdsale.rate()),freetokenSold);
    }
    
    function filmUploaded() public onlyOwner{
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed yet!");
        filmUpload = true;
    }

    function fixTimeBalance() public {
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed yet!");
        require(filmUpload == true, "Film not yet uploaded!");
        require((block.timestamp-timeDividend)>=52 weeks || timeDividend == 0, "Not one year since last call!");
        timeDividend = block.timestamp;
        fixBalance = address(this).balance;  
    }
    
    function claimDividend(address payable payee) public {
        require(fixBalance != 0, "No balance has been fixed!");
        require(filmUpload == true, "Film not yet uploaded!");
        require(claimAddress[payee] != timeDividend, "Dividend already claimed!");
        
        tokenSold = SafeMath.add(Crowdsale.weiRaised().mul(Crowdsale.rate()),freetokenSold);
        amountDividend = SafeMath.mul(_deposits[payee],fixBalance);
        weiToSend = SafeMath.div(amountDividend,tokenSold);
        
        payee.transfer(weiToSend);
        
        claimAddress[payee] = timeDividend;

        emit Withdrawn(payee, weiToSend);
    }
}