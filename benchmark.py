import argparse
import csv
import json
import os
import platform
from dataclasses import asdict, fields
from datetime import datetime

import cryptography
from cryptography.hazmat.backends.openssl import backend

from benchmarks.algorithms import KEM_SCHEMES, SIG_SCHEMES
from benchmarks.runner import OpResult, SizeResult, bench_kem, bench_sig


def machine_info():
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "cryptography": cryptography.__version__,
        "openssl": backend.openssl_version_text(),
    }


def write_csv(path, rows, row_type):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[fld.name for fld in fields(row_type)])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def print_tables(timings, sizes):
    print(f"\n{'scheme':<20}{'op':<8}{'median us':>12}{'mean us':>12}{'stdev':>10}")
    for t in timings:
        print(f"{t.scheme:<20}{t.operation:<8}{t.median_us:>12.1f}{t.mean_us:>12.1f}{t.stdev_us:>10.1f}")

    print(f"\n{'scheme':<20}{'kind':<6}{'pubkey B':>10}{'ct/sig B':>10}")
    for s in sizes:
        print(f"{s.scheme:<20}{s.kind:<6}{s.public_key_bytes:>10}{s.output_bytes:>10}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark classical vs post-quantum key exchange and signatures"
    )
    parser.add_argument("--iterations", type=int, default=10,
                        help="timed runs per operation")
    parser.add_argument("--warmup", type=int, default=5,
                        help="untimed runs before timing each operation")
    parser.add_argument("--message-size", type=int, default=1024,
                        help="bytes in the message that gets signed")
    parser.add_argument("--only", default="",
                        help="only run schemes whose name contains this text")
    parser.add_argument("--out", default="benchmarks/results",
                        help="folder for results.json, timings.csv and sizes.csv")
    args = parser.parse_args()

    message = os.urandom(args.message_size)
    timings, sizes = [], []

    for scheme in KEM_SCHEMES + SIG_SCHEMES:
        if args.only.lower() not in scheme.name.lower():
            continue
        print(f"benchmarking {scheme.name}...", flush=True)
        if scheme in KEM_SCHEMES:
            t, s = bench_kem(scheme, args.iterations, args.warmup)
        else:
            t, s = bench_sig(scheme, args.iterations, args.warmup, message)
        timings.extend(t)
        sizes.append(s)

    print_tables(timings, sizes)

    os.makedirs(args.out, exist_ok=True)
    write_csv(os.path.join(args.out, "timings.csv"), timings, OpResult)
    write_csv(os.path.join(args.out, "sizes.csv"), sizes, SizeResult)
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
        json.dump({
            "machine": machine_info(),
            "settings": {"iterations": args.iterations, "warmup": args.warmup,
                         "message_size": args.message_size},
            "timings": [asdict(t) for t in timings],
            "sizes": [asdict(s) for s in sizes],
        }, f, indent=2)
    print(f"\nresults written to {args.out}")


if __name__ == "__main__":
    main()
