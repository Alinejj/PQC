from mlkem import generate_keypair, encapsulate, decapsulate


def demo_kem():
    # Generate a keypair for the client
    public_key_client, secret_key_client = generate_keypair()

    # Encapsulate a shared secret using the client's public key
    ciphertext, shared_secret_server = encapsulate(public_key_client)

    # Decapsulate the ciphertext to obtain the shared secret on the client side
    shared_secret_client = decapsulate(ciphertext, secret_key_client)

    # Check if the shared secrets match
    if shared_secret_client == shared_secret_server:
        print("Shared secrets match.")
    else:
        print("Shared secrets do not match.")


if __name__ == "__main__":
    demo_kem()
