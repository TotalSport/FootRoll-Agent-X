import json
from swarm.bots import Agent
from cdp import *
from typing import List, Dict, Any
import os
from openai import OpenAI
import openai
from decimal import Decimal
from typing import Union
from web3 import Web3
from web3.exceptions import ContractLogicError
from cdp.errors import ApiError, UnsupportedAssetError
# from cdp import Wallet  # Убедитесь, что Wallet импортирован из нужного модуля
from cdp import Cdp, Wallet  # Убедитесь, что Cdp и Wallet импортированы из нужного модуля

from twitter_utils import TwitterBot, api_v1, client_v2

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


from Crypto.PublicKey import ECC
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Инициализация TwitterBot с правильными аргументами
twitter_bot = TwitterBot(api_v1=api_v1, client_v2=client_v2)

from dotenv import load_dotenv
from twitter_utils import TwitterBot

load_dotenv()  # Загрузка переменных окружения
# Предположим, что API v1 и v2 инициализируются в twitter_utils.py
twitter_bot = TwitterBot(api_v1=api_v1, client_v2=client_v2)


# Проверка наличия ключа API
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"OpenAI API Key загружен: {api_key[:5]}..."
          )  # Показ первых 5 символов для подтверждения
    openai.api_key = api_key
else:
    print("Ошибка: OpenAI API Key не загружен.")


# Загрузка переменной окружения
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")


def load_private_key():
    private_key = os.getenv("CDP_PRIVATE_KEY", "").replace('\\n', '\n').strip()

    if "-----BEGIN EC PRIVATE KEY-----" in private_key:
        try:
            # Загрузка ключа как PEM-формата с использованием PyCryptodome
            ec_key = ECC.import_key(private_key)
            # Преобразование ключа в 32-байтовый формат (HEX)
            private_key_bytes = ec_key.d.to_bytes(32, byteorder='big')
            return private_key_bytes.hex()
        except ValueError as e:
            print(f"Failed to load EC private key: {e}")
            return None
    else:
        print("Error: Private key is not in the correct PEM format.")
        return None

def initialize_wallet(private_key: str):
    """
    Initialize wallet with the provided private key.
    """
    try:
        print(f"Attempting to initialize wallet with private key: {private_key[:10]}...")
        wallet = Wallet(private_key)
        if wallet is None:
            raise ValueError("Wallet object is None. Initialization failed.")

        if wallet.addresses():
            primary_address = wallet.addresses()[0]
            print(f"Wallet successfully created. Primary address: {primary_address.address_id}")
            return wallet
        else:
            print("Error: Wallet contains no addresses.")
            return None
    except Exception as e:
        print(f"Wallet initialization failed: {e}")
        return None


# Загрузка и инициализация
private_key = load_private_key()

if private_key:
    print(f"Processed Private Key (first 10 chars): {private_key[:10]}...")
    agent_wallet = initialize_wallet(private_key)
else:
    print("Error: Wallet not initialized due to invalid private key.")
    agent_wallet = None

# wallet = Wallet(bytes.fromhex(private_key))

wallet = Wallet(private_key)

# from Crypto.PublicKey import ECC
# from base64 import b64decode

# def load_ec_key(private_key: str):
#     try:
#         key = ECC.import_key(private_key)
#         return key
#     except ValueError as e:
#         print(f"Failed to load EC key: {e}")
#         return None

# pem_key = os.getenv("CDP_PRIVATE_KEY", "").replace('\\n', '\n').strip()
# loaded_key = load_ec_key(pem_key)
# if loaded_key:
#     print("EC Private Key loaded successfully.")
# else:
#     print("Error loading EC Private Key.")

# def load_private_key():
#     private_key = os.getenv("CDP_PRIVATE_KEY", "").replace('\\n', '\n').strip()

#     if "-----BEGIN" in private_key:
#         try:
#             # Загрузка EC-ключа
#             pem_key = serialization.load_pem_private_key(
#                 private_key.encode(),
#                 password=None,  # Добавьте пароль, если ключ зашифрован
#                 backend=default_backend()
#             )
#             private_key_hex = pem_key.private_numbers().private_value.to_bytes(32, byteorder="big").hex()
#             return private_key_hex
#         except Exception as e:
#             print(f"Error converting PEM private key: {e}")
#             return None
#     else:
#         print("Error: Private key is not in the correct format.")
#         return None

# def initialize_wallet(private_key: str):
#     """
#     Initialize wallet with the provided private key.
#     """
#     try:
#         print(f"Attempting to initialize wallet with private key: {private_key[:10]}...")
#         wallet = Wallet(private_key)
#         if wallet is None:
#             raise ValueError("Wallet object is None. Initialization failed.")

