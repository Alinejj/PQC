import oqs
sigalg = "ML-DSA-44"


# generate a keypair for the specified signature algorithm
def generate_dsa_keypair(alg=sigalg):
    with oqs.Signature(alg) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()

    return public_key, secret_key


# sign a message with the specified signature algorithm and secret key
def sign_message(message, secret_key, alg=sigalg):
    with oqs.Signature(alg, secret_key) as signer:
        signature = signer.sign(message)

    return signature


# verify signature with the specified signature algorithm and public key
def verify_signature(message, signature, public_key, alg=sigalg):
    with oqs.Signature(alg) as verifier:
        is_valid = verifier.verify(message, signature, public_key)

    return is_valid
