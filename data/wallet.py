from solana.keypair import Keypair
import base58

def generate_solana_wallet():
    # Generate a new Solana keypair
    keypair = Keypair.generate()
    
    # Get the public key (wallet address) and private key
    public_key = keypair.public_key
    private_key = keypair.secret_key
    
    # Convert keys to a more readable format
    public_key_str = str(public_key)
    private_key_str = base58.b58encode(private_key).decode('utf-8')
    
    return public_key_str, private_key_str

if __name__ == "__main__":
    public_key, private_key = generate_solana_wallet()
    print(f"Public Key (Wallet Address): {public_key}")
    print(f"Private Key: {private_key}")
