from mlkem import generate_kem_keypair, encapsulate, decapsulate
from mldsa import generate_dsa_keypair, sign_message, verify_signature

# tests the implementation of the ML-KEM and ML-DSA algorithms


def demo_kem():
    # Generate a keypair for the client
    public_key_client, secret_key_client = generate_kem_keypair()

    # Encapsulate a shared secret using the client's public key
    ciphertext, shared_secret_server = encapsulate(public_key_client)

    # Decapsulate the ciphertext to obtain the shared secret on the client side
    shared_secret_client = decapsulate(ciphertext, secret_key_client)

    # Check if the shared secrets match
    if shared_secret_client == shared_secret_server:
        print("Shared secrets match.")
    else:
        print("Shared secrets do not match.")


def demo_dsa():

    # Generate a keypair for the signer
    public_key_signer, secret_key_signer = generate_dsa_keypair()

    # Sign a message using the signer's secret key
    message = b"This is the message to sign"
    signature = sign_message(message, secret_key_signer)

    # Verify the signature using the signer's public key
    is_valid = verify_signature(message, signature, public_key_signer)

    # Check if the signature is valid
    if is_valid:
        print("Signature is valid.")
    else:
        print("Signature is invalid.")


if __name__ == "__main__":
    print("Demonstrating ML-KEM:")
    demo_kem()
    print("Demonstrating ML-DSA:")
    demo_dsa()