#         if wallet.addresses():
#             primary_address = wallet.addresses()[0]
#             print(f"Wallet successfully created. Primary address: {primary_address.address_id}")
#             return wallet
#         else:
#             print("Error: Wallet contains no addresses.")
#             return None
#     except Exception as e:
#         print(f"Wallet initialization failed: {e}")
#         return None

# private_key = load_private_key()

# if private_key:
#     print(f"Processed Private Key (first 10 chars): {private_key[:10]}...")
#     agent_wallet = initialize_wallet(private_key)
# else:
#     print("Error: Wallet not initialized due to invalid private key.")
#     agent_wallet = None


# wallet = Wallet(private_key)

# Define blockchain and Twitter functions here
def get_balance(asset_id: str) -> str:
    """
    Get the balance of a specific asset in the agent's wallet.

    Args:
        asset_id (str): Asset identifier ("eth", "usdc") or contract address of an ERC-20 token

    Returns:
        str: A message showing the current balance of the specified asset
    """
    try:
        balance = agent_wallet.balance(asset_id)
        return f"Current balance of {asset_id}: {balance}"
    except Exception as e:
        return f"Error retrieving balance: {str(e)}"


def create_token(agent_wallet, name, symbol, initial_supply):
    """
    Create a new ERC-20 token.

    Args:
        agent_wallet (Wallet): Wallet instance to deploy the token
        name (str): The name of the token
        symbol (str): The symbol of the token
        initial_supply (int): The initial supply of tokens

    Returns:
        str: A message confirming the token creation with details
    """
    deployed_contract = agent_wallet.deploy_token(name, symbol, initial_supply)
    deployed_contract.wait()
    return f"Token {name} ({symbol}) created with initial supply of {initial_supply} and contract address {deployed_contract.contract_address}"


# Function to transfer assets
def transfer_asset(amount, asset_id, destination_address):
    """
    Transfer an asset to a specific address.

    Args:
        amount (Union[int, float, Decimal]): Amount to transfer
        asset_id (str): Asset identifier ("eth", "usdc") or contract address of an ERC-20 token
        destination_address (str): Recipient's address

    Returns:
        str: A message confirming the transfer or describing an error
    """
    try:
        # Check if we're on Base Mainnet and the asset is USDC for gasless transfer
        is_mainnet = agent_wallet.network_id == "base-mainnet"
        is_usdc = asset_id.lower() == "usdc"
        gasless = is_mainnet and is_usdc

        # For ETH and USDC, we can transfer directly without checking balance
        if asset_id.lower() in ["eth", "usdc"]:
            transfer = agent_wallet.transfer(amount,
                                             asset_id,
                                             destination_address,
                                             gasless=gasless)
            transfer.wait()
            gasless_msg = " (gasless)" if gasless else ""
            return f"Transferred {amount} {asset_id}{gasless_msg} to {destination_address}"

        # For other assets, check balance first
        try:
            balance = agent_wallet.balance(asset_id)
        except UnsupportedAssetError:
            return f"Error: The asset {asset_id} is not supported on this network. It may have been recently deployed. Please try again in about 30 minutes."

        if balance < amount:
            return f"Insufficient balance. You have {balance} {asset_id}, but tried to transfer {amount}."

        transfer = agent_wallet.transfer(amount, asset_id, destination_address)
        transfer.wait()
        return f"Transferred {amount} {asset_id} to {destination_address}"
    except Exception as e:
        return f"Error transferring asset: {str(e)}. If this is a custom token, it may have been recently deployed. Please try again in about 30 minutes, as it needs to be indexed by CDP first."



# Function to request ETH from the faucet (testnet only)
def request_eth_from_faucet():
    """
    Request ETH from the Base Sepolia testnet faucet.

    Returns:
        str: Status message about the faucet request
    """
    if agent_wallet is None:
        raise ValueError("Wallet is not initialized. Please initialize agent_wallet before calling this function.")

    if agent_wallet.network_id == "base-mainnet":
        return "Error: The faucet is only available on Base Sepolia testnet."

    faucet_tx = agent_wallet.faucet()
    return f"Requested ETH from faucet. Transaction: {faucet_tx}"

if agent_wallet:
    response = request_eth_from_faucet(agent_wallet)
else:
    print("Error: Wallet not initialized.")


# Function to generate art using DALL-E (requires separate OpenAI API key)
def generate_art(prompt):
    """
    Generate art using DALL-E based on a text prompt.

    Args:
        prompt (str): Text description of the desired artwork

    Returns:
        str: Status message about the art generation, including the image URL if successful
    """
    try:
        client = OpenAI()
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        image_url = response.data[0].url
        return f"Generated artwork available at: {image_url}"

    except Exception as e:
        return f"Error generating artwork: {str(e)}"


