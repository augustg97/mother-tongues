#!/usr/bin/env python3
"""audit_all.py — the gate. Runs every module's selftest; non-zero exit blocks the build."""
import subprocess, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = ["frames.py", "licences.py", "encoding.py", "diversity.py", "attribution.py", "climate.py", "witness.py", "timedepth.py", "spatial.py"]
fail = []
for m in MODULES:
    p = subprocess.run([sys.executable, os.path.join(HERE, m)],
                       capture_output=True, text=True)
    ok = p.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}  {m}")
    if not ok:
        fail.append(m)
        print(p.stdout[-2000:]); print(p.stderr[-2000:])
print()
print(f"{len(MODULES)-len(fail)}/{len(MODULES)} modules pass")
sys.exit(1 if fail else 0)
