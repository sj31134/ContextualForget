import argparse
from .utils import read_jsonl, write_jsonl

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True)
    ap.add_argument("--bcf", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    ifc_map = {r["guid"]: r for r in read_jsonl(a.ifc)}
    out = []
    for b in read_jsonl(a.bcf):
        text = " ".join([b.get("title", ""), b.get("ref", "")])
        matches = [g for g in ifc_map if g in text]
        conf = 1.0 if matches else 0.2
        out.append({
            "topic_id": b["topic_id"],
            "guid_matches": matches,
            "confidence": conf,
            "evidence": text
        })
    write_jsonl(a.out, out)

if __name__ == "__main__":
    main()
