//SPDX-License-Identifier: MIT

pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol"; //allowers us to use a modifier that is only accessable to the owner/admin.... Modifiers are like decorators in python
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol"; //generates a random number for us 


contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    address payable public recentWinner;
    uint256 public randomness;
    uint256 public usdEntryFee; //which is $50
    AggregatorV3Interface internal ethUsdPriceFeed;
    enum LOTTERY_STATE {
        OPEN, 
        CLOSED,
        CALCULATING_WINNER
    } //theses values or states are reps by numbers open 1, closed 2, calculating_winner 3
    LOTTERY_STATE public lottery_state;
    uint256 public fee;
    bytes32 public keyHash;    //a keyHash is a way to uniquely identify the chainlink vrf node
    event RequestedRandomness(bytes32 requestId);


    constructor(
        address _priceFeedAddress, 
        address _vrfCoordinator, 
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {   //VRFConsumerBase is an inherited constructor from the VRFConsumerBase contract in solididity we can add other constructors from contracts into our own constructor this way
        usdEntryFee = 50 * (10**18);
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED; //our initial state will be CLOSED
        fee = _fee;
        keyHash = _keyHash;
    }
    
    function enter() public payable {
        require(lottery_state == LOTTERY_STATE.OPEN, "Lottery hasn't open yet try again later"); //a user can only pay if the lottery has started
        // to enter you need to pay a $50 minimum
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        players.push(msg.sender);
    }

    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , ,) = ethUsdPriceFeed.latestRoundData(); //get's the lates price for eth/usd
        uint256 adjustedPrice = uint256(price) * 10**10; //converts our price from int256 to uint256 and adds 10 zeros to the back so it has up to 18 decimals all together
        //To convert our USD to ETH using the latest price feed we perform the following operation:
        uint256 costToEnter = (usdEntryFee * 10**18) / adjustedPrice; //Here the 18 decimals from both values cancel each other out 
        return costToEnter;
    }

    //the lottery should only be able to be started by the admin or owner
    function startLottery() public onlyOwner {
        require(lottery_state == LOTTERY_STATE.CLOSED, "Can't start a new lottery yet");
        lottery_state = LOTTERY_STATE.OPEN;
    }

    //the lottery will choose a random winnerand close
    function endLottery() public onlyOwner {
        //The method below achieves pseudo randomness but can be easily exploited because the number generated is predictable
        //This method isn't adviced
        // uint256(
        //     keccak256(  //keccak256 is the hashing algorithm similar to sha256
        //         abi.encodePacked(
        //             nonce,  //the nonce in this case is predictable because it's the transaction number
        //             msg.sender, //this is also predictable
        //             block.difficulty,   //this can be manipulated by miners
        //             block.timestamp //the timestamp is predictable
        //         )
        //     )
        // )   % players.length;
        //////////A better method is to use chainlink VRF to get a random number from outside the blockchain
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        bytes32 requestId = requestRandomness(keyHash, fee);    //requestRandomness is a function gotten from VRFConsumerBase
        emit RequestedRandomness(requestId);    //passes an event to our transaction which we can view and get information from
    }

    //This function below uses the requestId generated to receive a random number from the VRFConsumerBase contract and picks a winner from the list of users/players
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override { //a fulfillRandomness function already exists in the VRF contract in order for us to use it we need to override it and the "override" keyword let's us do that
        require(lottery_state == LOTTERY_STATE.CALCULATING_WINNER); //checks if we are in the right state
        require(_randomness > 0, "randomness not found");
        uint256 indexOfWinner = _randomness % players.length;
        recentWinner = players[indexOfWinner];
        recentWinner.transfer(address(this).balance);   //transfers the entire balance to the winners address
        //Reset lottery after prize has been transfered
        players = new address payable[](0); //resets the players array
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;
    }
}
