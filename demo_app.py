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

# from benchmarks.algorithms import KEM_SCHEMES, SIG_SCHEMES
from PQC_service.mlkem import generate_kem_keypair, encapsulate, decapsulate
from PQC_service.mldsa import generate_dsa_keypair, sign_message, verify_signature


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
    print("\n--- ML-KEM-768 Post-Quantum Key Exchange Demo ---")

    public_key, secret_key = generate_kem_keypair("ML-KEM-768")

    ciphertext, original_secret = encapsulate(public_key, "ML-KEM-768")
    recovered_secret = decapsulate(ciphertext, secret_key, "ML-KEM-768")

    print("ML-KEM key pair generated.")
    print("Shared secret encapsulated using public key.")
    print("Shared secret recovered using private key.")
    print("Secrets match:", original_secret == recovered_secret)


def mldsa_demo():
    print("\n--- ML-DSA-65 Post-Quantum Signature Demo ---")

    message = b"Hello from the PQC project!"

    public_key, secret_key = generate_dsa_keypair("ML-DSA-65")

    signature = sign_message(message, secret_key, "ML-DSA-65")
    verified = verify_signature(message, signature, public_key, "ML-DSA-65")

    print("Original message:", message.decode())
    print("Post-quantum signature generated.")
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
        print("5. ML-KEM-768 Post-Quantum Key Exchange")
        print("6. ML-DSA-65 Post-Quantum Signature")
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
