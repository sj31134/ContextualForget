import argparse
import os

import networkx as nx

from ..core import read_jsonl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True)
    ap.add_argument("--bcf", required=True)
    ap.add_argument("--links", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    G = nx.DiGraph()
    for r in read_jsonl(a.ifc):
        G.add_node(("IFC", r["guid"]), **r)
    for b in read_jsonl(a.bcf):
        G.add_node(("BCF", b["topic_id"]), **b)
    for link in read_jsonl(a.links):
        for g in link["guid_matches"]:
            G.add_edge(("BCF", link["topic_id"]), ("IFC", g),
                       type="refersTo", confidence=link["confidence"])

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    import pickle
    with Path(a.out).open('wb') as f:
        pickle.dump(G, f)

if __name__ == "__main__":
    main()
