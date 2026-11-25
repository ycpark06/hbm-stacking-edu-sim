"""Compare reference outputs with the immutable JS-porting golden vectors.

Usage: python3 -I calc/reference/check_golden.py [golden_path]
The default path is repo-relative sim/test/golden_vectors.json, resolved from
this script. build_golden() is evaluated in memory; no files are written.

Stage 3 JS tests (sim/test/) must use the same schema and comparison rules:
the JSON document contains meta (informational) and vectors. Each vector has
id, model, function, source, inputs{name: {value, unit}},
output{name: {value, unit}}, and tolerance{abs, rel}.
Match vectors by id, regardless of order; reject missing/extra/duplicate ids,
different output names, and different inputs (including units). Compare each
output.<name>.value, recursively requiring identical nested-list shapes.
For numeric leaves, pass iff |actual - expected| <= abs + rel * |expected|,
using the expected vector's tolerance. Booleans are not numbers; strings,
booleans and null must match exactly. NaN matches only NaN; infinities must
match with the same sign. Output units and model/function/source also match
exactly. Metadata such as the generating Python version is not compared.

Relative error is |actual - expected| / |expected| (zero for equal values,
infinity for a nonzero error at expected=0 or unmatched nonfinite numbers).
Non-numeric/structural failures report relative_error=n/a. Summary counts
compared output leaves, differing output leaves (including tolerated rounding
differences), failures, and the maximum numeric relative error.
"""

import argparse
import json
import math
from pathlib import Path
import sys

# Isolated mode (-I) omits the script directory from sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_models import build_golden


def is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def exact(expected, actual):
    """JSON equality without Python's True == 1 / False == 0 coercion."""
    if is_number(expected) and is_number(actual):
        return expected == actual or (math.isnan(expected) and math.isnan(actual))
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            exact(expected[key], actual[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            exact(e, a) for e, a in zip(expected, actual)
        )
    return expected == actual


class Comparison:
    def __init__(self):
        self.values = 0
        self.different = 0
        self.failures = 0
        self.max_relative_error = 0.0

    def fail(self, vector_id, path, expected, actual, relative_error="n/a"):
        self.failures += 1
        print(f"FAIL id={vector_id} {path} expected={expected!r} "
              f"actual={actual!r} relative_error={relative_error}")

    def value(self, vector_id, path, expected, actual, tolerance):
        if isinstance(expected, list) or isinstance(actual, list):
            if not isinstance(expected, list) or not isinstance(actual, list):
                self.fail(vector_id, path, expected, actual)
                return
            if len(expected) != len(actual):
                self.fail(vector_id, path + ".length", len(expected), len(actual))
                return
            for index, (e, a) in enumerate(zip(expected, actual)):
                self.value(vector_id, f"{path}[{index}]", e, a, tolerance)
            return

        self.values += 1
        equal = exact(expected, actual)
        self.different += not equal
        if is_number(expected) and is_number(actual):
            if equal:
                relative_error, passed = 0.0, True
            elif not math.isfinite(expected) or not math.isfinite(actual):
                relative_error, passed = math.inf, False
            else:
                error = abs(actual - expected)
                relative_error = error / abs(expected) if expected else math.inf
                passed = error <= tolerance["abs"] + tolerance["rel"] * abs(expected)
            self.max_relative_error = max(self.max_relative_error, relative_error)
            if not passed:
                self.fail(vector_id, path, expected, actual, relative_error)
        elif not equal:
            self.fail(vector_id, path, expected, actual)

    def index(self, vectors, side):
        indexed = {}
        for vector in vectors:
            vector_id = vector["id"]
            if vector_id in indexed:
                self.fail(vector_id, "id (duplicate)", "unique id", side)
            indexed[vector_id] = vector
        return indexed

    def compare(self, expected_vectors, actual_vectors):
        expected = self.index(expected_vectors, "golden")
        actual = self.index(actual_vectors, "reference")
        for vector_id in sorted(expected.keys() - actual.keys()):
            self.fail(vector_id, "id", "present", "missing")
        for vector_id in sorted(actual.keys() - expected.keys()):
            self.fail(vector_id, "id", "missing", "present")
        for vector_id in expected:
            if vector_id not in actual:
                continue
            e, a = expected[vector_id], actual[vector_id]
            for field in ("model", "function", "source", "inputs"):
                if not exact(e[field], a[field]):
                    self.fail(vector_id, field, e[field], a[field])
            for name in sorted(e["output"].keys() | a["output"].keys()):
                path = f"output.{name}"
                if name not in e["output"] or name not in a["output"]:
                    self.fail(vector_id, path, e["output"].get(name, "<missing>"),
                              a["output"].get(name, "<missing>"))
                    continue
                eo, ao = e["output"][name], a["output"][name]
                if not exact(eo["unit"], ao["unit"]):
                    self.fail(vector_id, path + ".unit", eo["unit"], ao["unit"])
                self.value(vector_id, path + ".value", eo["value"], ao["value"],
                           e["tolerance"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("golden_path", nargs="?", type=Path,
                        default=Path(__file__).resolve().parents[2]
                        / "sim" / "test" / "golden_vectors.json")
    args = parser.parse_args()
    result = Comparison()
    vector_count = 0
    try:
        with args.golden_path.open(encoding="utf-8") as stream:
            expected = json.load(stream)["vectors"]
        vector_count = len(expected)
        result.compare(expected, build_golden())
    except (OSError, ValueError, KeyError, TypeError) as error:
        result.fail("<document>", "schema/read", "valid golden", str(error))
    print(f"SUMMARY vectors={vector_count} compared_values={result.values} "
          f"different_values={result.different} failures={result.failures} "
          f"max_relative_error={result.max_relative_error:.17g}")
    print("FAILED" if result.failures else "ALL OK")
    return 1 if result.failures else 0


if __name__ == "__main__":
    sys.exit(main())
