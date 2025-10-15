import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextualforget.core import extract_ifc_entities, write_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with Path(a.ifc).open(errors="ignore") as f:
        text = f.read()

    rows = extract_ifc_entities(text)
    write_jsonl(a.out, rows)

if __name__ == "__main__":
    main()
