"""Generate C fixtures from repository golden JSON; no model calculation here."""
import json
import sys
from pathlib import Path

vectors = json.loads(Path(sys.argv[1]).read_text())["vectors"]
selected = [v for v in vectors if v["id"].startswith((
    "control.force_gains.", "control.force_sim.", "control.contact_peak."))]
assert len(selected) == 11

def val(v, key, default):
    return v["inputs"].get(key, {"value": default})["value"]

def num(x):
    return format(x, ".17g")

lines = ["/* Generated from sim/test/golden_vectors.json; do not edit. */",
         "static const golden_case_t cases[] = {"]
for v in selected:
    gain = v["id"].startswith("control.force_gains.")
    fields = [json.dumps(v["id"]), str(int(gain)),
              num(val(v, "k_spring", 50)), num(val(v, "F_target", 5)),
              num(val(v, "ramp", 5)), num(val(v, "approach", .02)),
              str(round(val(v, "Ts", .001) * 1000)),
              num(val(v, "t_end", 4)), num(val(v, "therm", 0))]
    # Contact cases inherit force_sim defaults (reference_models.py:312-313).
    outputs = ["{" + json.dumps(k) + ", " + num(q["value"]) + "}"
               for k, q in v["output"].items()]
    lines.append("    {" + ", ".join(fields) + ", " + str(len(outputs)) +
                 ", {" + ", ".join(outputs) + "}},")
lines.append("};")
Path(sys.argv[2]).write_text("\n".join(lines) + "\n")
