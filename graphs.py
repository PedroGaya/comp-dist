import argparse
import os
import re
import sys

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

PATTERN = re.compile(r"^(\d+)inst-(\d+)users-(.+)_stats\.csv$")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="locust-results", help="pasta com os CSVs")
    p.add_argument("--out", default="graphs", help="pasta de saida")
    p.add_argument("--log", action="store_true", help="eixo Y em escala log")
    p.add_argument("--line", action="store_true", help="tempo de resposta em linha")
    p.add_argument("--dpi", type=int, default=150)
    return p.parse_args()


def discover(results_dir):
    data = {}
    scenarios, instances, users = set(), set(), set()

    for fname in sorted(os.listdir(results_dir)):
        m = PATTERN.match(fname)
        if not m:
            continue
        inst, usr, scen = int(m.group(1)), int(m.group(2)), m.group(3)
        path = os.path.join(results_dir, fname)
        try:
            df = pd.read_csv(path)
        except Exception as e:
            print(f"[skip] {fname}: {e}")
            continue

        agg = df[df["Name"].astype(str).str.strip() == "Aggregated"]
        if agg.empty:
            agg = df.tail(1)
        if agg.empty:
            print(f"[skip] {fname}: sem linhas")
            continue

        row = agg.iloc[0]
        reqs = int(row.get("Request Count", 0))
        if reqs == 0:
            print(f"[skip] {fname}: 0 requests")
            continue

        data[(inst, usr, scen)] = {
            "avg_ms":   float(row["Average Response Time"]),
            "median":   float(row.get("Median Response Time", np.nan)),
            "p95":      float(row.get("95%", np.nan)),
            "p99":      float(row.get("99%", np.nan)),
            "rps":      float(row["Requests/s"]),
            "requests": reqs,
            "failures": int(row.get("Failure Count", 0)),
        }
        scenarios.add(scen)
        instances.add(inst)
        users.add(usr)

    return data, sorted(scenarios), sorted(instances), sorted(users)


def auto_scale(values):
    vals = [v for v in values if not np.isnan(v) and v > 0]
    if len(vals) < 2:
        return "linear"
    return "log" if max(vals) / min(vals) > 20 else "linear"


def annotate(ax, bars, values, fmt="{:.0f}"):
    for bar, val in zip(bars, values):
        if np.isnan(val):
            continue
        ax.annotate(fmt.format(val),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)


def get_colors(keys):
    cmap = plt.get_cmap("tab10")
    return {k: cmap(i % 10) for i, k in enumerate(keys)}


def chart_response_time(data, scenarios, instances, users,
                        out_path, use_log=False, use_line=False):
    n = len(scenarios)
    fig, axes = plt.subplots(1, n, figsize=(max(5 * n, 8), 5), squeeze=False)
    axes = axes[0]
    colors = get_colors(instances)
    width = 0.8 / max(len(instances), 1)
    x = np.arange(len(users))

    for ax, scen in zip(axes, scenarios):
        if use_line:
            for inst in instances:
                vals = [data.get((inst, u, scen), {}).get("avg_ms", np.nan) for u in users]
                if all(np.isnan(vals)):
                    continue
                ax.plot(users, vals, marker="o", linewidth=2,
                        label=f"{inst} inst", color=colors[inst])
            ax.set_xscale("log")
            ax.set_xticks(users)
            ax.set_xticklabels([str(u) for u in users])
            for lbl in ax.get_xticklabels():
                lbl.set_rotation(0)
        else:
            for i, inst in enumerate(instances):
                vals = [data.get((inst, u, scen), {}).get("avg_ms", np.nan) for u in users]
                if all(np.isnan(vals)):
                    continue
                offset = (i - (len(instances) - 1) / 2) * width
                bars = ax.bar(x + offset, vals, width,
                              label=f"{inst} inst", color=colors[inst])
                annotate(ax, bars, vals)

        ax.set_xticks(x)
        ax.set_xticklabels([str(u) for u in users])
        ax.set_xlabel("Usuarios")
        ax.set_title(scen)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        all_vals = [data.get((i, u, scen), {}).get("avg_ms", np.nan)
                    for i in instances for u in users]
        if use_log or auto_scale(all_vals) == "log":
            ax.set_yscale("log")

    axes[0].set_ylabel("Tempo de resposta medio (ms)")
    axes[0].legend(title="Instancias", loc="best")
    fig.suptitle("Tempo de resposta medio", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"salvo: {out_path}")


