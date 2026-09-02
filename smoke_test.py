"""
Post-deploy smoke test — run this AFTER your Render backend is live to
confirm the whole chain (DB -> PostGIS -> risk engine -> API) actually
works in production, not just locally.

Usage:
    python smoke_test.py https://himalayan-ai-backend.onrender.com

Exits with a non-zero code and prints which check failed, so you can
paste the output back if something's wrong.
"""

import sys
import requests

def check(name, fn):
    try:
        fn()
        print(f"  OK   {name}")
        return True
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python smoke_test.py <backend_url>")
        sys.exit(1)
    base = sys.argv[1].rstrip("/")
    results = []

    def root_ok():
        r = requests.get(f"{base}/", timeout=30)
        assert r.status_code == 200, f"status {r.status_code}"
        assert "product" in r.json()

    def locations_ok():
        r = requests.get(f"{base}/api/locations", timeout=30)
        assert r.status_code == 200, f"status {r.status_code}"
        data = r.json()["data"]
        assert len(data) == 8, f"expected 8 locations, got {len(data)} — did schema.sql seed run?"
        return data

    def risk_all_ok():
        r = requests.get(f"{base}/api/risk/all", timeout=30)
        assert r.status_code == 200, f"status {r.status_code}"
        data = r.json()["data"]
        assert len(data) > 0, "no risk data — did seed_demo_data.py or ingest_real_data.py run?"
        first = data[0]
        for key in ("location_id", "location", "overall_risk", "hazards"):
            assert key in first, f"missing key '{key}' in risk response"
        for hz in ("landslide", "flood", "glof", "avalanche", "fire"):
            assert hz in first["hazards"], f"missing hazard '{hz}'"

    def alerts_ok():
        r = requests.get(f"{base}/api/alerts?min_risk=0", timeout=30)
        assert r.status_code == 200, f"status {r.status_code}"
        assert "data" in r.json() and "disclaimer" in r.json()

    def data_sources_ok():
        r = requests.get(f"{base}/api/data-sources", timeout=30)
        assert r.status_code == 200, f"status {r.status_code}"

    print(f"Running smoke test against {base}\n"
          f"(first request may take ~1 min if the free-tier service was asleep)\n")

    results.append(check("Root endpoint reachable", root_ok))
    results.append(check("8 locations seeded (PostGIS working)", locations_ok))
    results.append(check("/api/risk/all shape correct", risk_all_ok))
    results.append(check("/api/alerts reachable", alerts_ok))
    results.append(check("/api/data-sources reachable", data_sources_ok))

    print()
    if all(results):
        print("All checks passed — backend is live and correctly wired.")
        sys.exit(0)
    else:
        print(f"{results.count(False)} check(s) failed — see FAIL lines above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
