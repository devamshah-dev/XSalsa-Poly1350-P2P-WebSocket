import time
import random
import os
import sys
from nacl import exceptions

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
try:
    import nacl.secret
    import nacl.utils
    import base64
except ImportError:
    print("[ERROR] PyNaCl not found. Please run the setup script first.")
    sys.exit(1)


REAL_SHARED_KEY = b'MySuperSecretKeyForAliceAndBob12'
if len(REAL_SHARED_KEY) != 32:
    raise ValueError("Key must be 32 bytes long!")

# A sample secret message from Alice to Bob.
PLAINTEXT_MESSAGE = "Bank Password is 123456."

# The attacker's small dictionary of guesses.
ATTACKER_WORDLIST = [
    "password", "123456", "secret", "admin", "root", "football",
    "dragon", "sunshine", "qwerty", "master", "login", "guest",
    "topsecret", "message", "meeting", "eagle", "dawn", "operation"
]

def get_color_escape(color_code):
    """Returns ANSI escape code for color, or empty string if not supported."""
    if sys.stdout.isatty() and platform.system() != 'Windows':
        return f"\033[{color_code}m"
    return ""

import platform
GREEN = get_color_escape("92")
RED = get_color_escape("91")
YELLOW = get_color_escape("93")
RESET = get_color_escape("0")

def generate_intercepted_packet():
    #encrypts the message with the REAL key to create our target.
    box = nacl.secret.SecretBox(REAL_SHARED_KEY)
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    encrypted_message = box.encrypt(PLAINTEXT_MESSAGE.encode('utf-8'), nonce)
    
    #attacker only gets the public parts of the message.
    intercepted_ciphertext = encrypted_message.ciphertext
    intercepted_nonce = encrypted_message.nonce
    
    return intercepted_ciphertext, intercepted_nonce

def derive_key_from_guess(guess: str) -> bytes:
    return guess.ljust(32, '*').encode('utf-8')

# --- Main Simulation ---

def run_simulation():
    """The main function to run the brute-force attack simulation."""
    print(f"{YELLOW}--- BRUTE-FORCE ATTACK SIMULATION ---{RESET}")
    print("I have intercepted an encrypted message between Alice and Bob.")
    
    ciphertext, nonce = generate_intercepted_packet()
    
    print(f"Intercepted Ciphertext (Base64): {base64.b64encode(ciphertext).decode()[:40]}...")
    print("The attacker will now try to decrypt it using a wordlist of common guesses.\n")
    time.sleep(3)

    total_attempts = len(ATTACKER_WORDLIST)
    for i, guess in enumerate(ATTACKER_WORDLIST):
        key_guess = derive_key_from_guess(guess)
        
        progress = f"[{i+1:>2}/{total_attempts}]"
        print(f"{progress} Attempting with key from '{guess}'...", end="", flush=True)
        
        for _ in range(3):
            time.sleep(random.uniform(0.05, 0.1))
            print(".", end="", flush=True)
        
        try:
            attacker_box = nacl.secret.SecretBox(key_guess)
            attacker_box.decrypt(ciphertext, nonce)
            
            print(f" {GREEN}SUCCESS!{RESET}")
            print(f"\n{GREEN}!!! SECURITY BREACH !!!{RESET}")
            print(f"Password '{guess}' successfully decrypted the message.")
            return

        except exceptions.CryptoError:
            print(f" {RED}FAILURE{RESET}")
            time.sleep(random.uniform(0.1, 0.2))

    print("\n-------------------------------------------------")
    print(f"{GREEN}ATTACK SIMULATION COMPLETE{RESET}")
    print(f"All {total_attempts} dictionary attacks failed.")
    print(f"The XChaCha20-Poly1305 encryption remains secure.")
    print("-------------------------------------------------")


if __name__ == "__main__":
    run_simulation()