# Function to deploy an ERC-721 NFT contract
def deploy_nft(name, symbol, base_uri):
    """
    Deploy an ERC-721 NFT contract.

    Args:
        name (str): Name of the NFT collection
        symbol (str): Symbol of the NFT collection
        base_uri (str): Base URI for token metadata

    Returns:
        str: Status message about the NFT deployment, including the contract address
    """
    try:
        deployed_nft = agent_wallet.deploy_nft(name, symbol, base_uri)
        deployed_nft.wait()
        contract_address = deployed_nft.contract_address

        return f"Successfully deployed NFT contract '{name}' ({symbol}) at address {contract_address} with base URI: {base_uri}"

    except Exception as e:
        return f"Error deploying NFT contract: {str(e)}"


# Function to mint an NFT
def mint_nft(contract_address, mint_to):
    """
    Mint an NFT to a specified address.

    Args:
        contract_address (str): Address of the NFT contract
        mint_to (str): Address to mint NFT to

    Returns:
        str: Status message about the NFT minting
    """
    try:
        mint_args = {"to": mint_to, "quantity": "1"}

        mint_invocation = agent_wallet.invoke_contract(
            contract_address=contract_address, method="mint", args=mint_args)
        mint_invocation.wait()

        return f"Successfully minted NFT to {mint_to}"

    except Exception as e:
        return f"Error minting NFT: {str(e)}"


# Function to swap assets (only works on Base Mainnet)
def swap_assets(amount: Union[int, float, Decimal], from_asset_id: str,
                to_asset_id: str):
    """
    Swap one asset for another using the trade function.
    This function only works on Base Mainnet.

    Args:
        amount (Union[int, float, Decimal]): Amount of the source asset to swap
        from_asset_id (str): Source asset identifier
        to_asset_id (str): Destination asset identifier

    Returns:
        str: Status message about the swap
    """
    if agent_wallet.network_id != "base-mainnet":
        return "Error: Asset swaps are only available on Base Mainnet. Current network is not Base Mainnet."

    try:
        trade = agent_wallet.trade(amount, from_asset_id, to_asset_id)
        trade.wait()
        return f"Successfully swapped {amount} {from_asset_id} for {to_asset_id}"
    except Exception as e:
        return f"Error swapping assets: {str(e)}"


# Contract addresses for Basenames
BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET = "0x4cCb0BB02FCABA27e82a56646E81d8c5bC4119a5"
BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET = "0x49aE3cC2e3AA768B1e5654f5D3C6002144A59581"
L2_RESOLVER_ADDRESS_MAINNET = "0xC6d566A56A1aFf6508b41f6c90ff131615583BCD"
L2_RESOLVER_ADDRESS_TESTNET = "0x6533C94869D28fAA8dF77cc63f9e2b2D6Cf77eBA"


# Function to create registration arguments for Basenames
def create_register_contract_method_args(base_name: str, address_id: str,
                                         is_mainnet: bool) -> dict:
    """
    Create registration arguments for Basenames.

    Args:
        base_name (str): The Basename (e.g., "example.base.eth" or "example.basetest.eth")
        address_id (str): The Ethereum address
        is_mainnet (bool): True if on mainnet, False if on testnet

    Returns:
        dict: Formatted arguments for the register contract method
    """
    w3 = Web3()

    resolver_contract = w3.eth.contract(abi=l2_resolver_abi)

    name_hash = w3.ens.namehash(base_name)

    address_data = resolver_contract.encode_abi("setAddr",
                                                args=[name_hash, address_id])

    name_data = resolver_contract.encode_abi("setName",
                                             args=[name_hash, base_name])

    register_args = {
        "request": [
            base_name.replace(".base.eth" if is_mainnet else ".basetest.eth",
                              ""),
            address_id,
            "31557600",  # 1 year in seconds
            L2_RESOLVER_ADDRESS_MAINNET
            if is_mainnet else L2_RESOLVER_ADDRESS_TESTNET,
            [address_data, name_data],
            True
        ]
    }

    return register_args


# Function to register a basename
def register_basename(basename: str, amount: float = 0.002):
    """
    Register a basename for the agent's wallet.
    
    Args:
        basename (str): The basename to register (e.g. "myname.base.eth" or "myname.basetest.eth")
        amount (float): Amount of ETH to pay for registration (default 0.002)
    
    Returns:
        str: Status message about the basename registration
    """
    address_id = agent_wallet.default_address.address_id
    is_mainnet = agent_wallet.network_id == "base-mainnet"

    suffix = ".base.eth" if is_mainnet else ".basetest.eth"
    if not basename.endswith(suffix):
        basename += suffix

    register_args = create_register_contract_method_args(
        basename, address_id, is_mainnet)

    try:
        contract_address = (BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET
                            if is_mainnet else
                            BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET)

        invocation = agent_wallet.invoke_contract(
            contract_address=contract_address,
            method="register",
            args=register_args,
            abi=registrar_abi,
            amount=amount,
            asset_id="eth",
        )
        invocation.wait()
        return f"Successfully registered basename {basename} for address {address_id}"
    except ContractLogicError as e:
        return f"Error registering basename: {str(e)}"
    except Exception as e:
        return f"Unexpected error registering basename: {str(e)}"


