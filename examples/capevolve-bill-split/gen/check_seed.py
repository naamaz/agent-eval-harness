"""Run the seed (buggy) skill script on each gold bill; report which cases it gets wrong."""
import json, subprocess, sys, tempfile
from pathlib import Path
import yaml
root = Path(__file__).resolve().parent.parent
script = sys.argv[1] if len(sys.argv) > 1 else root / ".claude/skills/split-bill/scripts/split.py"
bills = yaml.safe_load((root / "gen/bills.yaml").read_text())
ok = 0
for cid, spec in bills.items():
    gold = yaml.safe_load((root / f"eval/dataset/cases/{cid}/annotations.yaml").read_text())
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(spec["bill"], f)
    out = subprocess.run([sys.executable, str(script), f.name], capture_output=True, text=True).stdout
    got = {}
    for line in out.splitlines():
        if "->" in line:
            got[line.split(":")[0]] = round(float(line.rsplit("->", 1)[1]) * 100)
    wrong = {d: (got.get(d), c) for d, c in gold["shares_cents"].items() if got.get(d) != c}
    ok += not wrong
    print(cid, "OK" if not wrong else f"WRONG {wrong}")
print(f"{ok}/{len(bills)} correct")
