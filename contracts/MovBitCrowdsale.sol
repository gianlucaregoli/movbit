pragma solidity ^0.5.0;

import "./source/CappedCrowdsale.sol";
import "./source/RefundableCrowdsale.sol";
import "./source/MintedCrowdsale.sol";
import "./source/ERC20Mintable.sol";
import "./source/ERC20Detailed.sol";
import "./source/ERC20Burnable.sol";
import "./source/Ownable.sol";

// The following three smart contracts contain more functions and variables than the one needed for movbit app

contract MovBitToken is ERC20Mintable, ERC20Detailed, ERC20Burnable{
    /**
     * This token has been created using OpenZeppelin library v 2.5 (located in folder source)
     * It is mintable and burnable even though for movbit app only mintable would be fine
    */

    constructor (string memory _name, string memory _symbol, uint8 _decimals) public ERC20Detailed(_name, _symbol, _decimals) {
        _mint(msg.sender, 0); // The initial supply is set to zero because for our web app there is no need for the producer to set it: 
    }                         // the tokens are automatically minted through pay_out_free and buyTokens functions
}

contract MovBitFreeToken is Ownable {
    /**
     * MovBitFreeToken is the first contract to be deployed; MovBitToken is deployed inside here because it permits not to generate token 
     * directly in the account of the producer
     * The input here are: name, symbol and decimals of the token
    */

    using SafeMath for uint256;
    using SafeMath for int;

    MovBitToken token;
    address public admin;
    address public addToken;
    
    constructor (string memory _name, string memory _symbol, uint8 _decimals) public {
        token = new MovBitToken(_name, _symbol, _decimals);
        addToken = address(token);
        admin = msg.sender;
    }

    function openSell(address _address) public onlyOwner { // fucntion used to assign to the MovBitCrowdsale contract the role of minter:
        token.addMinter(_address);                         // in this way the contract mints tokens as needed by the investors
    }
}

