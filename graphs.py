import os
import re
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "locust-results"
OUTPUT_DIR  = "graphs"
SCENARIOS   = ["img-150kb", "text-400kb", "img-300kb"]
INSTANCES   = [1, 2, 3]
USERS       = [10, 100, 1000]
PATTERN     = re.compile(r"^(\d+)inst-(\d+)users-(.+)_stats\.csv$")

COLORS_INST = {1: "#4C72B0", 2: "#DD8452", 3: "#55A868"}
COLORS_USER = {10: "#4C72B0", 100: "#DD8452", 1000: "#55A868"}


def load_data():
    if not os.path.isdir(RESULTS_DIR):
        sys.exit(f"Diretório não encontrado: {RESULTS_DIR}")
    data = {}
    for fname in sorted(os.listdir(RESULTS_DIR)):
        m = PATTERN.match(fname)
        if not m:
            continue
        inst, users, scenario = int(m.group(1)), int(m.group(2)), m.group(3)
        try:
            df = pd.read_csv(os.path.join(RESULTS_DIR, fname))
        except Exception as e:
            print(f"[skip] {fname}: {e}")
            continue
        agg = df[df["Name"].astype(str).str.strip() == "Aggregated"]
        if agg.empty:
            agg = df.tail(1)
        if agg.empty:
            continue
        row = agg.iloc[0]
        requests = int(row["Request Count"])
        if requests == 0:
            print(f"[aviso] {fname}: 0 requisições (teste falhou?) - ponto omitido")
            continue
        data[(inst, users, scenario)] = {
            "avg_ms":   float(row["Average Response Time"]),
            "rps":      float(row["Requests/s"]),
            "requests": requests,
            "failures": int(row["Failure Count"]),
        }
    return data


def annotate(ax, bars, values, fmt="{:.0f}"):
    for bar, val in zip(bars, values):
        if np.isnan(val):
            continue
        ax.annotate(fmt.format(val),
                    xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)


def chart_response_time(data):
    """X = usuários, barras por instância, Y = tempo de resposta médio."""
    fig, axes = plt.subplots(1, len(SCENARIOS), figsize=(18, 5), sharey=True)
    width = 0.25
    x = np.arange(len(USERS))
    for ax, scenario in zip(axes, SCENARIOS):
        for i, inst in enumerate(INSTANCES):
            vals = [data.get((inst, u, scenario), {}).get("avg_ms", np.nan) for u in USERS]
            offset = (i - (len(INSTANCES) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width,
                          label=f"{inst} inst", color=COLORS_INST[inst])
            annotate(ax, bars, vals)
        ax.set_xticks(x)
        ax.set_xticklabels([str(u) for u in USERS])
        ax.set_xlabel("Usuários")
        ax.set_title(scenario)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    axes[0].set_ylabel("Tempo de resposta médio (ms)")
    axes[0].legend(title="Instâncias", loc="upper left")
    fig.suptitle("Tempo de resposta médio — por usuários e instâncias", fontsize=14, y=1.02)
    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "response_time_by_users.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"salvo: {out}")


def chart_rps(data):
    """X = instâncias, barras por usuários, Y = requisições por segundo."""
    fig, axes = plt.subplots(1, len(SCENARIOS), figsize=(18, 5), sharey=True)
    width = 0.25
    x = np.arange(len(INSTANCES))
    for ax, scenario in zip(axes, SCENARIOS):
        for i, u in enumerate(USERS):
            vals = [data.get((inst, u, scenario), {}).get("rps", np.nan) for inst in INSTANCES]
            offset = (i - (len(USERS) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width,
                          label=f"{u} usuários", color=COLORS_USER[u])
            annotate(ax, bars, vals, fmt="{:.1f}")
        ax.set_xticks(x)
        ax.set_xticklabels([f"{i} inst" for i in INSTANCES])
        ax.set_xlabel("Instâncias WordPress")
        ax.set_title(scenario)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    axes[0].set_ylabel("Requisições por segundo (RPS)")
    axes[0].legend(title="Usuários", loc="upper left")
    fig.suptitle("Throughput (RPS) — por instâncias e usuários", fontsize=14, y=1.02)
    plt.tight_layout()
    out = os.path.join(OUTPUT_DIR, "rps_by_instances.png")
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"salvo: {out}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    data = load_data()
    if not data:
        sys.exit("Nenhum CSV encontrado em " + RESULTS_DIR)
    print(f"Carregados {len(data)} pontos.\n")

    print(f"{'cenário':<14} {'inst':>4} {'users':>6} {'reqs':>6} {'fails':>6} {'avg(ms)':>8} {'rps':>8}")
    print("-" * 60)
    for scenario in SCENARIOS:
        for inst in INSTANCES:
            for u in USERS:
                d = data.get((inst, u, scenario))
                if not d:
                    print(f"{scenario:<14} {inst:>4} {u:>6} {'---':>6}")
                    continue
                print(f"{scenario:<14} {inst:>4} {u:>6} {d['requests']:>6} "
                      f"{d['failures']:>6} {d['avg_ms']:>8.1f} {d['rps']:>8.2f}")
    print()

    chart_response_time(data)
    chart_rps(data)


if __name__ == "__main__":
    main()