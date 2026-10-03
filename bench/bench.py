"""Simple nginx vs FastAPI static serving benchmark -> results/<time>/report.html

For each server and URL: oha runs a short warm-up, then a measured run with
N keep-alive connections. While it runs, `docker stats` samples the server's
CPU and memory. Only one server is under load at a time.

    python3 bench/bench.py                    # all servers, 10s per URL
    python3 bench/bench.py --duration 5 --servers nginx fastapi
"""

import argparse
import json
import subprocess
import threading
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "report_template.html"
OHA = "ghcr.io/hatoo/oha:latest"
NETWORK = "bench"  # from docker-compose.yml
SERVERS = ["nginx", "fastapi", "nginx-tuned"]

# accept: what a browser sends. text/html makes /any/deep/link a page
# navigation, so FastAPI answers with the index.html fallback like nginx does.
SCENARIOS = [
    {"key": "index", "label": "index.html", "path": "/", "accept": "text/html"},
    {"key": "deep_link", "label": "SPA deep link", "path": "/any/deep/link", "accept": "text/html"},
    {"key": "vendor_js", "label": "vendor.js (220 KB)", "path": "/assets/vendor.js", "accept": "*/*"},
    {"key": "hero_webp", "label": "hero.webp (215 KB)", "path": "/assets/hero.webp", "accept": "image/webp"},
]


def sh(*cmd: str) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def container_id(server: str) -> str:
    cid = sh("docker", "compose", "ps", "-q", server).strip()
    if not cid:
        raise SystemExit(f"{server} is not running, start it with `make up`")
    return cid


def oha(url: str, accept: str, seconds: int, connections: int, cpuset: str) -> dict:
    out = sh(
        "docker", "run", "--rm", "--network", NETWORK, "--cpuset-cpus", cpuset, OHA,
        "--no-tui", "--output-format", "json", "-z", f"{seconds}s", "-c", str(connections),
        "-H", f"Accept: {accept}", "-H", "Accept-Encoding: gzip, deflate, br", url,
    )
    return json.loads(out)


class StatsSampler(threading.Thread):
    """Samples `docker stats` (CPU %, memory) of one container until stopped."""

    def __init__(self, cid: str):
        super().__init__(daemon=True)
        self.cid, self.cpu, self.mem = cid, [], []
        self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            line = sh("docker", "stats", "--no-stream", "--format", "{{json .}}", self.cid)
            s = json.loads(line)
            self.cpu.append(float(s["CPUPerc"].rstrip("%")))
            self.mem.append(parse_mib(s["MemUsage"].split("/")[0].strip()))


def parse_mib(v: str) -> float:
    for unit, mul in (("GiB", 1024), ("MiB", 1), ("KiB", 1 / 1024), ("B", 1 / 1024 / 1024)):
        if v.endswith(unit):
            return float(v[: -len(unit)]) * mul
    return 0.0


def run_one(server: str, cid: str, sc: dict, args) -> dict:
    url = f"http://{server}{sc['path']}"
    oha(url, sc["accept"], args.warmup, args.connections, args.loadgen_cpus)  # warm-up, ignored
    sampler = StatsSampler(cid)
    sampler.start()
    r = oha(url, sc["accept"], args.duration, args.connections, args.loadgen_cpus)
    sampler.stop.set()
    sampler.join()

    codes = {int(k): v for k, v in r["statusCodeDistribution"].items()}
    # requests still in flight when the timer ends are cut by oha, not real errors
    conn_errors = sum(v for k, v in r["errorDistribution"].items() if "deadline" not in k)
    lat = r["latencyPercentiles"]
    cpu = sampler.cpu[1:] or sampler.cpu  # first sample overlaps the start
    return {
        "server": server,
        "scenario": sc["key"],
        "rps": r["summary"]["requestsPerSec"],
        "p50_ms": lat["p50"] * 1000,
        "p99_ms": lat["p99"] * 1000,
        "bytes_per_response": r["summary"]["sizePerRequest"] or 0,
        "errors": sum(v for k, v in codes.items() if k >= 400) + conn_errors,
        "status_codes": codes,
        "cpu_percent": sum(cpu) / len(cpu) if cpu else 0,
        "mem_mib": max(sampler.mem) if sampler.mem else 0,
    }


def write_report(payload: dict, out_dir: Path) -> Path:
    html = TEMPLATE.read_text().replace("__DATA__", json.dumps(payload))
    path = out_dir / "report.html"
    path.write_text(html)
    return path


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--servers", nargs="+", default=SERVERS, choices=SERVERS)
    p.add_argument("--duration", type=int, default=10, help="measured seconds per URL (default 10)")
    p.add_argument("--warmup", type=int, default=2, help="warm-up seconds per URL (default 2)")
    p.add_argument("--connections", type=int, default=64, help="concurrent connections (default 64)")
    p.add_argument("--loadgen-cpus", default="1-4", help="cores for oha, not the servers' core 0 (default 1-4)")
    p.add_argument("--report-only", type=Path, metavar="DIR", help="rebuild report.html from DIR/results.json")
    args = p.parse_args()

    if args.report_only:
        payload = json.loads((args.report_only / "results.json").read_text())
        print(write_report(payload, args.report_only))
        return

    print("Pulling oha …")
    sh("docker", "pull", "-q", OHA)
    started = datetime.now()
    results = []
    for server in args.servers:
        cid = container_id(server)
        for sc in SCENARIOS:
            print(f"  {server:12s} {sc['label']:22s}", end=" ", flush=True)
            res = run_one(server, cid, sc, args)
            results.append(res)
            print(f"{res['rps']:>10,.0f} req/s   p99 {res['p99_ms']:6.2f} ms   "
                  f"cpu {res['cpu_percent']:5.0f}%   mem {res['mem_mib']:5.1f} MiB   errors {res['errors']}")

    payload = {
        "started": started.isoformat(timespec="seconds"),
        "config": {
            "duration_s": args.duration,
            "warmup_s": args.warmup,
            "connections": args.connections,
            "server_cpus": int(sh("docker", "inspect", "-f", "{{.HostConfig.NanoCpus}}", container_id(args.servers[0])).strip()) / 1e9,
        },
        "servers": args.servers,
        "scenarios": SCENARIOS,
        "results": results,
    }
    out_dir = ROOT / "results" / started.strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True)
    (out_dir / "results.json").write_text(json.dumps(payload, indent=2))
    print(f"\nReport: {write_report(payload, out_dir)}")


if __name__ == "__main__":
    main()
