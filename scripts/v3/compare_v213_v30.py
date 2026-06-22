"""Compare v2.13 vs v3.0 hybrid benchmark results.

Usage: compare_v213_v30.py [v213.json] [v30.json]   (defaults: realistic set)
"""
import json
import sys

A_PATH = sys.argv[1] if len(sys.argv) > 1 else "/workspace/artifacts/metrics/benchmark_hybrid_v213_realistic.json"
B_PATH = sys.argv[2] if len(sys.argv) > 2 else "/workspace/artifacts/metrics/benchmark_hybrid_v30_realistic.json"
A = json.load(open(A_PATH))
B = json.load(open(B_PATH))


def typed_f1(d, var, cls=None):
    v = d["variants"][var]
    if cls:
        c = v["by_class"].get(cls)
        return c["f1"] if c else None
    return v["aggregate"]["typed"]["f1"]


def untyped_f1(d, var):
    return d["variants"][var]["aggregate"]["untyped"]["f1"]


print("=== OVERALL typed F1   (v2.13 -> v3.0) ===")
for var in ("raw", "hybrid"):
    fa, fb = typed_f1(A, var), typed_f1(B, var)
    print("  %-7s %.3f -> %.3f  (%+.3f)" % (var, fa, fb, fb - fa))

print("=== OVERALL untyped F1 (v2.13 -> v3.0) ===")
for var in ("raw", "hybrid"):
    fa, fb = untyped_f1(A, var), untyped_f1(B, var)
    print("  %-7s %.3f -> %.3f  (%+.3f)" % (var, fa, fb, fb - fa))

print("\n=== PER-CLASS hybrid F1 (v2.13 -> v3.0) ===")
classes = sorted(set(A["variants"]["hybrid"]["by_class"]) | set(B["variants"]["hybrid"]["by_class"]))
for c in classes:
    fa = typed_f1(A, "hybrid", c) or 0.0
    fb = typed_f1(B, "hybrid", c) or 0.0
    d = fb - fa
    arrow = "UP" if d > 0.01 else ("DOWN" if d < -0.01 else "==")
    star = "  <<< TARGET" if c in ("private_person", "private_address") else ""
    print("  %-18s %.3f -> %.3f  (%+.3f) %s%s" % (c, fa, fb, d, arrow, star))
