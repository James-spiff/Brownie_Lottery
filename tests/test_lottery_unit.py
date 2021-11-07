from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy import deploy_lottery
from web3 import Web3
import pytest
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, get_contract, fund_with_link

#0.013 which is $50 in eth
def test_get_entrance_fee():
    # account = accounts[0]
    # lottery = Lottery.deploy(config["networks"][network.show_active()]["eth_usd_price_feed"], {"from": account})
    # assert lottery.getEntranceFee() > Web3.toWei(0.012, "ether")
    # assert lottery.getEntranceFee() < Web3.toWei(0.016, "ether")
    
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    #Arrange
    lottery = deploy_lottery()
    #Act
    #let's assume 3900 eth/usd
    # entry fee is 50 USD
    #   3900 == 50/x == 0.013 (50/3900)
    #expected_entrance_fee = Web3.toWei(0.013, "ether") #correct price at the time
    expected_entrance_fee = Web3.toWei(0.025, "ether")  #used this because the contract was using an older price i.e 2000 eth/usd
    entrance_fee = lottery.getEntranceFee()
    #Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():   #test if a user cannot enter unless the lottery has started
    #Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    
    #Act /Assert
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    #Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()

    #Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})

    #Assert
    assert lottery.players(0) == account    #check if our player address exists in the players array


def test_can_end_lottery():
    #Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()

    #Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})

    #Assert
    assert lottery.lottery_state() == 2     #2 reps the 3rd state in the enum which is CALCULATING_WINNER


def test_can_pick_winner_correctly():
    #Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()

    #Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    #create 2 dummy accounts to enter the lottery with
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    transaction = lottery.endLottery({"from": account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]  #we access the events emitted when ending our lottery and get the RequestedRandomness by the requestId
    #below is how we mock responses in our tests
    static_random_number = 777
    get_contract("vrf_coordinator").callBackWithRandomness(request_id, static_random_number, lottery.address, {"from": account})
    #from the above our static random number is 777 which when passed against the length of players 3 will generate a winner using the calculation below:
    # 777 % 3 = 0 . Therefore our winner is player 0 

    #Assert
    assert lottery.recentWinner() == account #account is player 0
    assert lottery.balance() == 0 #all the money is transfered into the winners account
    