def post_to_twitter(content: str):
    """
    Post a message to Twitter.

    Args:
        content (str): The content to tweet

    Returns:
        str: Status message about the tweet
    """
    return twitter_bot.post_tweet(content)


# Create the Based Agent with all available functions
based_agent = Agent(
    name="DefaultAgent",
    instructions=
    "You are a helpful agent that can interact onchain on the Base Layer 2 using the Coinbase Developer Platform SDK. You can create tokens, transfer assets, generate art, deploy NFTs, mint NFTs, register basenames, and swap assets (on mainnet only). If you ever need to know your address, it is {agent_wallet.default_address.address_id}. If you ever need funds, you can request them from the faucet. You can also deploy your own ERC-20 tokens, NFTs, and interact with them. If someone asks you to do something you can't do, you can say so, and encourage them to implement it themselves using the CDP SDK, recommend they go to docs.cdp.coinbase.com for more informaton. You can also offer to help them implement it by writing the function and telling them to add it to the agents.py file and within your list of callable functions.",
    functions=[
        create_token,
        transfer_asset,
        get_balance,
        request_eth_from_faucet,
        #generate_art,  # Uncomment this line if you have configured the OpenAI API
        deploy_nft,
        mint_nft,
        swap_assets,
        register_basename,
        post_to_twitter,
    ],
)

# # add the following import to the top of the file, add the code below it, and add the new functions to the based_agent.functions list

# from twitter_utils import TwitterBot

# # Initialize TwitterBot with your credentials
# twitter_bot = TwitterBot(
#     api_key="",
#     api_secret="",
#     access_token="",
#     access_token_secret=""
# )

# Add these new functions to your existing functions list

# ABIs for smart contracts (used in basename registration)
l2_resolver_abi = [{
    "inputs": [{
        "internalType": "bytes32",
        "name": "node",
        "type": "bytes32"
    }, {
        "internalType": "address",
        "name": "a",
        "type": "address"
    }],
    "name":
    "setAddr",
    "outputs": [],
    "stateMutability":
    "nonpayable",
    "type":
    "function"
}, {
    "inputs": [{
        "internalType": "bytes32",
        "name": "node",
        "type": "bytes32"
    }, {
        "internalType": "string",
        "name": "newName",
        "type": "string"
    }],
    "name":
    "setName",
    "outputs": [],
    "stateMutability":
    "nonpayable",
    "type":
    "function"
}]

registrar_abi = [{
    "inputs": [{
        "components": [{
            "internalType": "string",
            "name": "name",
            "type": "string"
        }, {
            "internalType": "address",
            "name": "owner",
            "type": "address"
        }, {
            "internalType": "uint256",
            "name": "duration",
            "type": "uint256"
        }, {
            "internalType": "address",
            "name": "resolver",
            "type": "address"
        }, {
            "internalType": "bytes[]",
            "name": "data",
            "type": "bytes[]"
        }, {
            "internalType": "bool",
            "name": "reverseRecord",
            "type": "bool"
        }],
        "internalType":
        "struct RegistrarController.RegisterRequest",
        "name":
        "request",
        "type":
        "tuple"
    }],
    "name":
    "register",
    "outputs": [],
    "stateMutability":
    "payable",
    "type":
    "function"
}]

# To add a new function:
# 1. Define your function above (follow the existing pattern)
# 2. Add appropriate error handling
# 3. Add the function to the based_agent's functions list
# 4. If your function requires new imports or global variables, add them at the top of the file
# 5. Test your new function thoroughly before deploying

# Example of adding a new function:
# def my_new_function(param1, param2):
#     """
#     Description of what this function does.
#
#     Args:
#         param1 (type): Description of param1
#         param2 (type): Description of param2
#
#     Returns:
#         type: Description of what is returned
#     """
#     try:
#         # Your function logic here
#         result = do_something(param1, param2)
#         return f"Operation successful: {result}"
#     except Exception as e:
#         return f"Error in my_new_function: {str(e)}"

# Then add to based_agent.functions:
# based_agent = Agent(
#     ...
#     functions=[
#         ...
#         my_new_function,
#     ],
# )
