import oqs

kemalg = "ML-KEM-512"   # ML-KEM algorithm in use


# generate a keypair for the specified KEM algorithm
def generate_kem_keypair(alg=kemalg):
    if alg not in oqs.get_enabled_kem_mechanisms():
        raise ValueError(f"Unsupported ML-KEM algorithm: {alg}")

    with oqs.KeyEncapsulation(alg) as kem:
        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()

    return public_key, secret_key


def encapsulate(public_key, alg=kemalg):  # returns ciphertext and shared secret
    if alg not in oqs.get_enabled_kem_mechanisms():
        raise ValueError(f"Unsupported ML-KEM algorithm: {alg}")
    if not isinstance(public_key, bytes) or len(public_key) == 0:
        raise TypeError("public_key must be non-empty bytes")

    with oqs.KeyEncapsulation(alg) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)

    return ciphertext, shared_secret


def decapsulate(ciphertext, secret_key, alg=kemalg):  # returns shared secret
    if alg not in oqs.get_enabled_kem_mechanisms():
        raise ValueError(f"Unsupported ML-KEM algorithm: {alg}")
    if not isinstance(ciphertext, bytes) or len(ciphertext) == 0:
        raise TypeError("ciphertext must be non-empty bytes")
    if not isinstance(secret_key, bytes) or len(secret_key) == 0:
        raise TypeError("secret_key must be non-empty bytes")

    with oqs.KeyEncapsulation(alg, secret_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)

    return shared_secret
