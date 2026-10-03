"""nginx vs FastAPI benchmark -> results/<time>/report.html

Start the servers first (`make up`), then: python3 bench/bench.py

For each server and URL, oha (in Docker, on its own CPU cores) does a short
warm-up and then a measured run. CPU and memory come from the server
container's cgroup. One server is under load at a time.
"""

import json
import subprocess
from datetime import datetime
from html import escape
from pathlib import Path

DURATION = 10       # measured seconds per URL
WARMUP = 2          # seconds, results ignored
CONNECTIONS = 64
LOADGEN_CPUS = "1-4"  # servers are pinned to core 0 in docker-compose.yml

HERE = Path(__file__).resolve().parent
OHA = "ghcr.io/hatoo/oha:latest"
SERVERS = ["nginx", "fastapi", "nginx-tuned"]
URLS = [
    # text/html = browser page navigation, so FastAPI serves the SPA fallback like nginx
    ("index.html", "/", "text/html"),
    ("SPA deep link", "/any/deep/link", "text/html"),
    ("vendor.js 220 KB", "/assets/vendor.js", "*/*"),
    ("hero.webp 215 KB", "/assets/hero.webp", "image/webp"),
]


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def oha(url: str, accept: str, seconds: int) -> dict:
    return json.loads(sh(
        "docker", "run", "--rm", "--network", "bench", "--cpuset-cpus", LOADGEN_CPUS, OHA,
        "--no-tui", "--output-format", "json", "-z", f"{seconds}s", "-c", str(CONNECTIONS),
        "-H", f"Accept: {accept}", "-H", "Accept-Encoding: gzip, deflate, br", url,
    ))


def cgroup(cid: str) -> tuple[int, int]:
    """Server container's total CPU time (µs) and current memory (bytes)."""
    out = sh("docker", "exec", cid, "sh", "-c",
             "grep usage_usec /sys/fs/cgroup/cpu.stat; cat /sys/fs/cgroup/memory.current")
    cpu_line, mem = out.split("\n")[:2]
    return int(cpu_line.split()[1]), int(mem)


def measure(server: str, cid: str, path: str, accept: str) -> dict:
    url = f"http://{server}{path}"
    oha(url, accept, WARMUP)
    cpu_before, _ = cgroup(cid)
    r = oha(url, accept, DURATION)
    cpu_after, mem = cgroup(cid)

    bad_status = sum(v for k, v in r["statusCodeDistribution"].items() if int(k) >= 400)
    # requests cut off by the end of the run are not errors
    conn_errors = sum(v for k, v in r["errorDistribution"].items() if "deadline" not in k)
    return {
        "rps": r["summary"]["requestsPerSec"],
        "p99_ms": r["latencyPercentiles"]["p99"] * 1000,
        "bytes": r["summary"]["sizePerRequest"] or 0,
        "errors": bad_status + conn_errors,
        # % of one CPU core used during the run
        "cpu": (cpu_after - cpu_before) / (r["summary"]["total"] * 1e6) * 100,
        "mem_mib": mem / 1024**2,
    }


def report(results: dict, started: datetime) -> str:
    servers = [s for s in SERVERS if s in results]

    def cell(server: str, label: str) -> str:
        r = results[server][label]
        top = max(results[s][label]["rps"] for s in servers)
        err = f' <span class="err">{r["errors"]:,} errors</span>' if r["errors"] else ""
        return (f'<td><div class="bar s-{server}" style="width:{r["rps"] / top * 100:.1f}%"></div>'
                f'<b>{r["rps"]:,.0f}</b> req/s{err}<br><small>p99 {r["p99_ms"]:.2f} ms · {r["bytes"] / 1024:.1f} KB</small></td>')

    def summary_row(name: str, fn) -> str:
        return f"<tr class='sum'><th>{name}</th>" + "".join(f"<td>{fn(results[s])}</td>" for s in servers) + "</tr>"

    head = "".join(f'<th><i class="dot s-{s}"></i>{escape(s)}</th>' for s in servers)
    rows = "".join(f"<tr><th>{escape(label)}</th>" + "".join(cell(s, label) for s in servers) + "</tr>"
                   for label, _, _ in URLS)
    rows += summary_row("memory", lambda r: f"{max(x['mem_mib'] for x in r.values()):.1f} MiB")
    rows += summary_row("CPU used", lambda r: f"{sum(x['cpu'] for x in r.values()) / len(r):.0f}%")

    tiles = ""
    if {"nginx", "fastapi"} <= set(servers):
        n, f = results["nginx"]["index.html"]["rps"], results["fastapi"]["index.html"]["rps"]
        tiles = (f'<div class="tile"><small>FastAPI, index.html</small><b>{f:,.0f} req/s</b>'
                 f'<small>≈ {f * 86400 / 1e6:,.0f} million requests a day</small></div>'
                 f'<div class="tile"><small>nginx vs FastAPI, index.html</small><b>{n / f:.1f}× faster</b>'
                 f'<small>{n:,.0f} vs {f:,.0f} req/s</small></div>')

    meta = (f"{started:%Y-%m-%d %H:%M} · 1 CPU per server · {CONNECTIONS} connections · "
            f"{DURATION}s per URL · CPU near 100% = server was the bottleneck")
    return ((HERE / "report_template.html").read_text()
            .replace("{{meta}}", meta).replace("{{tiles}}", tiles)
            .replace("{{head}}", head).replace("{{rows}}", rows))


def main() -> None:
    sh("docker", "pull", "-q", OHA)
    started = datetime.now()
    results = {}
    for server in SERVERS:
        cid = sh("docker", "compose", "ps", "-q", server).strip()
        if not cid:
            print(f"{server} is not running, skipped (start it with `make up`)")
            continue
        results[server] = {}
        for label, path, accept in URLS:
            print(f"{server:12s} {label:18s}", end=" ", flush=True)
            r = results[server][label] = measure(server, cid, path, accept)
            print(f"{r['rps']:>9,.0f} req/s  p99 {r['p99_ms']:6.2f} ms  "
                  f"cpu {r['cpu']:4.0f}%  mem {r['mem_mib']:5.1f} MiB  errors {r['errors']}")

    if not results:
        raise SystemExit("no servers running, start them with `make up`")
    out = HERE.parent / "results" / f"{started:%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    (out / "results.json").write_text(json.dumps(results, indent=2))
    (out / "report.html").write_text(report(results, started))
    print(f"\nReport: {out / 'report.html'}")


if __name__ == "__main__":
    main()
