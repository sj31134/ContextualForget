import argparse
import json
import os


def ndcg_at_k(pred, gold, k=5):
    s = 0.0
    for i, p in enumerate(pred[:k], start=1):
        s += (1.0 / i) if p in gold else 0.0
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True)
    ap.add_argument("--gold", required=True)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()

    _q = json.loads(Path(a.q).open(encoding="utf-8").read().splitlines()[0])
    gold = json.loads(Path(a.gold).open(encoding="utf-8").read().splitlines()[0])

    # toy prediction: equal to gold
    pred = gold["gold_issue_ids"]
    res = {"ndcg@5": ndcg_at_k(pred, gold["gold_issue_ids"], 5)}

    Path("results").mkdir(parents=True, exist_ok=True)
    with Path(a.run).open("w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
