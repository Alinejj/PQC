import oqs

kemalg = "ML-KEM-512"   # ML-KEM algorithm in use


# generate a keypair for the specified KEM algorithm
def generate_kem_keypair(alg=kemalg):
    with oqs.KeyEncapsulation(alg) as kem:

        public_key = kem.generate_keypair()
        secret_key = kem.export_secret_key()

    return public_key, secret_key


def encapsulate(public_key, alg=kemalg):  # returns ciphertext and shared secret
    with oqs.KeyEncapsulation(alg) as kem:
        ciphertext, shared_secret = kem.encap_secret(public_key)

    return ciphertext, shared_secret


def decapsulate(ciphertext, secret_key, alg=kemalg):  # returns shared secret
    with oqs.KeyEncapsulation(alg, secret_key) as kem:
        shared_secret = kem.decap_secret(ciphertext)

    return shared_secret
