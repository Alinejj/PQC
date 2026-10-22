from dataclasses import dataclass
from typing import Callable


@dataclass
class KEMScheme:
    name: str
    family: str          # classical or pqc
    keygen: Callable     # () -> (private_key, public_key)
    encaps: Callable     # (public_key) -> (ciphertext, shared_secret)
    decaps: Callable     # (private_key, ciphertext) -> shared_secret
    public_key_bytes: Callable   # (public_key) -> bytes


@dataclass
class SigScheme:
    name: str
    family: str
    keygen: Callable     # () -> (private_key, public_key)
    sign: Callable       # (private_key, message) -> signature
    verify: Callable     # (public_key, signature, message) -> bool
    public_key_bytes: Callable
