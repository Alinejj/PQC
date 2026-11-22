import oqs

sigalg = "ML-DSA-44"


# generate a keypair for the specified signature algorithm
def generate_dsa_keypair(alg=sigalg):
    if alg not in oqs.get_enabled_sig_mechanisms():
        raise ValueError(f"Unsupported ML-DSA algorithm: {alg}")

    with oqs.Signature(alg) as signer:
        public_key = signer.generate_keypair()
        secret_key = signer.export_secret_key()

    return public_key, secret_key


# sign a message with the specified signature algorithm and secret key
def sign_message(message, secret_key, alg=sigalg):
    if alg not in oqs.get_enabled_sig_mechanisms():
        raise ValueError(f"Unsupported ML-DSA algorithm: {alg}")
    if not isinstance(message, bytes):
        raise TypeError("message must be bytes")
    if not isinstance(secret_key, bytes) or len(secret_key) == 0:
        raise TypeError("secret_key must be non-empty bytes")

    with oqs.Signature(alg, secret_key) as signer:
        signature = signer.sign(message)

    return signature


# verify signature with the specified signature algorithm and public key
def verify_signature(message, signature, public_key, alg=sigalg):
    if alg not in oqs.get_enabled_sig_mechanisms():
        raise ValueError(f"Unsupported ML-DSA algorithm: {alg}")
    if not isinstance(message, bytes):
        raise TypeError("message must be bytes")
    if not isinstance(signature, bytes) or len(signature) == 0:
        raise TypeError("signature must be non-empty bytes")
    if not isinstance(public_key, bytes) or len(public_key) == 0:
        raise TypeError("public_key must be non-empty bytes")

    with oqs.Signature(alg) as verifier:
        is_valid = verifier.verify(message, signature, public_key)

    return is_valid
