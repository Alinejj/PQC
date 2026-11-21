import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullLocator

COLORS = {"classical": "#2a78d6", "pqc": "#eb6834"}
LABELS = {"classical": "Classical", "pqc": "Post-quantum"}
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

OPERATIONS = {
    "kem": [("keygen", "Key generation"), ("encaps", "Encapsulate"), ("decaps", "Decapsulate")],
    "sig": [("keygen", "Key generation"), ("sign", "Sign"), ("verify", "Verify")],
}
TITLES = {"kem": "Key exchange", "sig": "Signatures"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=MUTED, length=0)
    ax.tick_params(axis="y", labelcolor=INK)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def legend(fig):
    handles = [plt.Line2D([], [], marker="o", linestyle="", markersize=8, color=COLORS[k])
               for k in COLORS]
    fig.legend(handles, [LABELS[k] for k in COLORS], loc="upper right",
               frameon=False, ncol=2, labelcolor=INK)


def format_us(us):
    if us >= 1000:
        return f"{us / 1000:,.1f} ms"
    return f"{us:,.0f} µs"


def tick_label(us):
    if us >= 1_000_000:
        return f"{us / 1_000_000:g} s"
    if us >= 1000:
        return f"{us / 1000:g} ms"
    return f"{us:g} µs"


# Timings span four orders of magnitude (RSA key generation vs ECDH), so they
# are drawn as dots on a log axis instead of bars, which need a zero baseline.
def plot_timings(timings, kind, out_dir):
    ops = OPERATIONS[kind]
    rows = [r for r in timings if r["kind"] == kind]
    schemes = list(dict.fromkeys(r["scheme"] for r in rows))

    fig, axes = plt.subplots(1, len(ops), figsize=(13, 0.45 * len(schemes) + 1.6), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, (op, op_title) in zip(axes, ops):
        style(ax)
        medians = []
        for i, scheme in enumerate(schemes):
            row = next(r for r in rows if r["scheme"] == scheme and r["operation"] == op)
            median = float(row["median_us"])
            medians.append(median)
            ax.plot(median, i, "o", markersize=8, color=COLORS[row["family"]],
                    markeredgecolor=SURFACE, markeredgewidth=2)
            ax.annotate(format_us(median), (median, i), xytext=(8, 0),
                        textcoords="offset points", va="center", fontsize=8, color=MUTED)
        ax.set_xscale("log")
        wide = max(medians) / min(medians) > 20
        ax.xaxis.set_major_locator(LogLocator(subs=(1,) if wide else (1, 2, 5)))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: tick_label(v)))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_title(op_title, color=INK, fontsize=11, loc="left")
        ax.set_xlabel("median time (log scale)", color=MUTED, fontsize=9)
        ax.margins(x=0.25)
    axes[0].set_yticks(range(len(schemes)), schemes)
    axes[0].invert_yaxis()

    fig.suptitle(f"{TITLES[kind]}: median time per operation", x=0.01, ha="left",
                 color=INK, fontsize=13)
    legend(fig)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = os.path.join(out_dir, f"timings_{kind}.png")
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def plot_sizes(sizes, kind, out_dir):
    rows = [r for r in sizes if r["kind"] == kind]
    output_name = "Ciphertext" if kind == "kem" else "Signature"
    panels = [("public_key_bytes", "Public key"), ("output_bytes", output_name)]

    fig, axes = plt.subplots(1, 2, figsize=(11, 0.45 * len(rows) + 1.6), sharey=True)
    fig.patch.set_facecolor(SURFACE)
    for ax, (field, panel_title) in zip(axes, panels):
        style(ax)
        values = [int(r[field]) for r in rows]
        ax.barh(range(len(rows)), values, height=0.6,
                color=[COLORS[r["family"]] for r in rows],
                edgecolor=SURFACE, linewidth=2)
        for i, v in enumerate(values):
            ax.annotate(f"{v:,} B", (v, i), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=MUTED)
        ax.set_title(panel_title, color=INK, fontsize=11, loc="left")
        ax.set_xlabel("bytes", color=MUTED, fontsize=9)
        ax.margins(x=0.18)
    axes[0].set_yticks(range(len(rows)), [r["scheme"] for r in rows])
    axes[0].invert_yaxis()

    fig.suptitle(f"{TITLES[kind]}: size in bytes", x=0.01, ha="left", color=INK, fontsize=13)
    legend(fig)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    path = os.path.join(out_dir, f"sizes_{kind}.png")
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description="Draw charts from benchmark results")
    parser.add_argument("results", nargs="?", default="benchmarks/final_results",
                        help="folder containing timings.csv and sizes.csv")
    args = parser.parse_args()

    timings = read_csv(os.path.join(args.results, "timings.csv"))
    sizes = read_csv(os.path.join(args.results, "sizes.csv"))
    for kind in ("kem", "sig"):
        print(plot_timings(timings, kind, args.results))
        print(plot_sizes(sizes, kind, args.results))


if __name__ == "__main__":
    main()