def chart_rps(data, scenarios, instances, users, out_path, use_log=False):
    n = len(scenarios)
    fig, axes = plt.subplots(1, n, figsize=(max(5 * n, 8), 5), squeeze=False)
    axes = axes[0]
    colors = get_colors(users)
    width = 0.8 / max(len(users), 1)
    x = np.arange(len(instances))

    for ax, scen in zip(axes, scenarios):
        for i, u in enumerate(users):
            vals = [data.get((inst, u, scen), {}).get("rps", np.nan) for inst in instances]
            if all(np.isnan(vals)):
                continue
            offset = (i - (len(users) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width,
                          label=f"{u} usuarios", color=colors[u])
            annotate(ax, bars, vals, fmt="{:.1f}")

        ax.set_xticks(x)
        ax.set_xticklabels([f"{i} inst" for i in instances])
        ax.set_xlabel("Instancias WordPress")
        ax.set_title(scen)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        all_vals = [data.get((i, u, scen), {}).get("rps", np.nan)
                    for i in instances for u in users]
        if use_log or auto_scale(all_vals) == "log":
            ax.set_yscale("log")

    axes[0].set_ylabel("Requisicoes por segundo")
    axes[0].legend(title="Usuarios", loc="best")
    fig.suptitle("Throughput (RPS)", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"salvo: {out_path}")


def chart_failures(data, scenarios, instances, users, out_path):
    n = len(scenarios)
    fig, axes = plt.subplots(1, n, figsize=(max(5 * n, 8), 5), squeeze=False)
    axes = axes[0]
    colors = get_colors(instances)
    width = 0.8 / max(len(instances), 1)
    x = np.arange(len(users))

    for ax, scen in zip(axes, scenarios):
        for i, inst in enumerate(instances):
            vals = [data.get((inst, u, scen), {}).get("failures", np.nan) for u in users]
            if all(np.isnan(vals)):
                continue
            offset = (i - (len(instances) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width,
                          label=f"{inst} inst", color=colors[inst])
            annotate(ax, bars, vals)
        ax.set_xticks(x)
        ax.set_xticklabels([str(u) for u in users])
        ax.set_xlabel("Usuarios")
        ax.set_title(scen)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    axes[0].set_ylabel("Falhas")
    axes[0].legend(title="Instancias", loc="best")
    fig.suptitle("Falhas por cenario", fontsize=14, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"salvo: {out_path}")


def print_summary(data, scenarios, instances, users):
    print(f"\n{'cenario':<14} {'inst':>4} {'users':>6} {'reqs':>6} {'fails':>6} {'avg_ms':>8} {'rps':>8}")
    print("-" * 60)
    total = 0
    for scen in scenarios:
        for inst in instances:
            for u in users:
                d = data.get((inst, u, scen))
                if not d:
                    print(f"{scen:<14} {inst:>4} {u:>6} {'---':>6}")
                    continue
                print(f"{scen:<14} {inst:>4} {u:>6} {d['requests']:>6} "
                      f"{d['failures']:>6} {d['avg_ms']:>8.1f} {d['rps']:>8.2f}")
                total += 1
    expected = len(scenarios) * len(instances) * len(users)
    print(f"\n{total}/{expected} combinacoes presentes")
    if total < expected:
        print("Faltando:", expected - total, "ponto(s)")


def main():
    args = parse_args()
    os.makedirs(args.out, exist_ok=True)

    data, scenarios, instances, users = discover(args.dir)
    if not data:
        sys.exit(f"Nenhum CSV valido em {args.dir}")

    print(f"Detectado: {len(scenarios)} cenario(s), "
          f"{len(instances)} instancia(s) {instances}, "
          f"{len(users)} usuario(s) {users}\n")

    print_summary(data, scenarios, instances, users)

    suffix = "_log" if args.log else ""
    suffix += "_line" if args.line else ""

    chart_response_time(
        data, scenarios, instances, users,
        os.path.join(args.out, f"response_time{suffix}.png"),
        use_log=args.log, use_line=args.line,
    )
    chart_rps(
        data, scenarios, instances, users,
        os.path.join(args.out, f"rps{suffix}.png"),
        use_log=args.log,
    )
    chart_failures(
        data, scenarios, instances, users,
        os.path.join(args.out, f"failures{suffix}.png"),
    )


if __name__ == "__main__":
    main()