contract MovBitCrowdsale is CappedCrowdsale, RefundableCrowdsale, MintedCrowdsale, Ownable {
    /**
     * This crowdsale contract is capped, minted, refundable and timed (derived from refundable):
     * - capped: the producer sets the cap amount of token to be raised;
     * - minted: the contract automatically creates tokens based on the amount bought through buyTokens function;
     * - refundable: the producer sets a goal and if not reached the investors can call their ether back;
     * - timed: the producer chooses opening Time and closing Time even though in movbit app he sets only closing time
     *   in order to handle a problem raised (explained in 2_deploy_contracts.js file in migrations folder).
     * MovBitCrowdsale is the second contract to be deployed and the input are: opening Time, closing Time, rate, cap, wallet of the
     * producer, goal and finally address of the previous deployed token contract.
    */

    using SafeMath for int;
    using SafeMath for uint256;
    using Address for address payable;

    MovBitToken private tokenContract;
    
    // Set the state variables for FREE TOKENS
    int256 public freeTokensAssign;
    uint256 public freetokenSold;
    bool public endFree;
    address[] public indexAddress;

    mapping (address => int) public Royalties;

    // Set the state variables for DIVIDEND
    uint256 public tokenSold;
    uint256 weiToSend;
    uint256 amountDividend;
    uint256 public timeDividend;
    uint256 public fixBalance;
    bool public filmUpload;

    mapping(address => uint256) public _deposits;
    mapping (address => uint256) public claimAddress;
    
    event Withdrawn(address indexed payee, uint256 weiAmount);
    
    // Constructor of the contract with all the inputs
    constructor (uint256 openingTime, uint256 closingTime, uint256 rate, address payable wallet, uint256 cap, MovBitToken token, uint256 goal) public 
        Crowdsale(rate, wallet, token)
        CappedCrowdsale(cap)
        TimedCrowdsale(openingTime, closingTime)
        RefundableCrowdsale(goal) {
            require(goal <= cap, "SampleCrowdSale: goal is greater than cap");
            tokenContract = token; // necessary to call MovBitToken functions
            timeDividend = 0;
            filmUpload = false;
        }
    
    // ***CHECK BALANCE functions: introduced to quickly check eth balance of the contract and accounts (not used by web app)
    function balance_contract() view public returns(uint256) {
        return address(this).balance;
    }
    
    function balance_account() view public returns(uint256) {
        return msg.sender.balance;
    }
    
    // ***FREE TOKENS functions
    // Function to create tokens based on the amount choose by the producer (not used by web app)
    function addTokens(uint256 _amount) public onlyOwner {
        require(endFree == false, "Already closed the free tokens!");
        tokenContract.mint(address(this), _amount);
    }
    // Function to burn tokens based on the amount choose by the producer (not used by web app)
    function burnTokens(uint256 _amount) public onlyOwner {
        require(endFree == false, "Already closed the free tokens!");
        tokenContract.burn(_amount);
    }
    // Function to check the amount of tokens in a certain account (used by web app)
    function balanceOf(address _address) public view returns (uint256) {
        return tokenContract.balanceOf(_address);
    }

    // *Series of functions to handle the mapping created by the producer before paying actually the free tokens to his colaborators
    // Assign or remove free tokens to a certain address (used by web app)
    function add_royalties(address _add_id, int _num_tokens) public onlyOwner {
        Royalties[_add_id] += _num_tokens;
        require(Royalties[_add_id]>=0);
        freeTokensAssign += _num_tokens;
        indexAddress.push(_add_id);
    }
    // Set to zero an account where the producer previously assigned some free tokens (not used by the web app)
    function set_to_zero (address _add_id) public onlyOwner {
        require(Royalties[_add_id]>=0, "It is already at zero");
        int balance = Royalties[_add_id];
        Royalties[_add_id] -= balance;
        freeTokensAssign -= balance;
    }
    // Pay out actually all the free tokens set based on the Royalties mapping (used by web app)  
    function pay_out_free() payable public onlyOwner{
        require(endFree == false, "You cannot send free tokens anymore!"); // once call allowCrowdsale the producer can not anymore send free tokens.
        
        tokenContract.mint(address(this),uint256(freeTokensAssign)); // freeTokensAssign permits to call pay_out_free more than once creating only the
        freeTokensAssign -= freeTokensAssign;                        // amount of tokens mapped by the producer after the last call of this function
        for (uint i=0; i<indexAddress.length; i++) { 
            tokenContract.transfer(indexAddress[i], uint256(Royalties[indexAddress[i]]));
            freetokenSold += uint256(Royalties[indexAddress[i]]); // freetokenSold stores the amount of actually sold free tokens
            deposit(indexAddress[i],uint256(Royalties[indexAddress[i]])); // add each address and relative token amount to the mapping 
            Royalties[indexAddress[i]] -= Royalties[indexAddress[i]];     // that will be used to pay dividend
        }
    }
    // When the producer calls this function, investors can start buying the tokens and the producer can not sell anymore free tokens (used by web app)
    function allowCrowdsale() public onlyOwner {
        require(endFree == false, "Already closed the free token phase!");
        tokenContract.burn(tokenContract.balanceOf(address(this))); // not needed for the web app
        endFree = true;
    }
    // Inheritance in OpenZeppelin Crowdsale contract to lock buyTokens investor function until the producer call allowCrowdsale
    function _postValidatePurchase(address beneficiary, uint256 weiAmount) internal view {
        require(endFree == true, "Free Token PHASE still open!");
        super._postValidatePurchase(beneficiary, weiAmount);
    }

    // ***THE REFUNDABLE PHASE IS HANDLE BY OPENZEPPELIN FUNCTIONS!

    // ***IN CASE THE FILM HAS BEEN PRODUCED
    // The producer call this funtion to allow consumer to buy the film (used by web app)
    function filmUploaded() public onlyOwner{
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed yet!");
        filmUpload = true;
    }

    // ***CONSUMER function
    // Through this function consumers buy the film (used by web app)
    function buyFilm() external payable { 
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed!");
        require(filmUpload == true, "Film not yet uploaded!");
    }

    // ***HANDLE DIVIDEND
    // Check number of tokens sold to a specific address based on the mapping created within the smart contract (not used by we app)
    function depositsOf(address payee) public view returns (uint256) {
        return _deposits[payee];
    }
    // Add address and deposit to the mapping
    function deposit(address payee, uint256 _tokenAmount) internal {
        _deposits[payee] = _deposits[payee].add(_tokenAmount);
    }
    // Inheritance in OpenZeppelin Crowdsale contract to take for each investor the number of tokens bought and store them in the mapping 
    function _updatePurchasingState(address beneficiary, uint256 weiAmount) internal {
        super._updatePurchasingState(beneficiary, weiAmount);
        uint256 tokensAmount = weiAmount.mul(Crowdsale.rate());
        deposit(beneficiary,tokensAmount);
    }
    // Return the overall amount of free token sold (used by web app)
    function freeTokenAmount() view public returns(uint256){
        return freetokenSold;
    }
    // Return the amount of token sold both to investors and collaborators (used by web app)
    function totalAmountToken() view public returns(uint256){
        return SafeMath.add(Crowdsale.weiRaised().mul(Crowdsale.rate()),freetokenSold);
    }

    /** 
     * The following function has been implemented in order to be called once a year by anyone to set the balance of the Crowdsale contract    
     * at that point in time and permits to claim the dividend based on that amount (used by we app)
     * This has been the way that we found to solve the claim dividend problem of a smart contract with continously ether coming in
     * by consumer buyng the film
    */
    function fixTimeBalance() public {
        require(TimedCrowdsale.hasClosed() == true, "Crowdsale not closed yet!");
        require(filmUpload == true, "Film not yet uploaded!");
        require((block.timestamp-timeDividend)>=52 weeks || timeDividend == 0, "Not one year since last call!");
        timeDividend = block.timestamp;
        fixBalance = address(this).balance;  
    }
    // claimDividend is used by investors and free token owners to claim their dividend and it can be called only once a year (used by web app)
    function claimDividend(address payable payee) public {
        require(fixBalance != 0, "No balance has been fixed!");
        require(filmUpload == true, "Film not yet uploaded!");
        require(claimAddress[payee] != timeDividend, "Dividend already claimed!");
        
        tokenSold = SafeMath.add(Crowdsale.weiRaised().mul(Crowdsale.rate()),freetokenSold); // overall amount of token sold
        amountDividend = SafeMath.mul(_deposits[payee],fixBalance);
        weiToSend = SafeMath.div(amountDividend,tokenSold); // wei that must be sent to the caller investor
        
        payee.transfer(weiToSend); // this transfer should be improved in case of deployment, no more safe right now
        
        claimAddress[payee] = timeDividend;

        emit Withdrawn(payee, weiToSend); // events of the withdraw
    }
}