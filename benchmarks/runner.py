import statistics
import time
from dataclasses import dataclass


@dataclass
class OpResult:
    scheme: str
    family: str
    kind: str            # kem or sig
    operation: str       # keygen, encaps, decaps, sign, verify
    iterations: int
    mean_us: float
    median_us: float
    stdev_us: float
    min_us: float
    max_us: float


@dataclass
class SizeResult:
    scheme: str
    family: str
    kind: str
    public_key_bytes: int
    output_bytes: int    # ciphertext for kem, signature for sig
    shared_secret_bytes: int


def time_op(fn, iterations, warmup):
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - start) / 1000)
    return samples


def _op_result(scheme, kind, operation, samples):
    return OpResult(
        scheme=scheme.name,
        family=scheme.family,
        kind=kind,
        operation=operation,
        iterations=len(samples),
        mean_us=statistics.mean(samples),
        median_us=statistics.median(samples),
        stdev_us=statistics.stdev(samples) if len(samples) > 1 else 0.0,
        min_us=min(samples),
        max_us=max(samples),
    )


def bench_kem(scheme, iterations, warmup):
    sk, pk = scheme.keygen()
    ct, ss = scheme.encaps(pk)
    if scheme.decaps(sk, ct) != ss:
        raise RuntimeError(f"{scheme.name}: decapsulated secret does not match")

    ops = [
        ("keygen", lambda: scheme.keygen()),
        ("encaps", lambda: scheme.encaps(pk)),
        ("decaps", lambda: scheme.decaps(sk, ct)),
    ]
    timings = [_op_result(scheme, "kem", name, time_op(fn, iterations, warmup)) for name, fn in ops]
    size = SizeResult(scheme.name, scheme.family, "kem",
                      len(scheme.public_key_bytes(pk)), len(ct), len(ss))
    return timings, size


def bench_sig(scheme, iterations, warmup, message):
    sk, pk = scheme.keygen()
    sig = scheme.sign(sk, message)
    if not scheme.verify(pk, sig, message):
        raise RuntimeError(f"{scheme.name}: signature failed to verify")
    if scheme.verify(pk, sig, message + b"x"):
        raise RuntimeError(f"{scheme.name}: signature verified for a tampered message")

    ops = [
        ("keygen", lambda: scheme.keygen()),
        ("sign", lambda: scheme.sign(sk, message)),
        ("verify", lambda: scheme.verify(pk, sig, message)),
    ]
    timings = [_op_result(scheme, "sig", name, time_op(fn, iterations, warmup)) for name, fn in ops]
    size = SizeResult(scheme.name, scheme.family, "sig",
                      len(scheme.public_key_bytes(pk)), len(sig), 0)
    return timings, size
