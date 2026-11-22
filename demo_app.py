import subprocess
import sys
from pathlib import Path

from classical import (
    rsa_keygen,
    rsa_encap,
    rsa_decap,
    rsa_sign,
    rsa_verify,
    ecdsa_keygen,
    ecdsa_sign,
    ecdsa_verify,
    aes_keygen,
    aes_encrypt,
    aes_decrypt,
)

from PQC_service.mlkem import generate_kem_keypair, encapsulate, decapsulate
from PQC_service.mldsa import generate_dsa_keypair, sign_message, verify_signature

KEM_ALGS = ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"]
DSA_ALGS = ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"]


def choose(options):
    while True:
        print()
        for i in range(len(options)):
            print(f"{i + 1}. {options[i]}")
        print("0. Back")

        pick = input("Pick a variant: ").strip()

        if pick == "0":
            return None
        if pick.isdigit() and 1 <= int(pick) <= len(options):
            return options[int(pick) - 1]

        print("That's not an option, try again.")


def rsa_demo():
    print("\n--- RSA Key Exchange Demo ---")

    private_key, public_key = rsa_keygen()

    encrypted_key, original_key = rsa_encap(public_key)
    recovered_key = rsa_decap(private_key, encrypted_key)

    print("RSA key pair generated.")
    print("AES key encrypted using RSA.")
    print("AES key recovered using RSA.")

    print("Keys match:", original_key == recovered_key)


def rsa_signature_demo():
    print("\n--- RSA Digital Signature Demo ---")

    message = b"Hello from the PQC project!"

    private_key, public_key = rsa_keygen()

    signature = rsa_sign(private_key, message)
    verified = rsa_verify(public_key, signature, message)

    print("Original message:", message.decode())
    print("Signature generated.")
    print("Signature valid:", verified)


def ecdsa_demo():
    print("\n--- ECDSA Digital Signature Demo ---")

    message = b"Hello from the PQC project!"

    private_key, public_key = ecdsa_keygen()

    signature = ecdsa_sign(private_key, message)
    verified = ecdsa_verify(public_key, signature, message)

    print("Original message:", message.decode())
    print("Signature generated.")
    print("Signature valid:", verified)


def aes_demo():
    print("\n--- AES-GCM Encryption Demo ---")

    message = b"Hello from the PQC project!"

    key = aes_keygen()
    nonce, ciphertext = aes_encrypt(key, message)
    decrypted = aes_decrypt(key, nonce, ciphertext)

    print("Original message:", message.decode())
    print("Encrypted message (hex):", ciphertext.hex())
    print("Decrypted message:", decrypted.decode())
    print("Messages match:", message == decrypted)


def mlkem_demo():
    alg = choose(KEM_ALGS)
    if not alg:
        return

    print(f"\n--- {alg} Post-Quantum Key Exchange Demo ---")

    try:
        public_key, secret_key = generate_kem_keypair(alg)
        ciphertext, original_secret = encapsulate(public_key, alg)
        recovered_secret = decapsulate(ciphertext, secret_key, alg)

    except Exception as e:
        print(f"Error occurred while running {alg} demo: {e}")
        return

    print(f"{alg} key pair generated.")
    print("Shared secret encapsulated using public key.")
    print(f"{alg} shared secret recovered using private key.")
    print("Secrets match:", original_secret == recovered_secret)


def mldsa_demo():
    alg = choose(DSA_ALGS)
    if not alg:
        return

    print(f"\n--- {alg} Post-Quantum Signature Demo ---")

    message = b"Hello from the PQC project!"

    try:
        public_key, secret_key = generate_dsa_keypair(alg)
        signature = sign_message(message, secret_key, alg)
        verified = verify_signature(message, signature, public_key, alg)

    except Exception as e:
        print(f"Error occurred while running {alg} demo: {e}")
        return

    print("Original message:", message.decode())
    print(f"{alg} signature generated.")
    print("Signature valid:", verified)


def benchmark_demo():
    print("\n--- Classical vs Post-Quantum Benchmark ---")
    print("Running benchmarks. This may take a moment...\n")

    benchmark_script = Path(__file__).resolve().with_name("benchmark.py")

    subprocess.run(
        [
            sys.executable,
            str(benchmark_script),
            "--iterations", "10",
            "--warmup", "2",
        ],
        check=True,
    )


def main():
    while True:
        print("\n===================================")
        print("      CRYPTOGRAPHY DEMO APP")
        print("===================================")
        print("1. RSA Key Exchange")
        print("2. RSA Digital Signature")
        print("3. ECDSA Digital Signature")
        print("4. AES-GCM Encryption")
        print("5. ML-KEM Post-Quantum Key Exchange")
        print("6. ML-DSA Post-Quantum Signature")
        print("7. Compare Classical vs Post-Quantum Performance")
        print("8. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            rsa_demo()
        elif choice == "2":
            rsa_signature_demo()
        elif choice == "3":
            ecdsa_demo()
        elif choice == "4":
            aes_demo()
        elif choice == "5":
            mlkem_demo()
        elif choice == "6":
            mldsa_demo()
        elif choice == "7":
            benchmark_demo()
        elif choice == "8":
            print("Exiting demo application.")
            break


if __name__ == "__main__":
    main()
