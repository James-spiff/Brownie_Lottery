from brownie import Lottery, network, config
from .helpful_scripts import get_account, get_contract, fund_with_link
import time

def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(   #this must follow the same order as it appears in the constructor of Lottery.sol
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        publish_source=config["networks"][network.show_active()].get("verify", False)
    ) #This uses the get_contract function to get the data from the config file. The contracts are gotten from chainlink-mix and are stored in our contracts/test folder
    print("Deployed Lottery!")   
    return lottery 


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account}) #triggers the startLottery function from the contract
    starting_tx.wait(1) #wait's for the transaction to finish before continuing it's advised to implement this to avoid errors
    print("Lottery has started!")    


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You've entered the lottery!")

def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    #we need to fund the contract with some link token before we can end it
    #it needs the link token to check for randomness
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_transaction = lottery.endLottery({"from": account})
    ending_transaction.wait(1)
    time.sleep(60)  #in the smart contract we make a request to a chainlink node for a random number this let's us wait about 60 seconds until we get the response back from the chainlink node
    print(f"{lottery.recentWinner()} is the winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()