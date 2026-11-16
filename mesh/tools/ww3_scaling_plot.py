#!/usr/bin/env python3
"""Plot WW3 strong-scaling from a set of CESM cesm_timing.* reports.

Each report contributes one point: the wave-component task count and the
throughput it achieved. Throughput is recomputed from "seconds/mday" rather
than read from the "Model Throughput" line, which is rounded to 2 decimals
and too coarse to compare neighbouring task counts.

Usage:
    ww3_scaling_plot.py <timing_dir | cesm_timing_file> ... [-o out.png] [--dark]
"""

import argparse
import glob
import os
import re
import sys

SEC_PER_DAY = 86400.0
DAYS_PER_YEAR = 365.0

# light / dark tokens, from the validated reference palette
THEME = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", muted="#52514e",
                  grid="#e4e3df", series="#2a78d6"),
    "dark":  dict(surface="#1a1a19", ink="#ffffff", muted="#c3c2b7",
                  grid="#333330", series="#3987e5"),
}

PATTERNS = {
    "wav_tasks":   re.compile(r"^\s*wav\s*=\s*\S+\s+\d+\s+\d+\s+(\d+)\s+x\s+(\d+)"),
    "total_pes":   re.compile(r"total pes active\s*:\s*(\d+)"),
    "cost":        re.compile(r"Model Cost:\s*([\d.]+)"),
    "tot_per_day": re.compile(r"TOT Run Time:.*?([\d.]+)\s+seconds/mday"),
    "wav_per_day": re.compile(r"WAV Run Time:.*?([\d.]+)\s+seconds/mday"),
    "stop_n":      re.compile(r"stop option\s*:\s*(\w+),\s*stop_n\s*=\s*(\d+)"),
}


def parse_timing(path):
    """Pull the scaling-relevant numbers out of one cesm_timing report."""
    found = {}
    with open(path) as fh:
        for line in fh:
            for key, pat in PATTERNS.items():
                if key in found:
                    continue
                m = pat.search(line)
                if m:
                    found[key] = m.groups()
    missing = {"wav_tasks", "tot_per_day"} - set(found)
    if missing:
        raise ValueError(f"{path}: could not find {', '.join(sorted(missing))}")

    tasks, threads = (int(x) for x in found["wav_tasks"])
    tot_per_day = float(found["tot_per_day"][0])
    rec = {
        "path": path,
        "wav_pes": tasks * threads,
        "total_pes": int(found["total_pes"][0]) if "total_pes" in found else tasks,
        "sec_per_mday": tot_per_day,
        "sypd": SEC_PER_DAY / tot_per_day / DAYS_PER_YEAR,
        "cost": float(found["cost"][0]) if "cost" in found else float("nan"),
        "wav_sec_per_mday": float(found["wav_per_day"][0]) if "wav_per_day" in found else float("nan"),
    }
    rec["wav_frac"] = rec["wav_sec_per_mday"] / rec["sec_per_mday"]
    return rec


def collect(inputs):
    """Expand directories to cesm_timing.* files and parse each one."""
    files = []
    for item in inputs:
        if os.path.isdir(item):
            files += glob.glob(os.path.join(item, "cesm_timing.*"))
        else:
            files.append(item)
    files = [f for f in files if "ESMF_Profile" not in os.path.basename(f)]
    if not files:
        raise SystemExit("no cesm_timing.* files found")

    runs = {}
    for f in sorted(files):
        rec = parse_timing(f)
        # keep the newest report per PE layout, so a re-run supersedes its predecessor
        key = (rec["wav_pes"], rec["total_pes"])
        prev = runs.get(key)
        if prev is None or os.path.getmtime(f) > os.path.getmtime(prev["path"]):
            runs[key] = rec
    wav_pes = [k[0] for k in runs]
    clash = sorted({p for p in wav_pes if wav_pes.count(p) > 1})
    if clash:
        raise SystemExit(f"different PE layouts at {clash} WW3 tasks; pass one layout per task count")
    return [runs[k] for k in sorted(runs)]


