"""Regenerate eval/dataset/cases from gen/bills.yaml using the reference calculator."""
import shutil
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from reference import split  # noqa: E402

root = Path(__file__).resolve().parent.parent
out = root / "eval/dataset/cases"
shutil.rmtree(out, ignore_errors=True)
for case_id, spec in yaml.safe_load((root / "gen/bills.yaml").read_text()).items():
    shares, total = split(spec["bill"])
    d = out / case_id
    d.mkdir(parents=True)
    (d / "input.yaml").write_text(yaml.safe_dump({"prompt": spec["story"]}, sort_keys=False, width=1000))
    (d / "annotations.yaml").write_text(yaml.safe_dump({
        "total_cents": total,
        "shares_cents": shares,
    }, sort_keys=False))
    print(case_id, total, shares)
