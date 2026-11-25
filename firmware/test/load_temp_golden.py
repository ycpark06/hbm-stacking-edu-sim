"""Extract temperature/profile fixtures only; never calculate model outputs."""
import json
import sys
from pathlib import Path

vectors = json.loads(Path(sys.argv[1]).read_text())["vectors"]
temps = [v for v in vectors if v["id"].startswith("control.temp_sim.")]
profiles = [v for v in vectors if v["id"].startswith("control.tcncf_profile.")]
assert len(temps) == 2 and len(profiles) == 6
lines = ["/* Generated from sim/test/golden_vectors.json; do not edit. */",
         "static const temp_case_t temp_cases[] = {"]
for v in temps:
    fields = [json.dumps(v["id"]), str(round(v["inputs"]["Ts"]["value"] * 1000)),
              format(v["inputs"]["t_end"]["value"], ".17g")]
    outputs = ["{" + json.dumps(k) + ", " + format(q["value"], ".17g") + "}"
               for k, q in v["output"].items()]
    assert len(outputs) == 6
    lines.append("    {" + ", ".join(fields) + ", {" + ", ".join(outputs) + "}},")
lines.extend(["};", "static const profile_case_t profile_cases[] = {"])
for v in profiles:
    lines.append("    {" + json.dumps(v["id"]) + ", " +
                 format(v["inputs"]["t"]["value"], ".17g") + ", " +
                 format(v["output"]["sp"]["value"], ".17g") + "},")
lines.append("};")
Path(sys.argv[2]).write_text("\n".join(lines) + "\n")
