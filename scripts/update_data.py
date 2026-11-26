"""Download CelesTrak orbits (active satellites) and owners (SATCAT), join them,
and write data/sats.json in the compact row format the page reads.

Row: [norad, name, intl_designator, owner, launch_date, epoch_ms,
      mean_motion_rev_per_day, eccentricity, inclination_deg, raan_deg,
      arg_perigee_deg, mean_anomaly_deg, mean_motion_dot]
"""
import csv, io, json, os, sys, time, urllib.request
from datetime import datetime, timezone

UA = "satellite-tracker (github.com/tonyferg1976/satellite-tracker; scheduled update)"
GP_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=json"
SATCAT_URLS = [
    "https://celestrak.org/satcat/records.php?GROUP=active&FORMAT=csv",
    "https://celestrak.org/pub/satcat.csv",
]
WORKING = {"+", "P", "B", "S", "X"}
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "sats.json")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace")


def epoch_ms(s):
    s = str(s).strip().replace("Z", "")
    dt = datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def load_previous():
    try:
        with open(OUT) as f:
            return {r[0]: r for r in json.load(f)["rows"]}
    except Exception:
        return {}


def main():
    gp = json.loads(get(GP_URL))
    if not isinstance(gp, list) or len(gp) < 1000:
        sys.exit(f"Orbit download looks wrong ({type(gp).__name__}, {len(gp) if isinstance(gp, list) else 0} records); keeping old data.")

    cat = None
    for url in SATCAT_URLS:
        try:
            time.sleep(2)  # be gentle with CelesTrak
            text = get(url)
            rows = list(csv.DictReader(io.StringIO(text)))
            if rows and "OWNER" in rows[0]:
                cat = {int(r["NORAD_CAT_ID"]): r for r in rows if r.get("NORAD_CAT_ID", "").strip().isdigit()}
                print(f"SATCAT: {len(cat)} records from {url}")
                break
        except Exception as e:
            print(f"SATCAT download failed from {url}: {e}")
    prev = load_previous() if cat is None else {}
    if cat is None:
        print(f"Using owners from previous data ({len(prev)} records).")

    best = {}
    for g in gp:
        try:
            nid = int(g["NORAD_CAT_ID"]); ep = epoch_ms(g["EPOCH"]); n = float(g["MEAN_MOTION"])
        except Exception:
            continue
        if n > 0 and (nid not in best or best[nid][1] < ep):
            best[nid] = (g, ep)

    out, dropped = [], 0
    for nid, (g, ep) in best.items():
        owner, launch = "UNK", ""
        if cat is not None:
            c = cat.get(nid)
            if c:
                st = (c.get("OPS_STATUS_CODE") or "").strip()
                typ = (c.get("OBJECT_TYPE") or "").strip()
                if (st and st not in WORKING) or (typ and typ != "PAY"):
                    dropped += 1
                    continue
                owner = (c.get("OWNER") or "").strip() or "UNK"
                launch = (c.get("LAUNCH_DATE") or "").strip()
        elif nid in prev:
            owner, launch = prev[nid][3], prev[nid][4]
            if owner == "STARLINK":
                owner = "US"
        name = (g.get("OBJECT_NAME") or "").strip()
        if owner == "US" and name.upper().startswith("STARLINK"):
            owner = "STARLINK"
        f = lambda k: float(g.get(k) or 0)
        out.append([nid, name, g.get("OBJECT_ID") or "", owner, launch, ep,
                    f("MEAN_MOTION"), f("ECCENTRICITY"), f("INCLINATION"), f("RA_OF_ASC_NODE"),
                    f("ARG_OF_PERICENTER"), f("MEAN_ANOMALY"), f("MEAN_MOTION_DOT")])

    out.sort(key=lambda r: r[0])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "source": "CelesTrak GP (active) + SATCAT", "rows": out}, fh, separators=(",", ":"))
    print(f"Wrote {len(out)} working satellites ({dropped} non-working dropped).")


if __name__ == "__main__":
    main()