def plot(runs, out, title, dark):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    c = THEME["dark" if dark else "light"]
    pes = [r["wav_pes"] for r in runs]
    sypd = [r["sypd"] for r in runs]
    base_pes, base_sypd = pes[0], sypd[0]
    ideal = [base_sypd * p / base_pes for p in pes]
    eff = [100.0 * s / i for s, i in zip(sypd, ideal)]

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.3), dpi=200)
    fig.patch.set_facecolor(c["surface"])

    line_kw = dict(color=c["series"], lw=2, marker="o", ms=6.5,
                   markeredgecolor=c["surface"], markeredgewidth=1.5, zorder=3)

    ax = axes[0]
    ax.plot(pes, ideal, color=c["muted"], lw=1.5, ls="--", zorder=2,
            label=f"ideal (from {base_pes} tasks)")
    ax.plot(pes, sypd, label="measured", **line_kw)
    ax.set_ylabel("throughput  (simulated years / day)", color=c["muted"], fontsize=9)
    ax.set_title("Throughput", color=c["ink"], fontsize=11, loc="left", pad=10)
    ax.set_ylim(0, max(ideal) * 1.08)
    leg = ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    for t in leg.get_texts():
        t.set_color(c["muted"])
    # label the endpoint only; the full numbers go to stdout
    ax.annotate(f"{sypd[-1]:.2f}", (pes[-1], sypd[-1]), textcoords="offset points",
                xytext=(-4, -14), ha="right", fontsize=8.5, color=c["muted"])

    ax = axes[1]
    ax.axhline(100, color=c["grid"], lw=1.5, zorder=1)
    ax.plot(pes, eff, **line_kw)
    ax.set_ylabel("parallel efficiency  (% of ideal)", color=c["muted"], fontsize=9)
    ax.set_title("Parallel efficiency", color=c["ink"], fontsize=11, loc="left", pad=10)
    ax.set_ylim(0, 115)
    ax.annotate(f"{eff[-1]:.0f}%", (pes[-1], eff[-1]), textcoords="offset points",
                xytext=(-4, -14), ha="right", fontsize=8.5, color=c["muted"])

    for ax in axes:
        ax.set_facecolor(c["surface"])
        ax.set_xlabel("WW3 tasks", color=c["muted"], fontsize=9)
        ax.set_xticks(pes)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}"))
        ax.grid(axis="y", color=c["grid"], lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(c["grid"])
        ax.tick_params(colors=c["muted"], labelsize=8.5, length=0)

    if title:
        fig.suptitle(title, color=c["ink"], fontsize=12.5, x=0.012, ha="left", y=0.97)
        fig.tight_layout(rect=(0, 0, 1, 0.945))
    else:
        fig.tight_layout()
    fig.savefig(out, facecolor=c["surface"])
    return eff


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="timing directories or cesm_timing.* files")
    ap.add_argument("-o", "--out", default="ww3_scaling.png")
    ap.add_argument("--title", default="")
    ap.add_argument("--dark", action="store_true", help="render on the dark surface")
    args = ap.parse_args()

    runs = collect(args.inputs)
    if len(runs) < 2:
        raise SystemExit("need at least two task counts to plot a scaling curve")

    eff = plot(runs, args.out, args.title, args.dark)

    print(f"{'WW3 tasks':>10} {'nodes':>6} {'s/mday':>9} {'SYPD':>7} "
          f"{'pe-hr/yr':>10} {'WAV %':>6} {'effic':>7}")
    for r, e in zip(runs, eff):
        print(f"{r['wav_pes']:>10d} {r['wav_pes']/128:>6.0f} {r['sec_per_mday']:>9.1f} "
              f"{r['sypd']:>7.3f} {r['cost']:>10.0f} {100*r['wav_frac']:>5.1f}% {e:>6.1f}%")
    print(f"\nwrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
