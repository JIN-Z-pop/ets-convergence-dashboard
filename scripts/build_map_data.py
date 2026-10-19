"""build_map_data.py — generate the two public data files for map.html.

Reads the research GeoJSON + province CSV from the machine-local path configured
in scripts/local_paths.py (key: china_mcp_dir) and writes:

  data/map_entities.json        public columns only: lon/lat (4 dp), name, province,
                                city, sector, year
  data/map_cbam_province.json   31 regions: roster columns from the CSV plus the
                                mapped / no-coordinate counts measured on the GeoJSON
                                (no total row; the page computes the total)

Privacy: credit_code, source and sub_sector are dropped. The resolved input path is
never printed (stdout/log/errors) — only counts and byte sizes are reported.

JSON is written compact (no indentation, ',' and ':') to stay under the 500 KB budget.
"""
import csv
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_paths  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PUBLIC_FIELDS = ("name", "province", "city", "sector", "year")
CBAM_SECTORS = ("セメント", "鉄鋼", "アルミ冶金")


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    base = local_paths.require("china_mcp_dir")  # never printed
    gj = _load_json(os.path.join(base, "data", "ets_entities_all.geojson"))
    rows = _load_csv(os.path.join(base, "data", "cbam_exposure_by_province.csv"))

    entities = []
    mapped_total = {}
    mapped_cbam = {}
    mapped_sector = {}
    for feat in gj["features"]:
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if len(coords) < 2:
            continue
        props = feat.get("properties") or {}
        rec = {"lon": round(coords[0], 4), "lat": round(coords[1], 4)}
        for key in PUBLIC_FIELDS:
            rec[key] = props.get(key)
        entities.append(rec)
        prov = rec["province"]
        mapped_total[prov] = mapped_total.get(prov, 0) + 1
        if rec["sector"] in CBAM_SECTORS:
            mapped_cbam[prov] = mapped_cbam.get(prov, 0) + 1
        mapped_sector[(prov, rec["sector"])] = mapped_sector.get((prov, rec["sector"]), 0) + 1

    csv_provinces = [r["Province"] for r in rows]
    unknown = sorted(set(mapped_total) - set(csv_provinces))
    if unknown:
        print("ERROR: GeoJSON provinces missing from the CSV: %r" % unknown)
        return 2

    # 31 rows, one flat 15-key object per region. No total row:
    # the page computes and renders its own total.
    provinces = []
    tot = {"power": 0, "cement": 0, "steel": 0, "aluminum": 0, "total": 0,
           "cbam": 0, "mapped_total": 0, "mapped_cbam": 0,
           "nc_power": 0, "nc_cement": 0, "nc_steel": 0, "nc_aluminum": 0}
    for r in rows:
        name = r["Province"]
        listed = int(r["Total"])
        power, cement = int(r["Power"]), int(r["Cement"])
        steel, aluminum = int(r["Steel"]), int(r["Aluminum"])
        m_total = mapped_total.get(name, 0)
        m_cbam = mapped_cbam.get(name, 0)
        nc_power = power - mapped_sector.get((name, "発電"), 0)
        nc_cement = cement - mapped_sector.get((name, "セメント"), 0)
        nc_steel = steel - mapped_sector.get((name, "鉄鋼"), 0)
        nc_aluminum = aluminum - mapped_sector.get((name, "アルミ冶金"), 0)
        provinces.append({
            "province": name,
            "power": power, "cement": cement, "steel": steel, "aluminum": aluminum,
            "total": listed,
            "cbam_entities": int(r["CBAM_entities"]),
            "cbam_pct": float(r["CBAM_pct"]),
            "mapped_total": m_total,
            "mapped_cbam": m_cbam,
            "no_coord_total": listed - m_total,
            "no_coord_power": nc_power,
            "no_coord_cement": nc_cement,
            "no_coord_steel": nc_steel,
            "no_coord_aluminum": nc_aluminum,
        })
        tot["power"] += power
        tot["cement"] += cement
        tot["steel"] += steel
        tot["aluminum"] += aluminum
        tot["total"] += listed
        tot["cbam"] += int(r["CBAM_entities"])
        tot["mapped_total"] += m_total
        tot["mapped_cbam"] += m_cbam
        tot["nc_power"] += nc_power
        tot["nc_cement"] += nc_cement
        tot["nc_steel"] += nc_steel
        tot["nc_aluminum"] += nc_aluminum

    out_dir = REPO / "data"
    out_dir.mkdir(exist_ok=True)
    e_bytes = json.dumps(entities, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    p_bytes = json.dumps(provinces, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (out_dir / "map_entities.json").write_bytes(e_bytes)
    (out_dir / "map_cbam_province.json").write_bytes(p_bytes)

    cbam_mapped = sum(1 for e in entities if e["sector"] in CBAM_SECTORS)
    regions_with_cbam = len({e["province"] for e in entities if e["sector"] in CBAM_SECTORS})
    print("entities: %d (CBAM %d)" % (len(entities), cbam_mapped))
    print("regions: %d (with mapped CBAM points: %d)" % (len(rows), regions_with_cbam))
    print("roster: total %d / CBAM %d | mapped %d / %d | no coordinates %d (%d/%d/%d/%d)"
          % (tot["total"], tot["cbam"], tot["mapped_total"], tot["mapped_cbam"],
             tot["total"] - tot["mapped_total"],
             tot["nc_power"], tot["nc_cement"], tot["nc_steel"], tot["nc_aluminum"]))
    print("bytes: entities %d / province %d / total %d (%.1f KB)"
          % (len(e_bytes), len(p_bytes), len(e_bytes) + len(p_bytes),
             (len(e_bytes) + len(p_bytes)) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
