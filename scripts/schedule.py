#!/usr/bin/env python3
"""Download today's and tomorrow's scheduled flights from ANAC (Brazil's civil aviation
agency, SIROS open API) and write one small departures file per Brazilian airport for the board.

Output: data/schedule/<ICAO>.json  and  data/schedule/index.json (IATA -> ICAO).
Runs on GitHub Actions; uses only the Python standard library.
"""
import csv, io, json, os, sys, time, unicodedata, urllib.request
from datetime import datetime, timedelta, timezone

ANAC = "https://sas.anac.gov.br/sas/siros_api/api/voos?dataReferencia={d}"
AIRPORTS = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
AIRLINES = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "schedule")
BRT = timezone(timedelta(hours=-3))

# Names people expect on a departures board, where the airport's town differs from the city it serves.
CITY = {
    "SBGR": "SAO PAULO", "SBSP": "SAO PAULO", "SBKP": "CAMPINAS", "SBCF": "BELO HORIZONTE",
    "SBGL": "RIO DE JANEIRO", "SBRJ": "RIO DE JANEIRO", "SBBR": "BRASILIA", "SBSV": "SALVADOR",
    "SBRF": "RECIFE", "SBFZ": "FORTALEZA", "SBPA": "PORTO ALEGRE", "SBCT": "CURITIBA",
    "SBFL": "FLORIANOPOLIS", "SBSG": "NATAL", "SBEG": "MANAUS", "SBBE": "BELEM",
    "KJFK": "NEW YORK", "KEWR": "NEWARK", "KMIA": "MIAMI", "KMCO": "ORLANDO", "KATL": "ATLANTA",
    "KIAH": "HOUSTON", "KDFW": "DALLAS", "KORD": "CHICAGO", "LFPG": "PARIS", "EGLL": "LONDON",
    "LEMD": "MADRID", "LPPT": "LISBON", "LPPR": "PORTO", "LIRF": "ROME", "LIMC": "MILAN",
    "EDDF": "FRANKFURT", "EHAM": "AMSTERDAM", "LSZH": "ZURICH", "OMDB": "DUBAI", "OTHH": "DOHA",
    "SAEZ": "BUENOS AIRES", "SABE": "BUENOS AIRES", "SCEL": "SANTIAGO", "SPJC": "LIMA",
    "SKBO": "BOGOTA", "SUMU": "MONTEVIDEO", "MPTO": "PANAMA", "SGAS": "ASUNCION", "MMMX": "MEXICO CITY",
}
# ICAO -> IATA airline codes where the open list is missing or ambiguous.
AIRLINE = {"TAM": "LA", "LAN": "LA", "GLO": "G3", "AZU": "AD", "TAP": "TP", "PTB": "2Z", "VOE": "VO"}


def get(url, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "flapboard-schedule/1.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # ANAC is sometimes slow; retry a few times
            print(f"  attempt {i + 1} failed for {url}: {e}", file=sys.stderr)
            time.sleep(10 * (i + 1))
    raise SystemExit(f"Could not download {url}")


def plain(s):
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").upper().strip()


def load_airports():
    rows = csv.reader(io.StringIO(get(AIRPORTS).decode("utf-8", "replace")))
    out = {}
    for r in rows:
        if len(r) < 12:
            continue
        iata, icao = r[4].strip('"'), r[5].strip('"')
        if len(icao) == 4 and icao != "\\N":
            out[icao] = {"city": plain(r[2]), "iata": iata if len(iata) == 3 else "", "tz": r[11] if r[11] != "\\N" else ""}
    return out


def load_airlines():
    rows = csv.reader(io.StringIO(get(AIRLINES).decode("utf-8", "replace")))
    out = {}
    for r in rows:
        if len(r) < 8:
            continue
        iata, icao, active = r[3], r[4], r[7]
        if len(icao) == 3 and len(iata) == 2 and iata.isalnum():
            if icao not in out or active == "Y":
                out[icao] = iata
    out.update(AIRLINE)
    return out


def flights_for(day):
    raw = json.loads(get(ANAC.format(d=day.strftime("%d%m%Y"))))
    if isinstance(raw, str):  # the API returns JSON encoded as a JSON string
        raw = json.loads(raw)
    if not isinstance(raw, list):
        raise SystemExit(f"Unexpected ANAC response for {day}: {str(raw)[:200]}")
    return raw


def utc_ms(s):
    return int(datetime.strptime(s, "%d/%m/%Y %H:%M").replace(tzinfo=timezone.utc).timestamp() * 1000)


def main():
    airports, airlines = load_airports(), load_airlines()
    today = datetime.now(BRT).date()
    by_origin, seen = {}, set()
    for day in (today, today + timedelta(days=1)):
        rows = flights_for(day)
        print(f"{day}: {len(rows)} flights from ANAC")
        for v in rows:
            if "PASSAGEIROS" not in (v.get("ds_tipo_servico") or ""):
                continue
            o, d = v.get("sg_icao_origem", ""), v.get("sg_icao_destino", "")
            al = v.get("sg_empresa_icao", "")
            try:
                num = str(int(v.get("nr_voo", "")))
                t = utc_ms(v["dt_partida_prevista_utc"])
            except (ValueError, KeyError):
                continue
            key = (o, al, num, t)
            if key in seen:
                continue
            seen.add(key)
            ap = airports.get(d, {})
            by_origin.setdefault(o, []).append({
                "t": t,
                "num": airlines.get(al, al) + num,
                "dest": CITY.get(d) or ap.get("city") or d,
                "destCode": ap.get("iata") or d,
            })

    os.makedirs(OUT, exist_ok=True)
    now_ms = int(time.time() * 1000)
    index = {}
    for icao, deps in by_origin.items():
        if not icao.startswith("SB") and not icao.startswith("SD") and not icao.startswith("SN") and not icao.startswith("SW") and not icao.startswith("SS"):
            continue  # Brazilian airports only
        deps.sort(key=lambda x: x["t"])
        deps = [x for x in deps if x["t"] > now_ms - 2 * 3600 * 1000]
        ap = airports.get(icao, {})
        if ap.get("iata"):
            index[ap["iata"]] = icao
        doc = {"airport": icao, "iata": ap.get("iata", ""), "tz": ap.get("tz") or "America/Sao_Paulo",
               "source": "ANAC SIROS", "days": [today.isoformat(), (today + timedelta(days=1)).isoformat()],
               "departures": deps}
        with open(os.path.join(OUT, f"{icao}.json"), "w") as f:
            json.dump(doc, f, separators=(",", ":"), ensure_ascii=False)
    with open(os.path.join(OUT, "index.json"), "w") as f:
        json.dump({"updated": now_ms, "airports": dict(sorted(index.items()))}, f, separators=(",", ":"))
    gig = len(by_origin.get("SBGL", []))
    print(f"Wrote {len(index)} airports; SBGL has {gig} departures")


if __name__ == "__main__":
    main()
