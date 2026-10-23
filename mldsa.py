from pprint import pformat
from sys import stdout

import oqs

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# logger.addHandler(logging.StreamHandler(stdout))

# logger.info("liboqs version: %s", oqs.oqs_version())
# logger.info("liboqs-python version: %s", oqs.oqs_python_version())
# logger.info(
#     "Enabled signature mechanisms:\n%s",
#     pformat(oqs.get_enabled_sig_mechanisms(), compact=True),
# )

# message = b"This is the message to sign"

# Create signer and verifier with sample signature mechanisms
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


# with oqs.Signature(sigalg) as signer, oqs.Signature(sigalg) as verifier:
#     logger.info("Signature details:\n%s", pformat(signer.details))

#     # Signer generates its keypair
#     signer_public_key = signer.generate_keypair()
#     # Optionally, the secret key can be obtained by calling export_secret_key()
#     # and the signer can later be re-instantiated with the key pair:
#     # secret_key = signer.export_secret_key()

#     # Store key pair, wait... (session resumption):
#     # signer = oqs.Signature(sigalg, secret_key)

#     # Signer signs the message
#     signature = signer.sign(message)

#     # Verifier verifies the signature
#     is_valid = verifier.verify(message, signature, signer_public_key)

#     logger.info("Valid signature? %s", is_valid)
