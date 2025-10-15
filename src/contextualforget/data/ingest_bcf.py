import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextualforget.core import parse_bcf_zip, write_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bcf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = parse_bcf_zip(a.bcf)
    write_jsonl(a.out, rows)

if __name__ == "__main__":
    main()
