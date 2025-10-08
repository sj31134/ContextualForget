import networkx as nx
from .forgetting import expired

def find_by_guid(G: nx.DiGraph, guid: str, ttl: int = 0):
    hits = []
    for n, d in G.nodes(data=True):
        if n[0] == "BCF":
            created = d.get("created", "")
            if ttl > 0 and expired(created, ttl):
                continue
            for _, t, ed in G.out_edges(n, data=True):
                if t == ("IFC", guid):
                    hits.append((n, d, ed))
    return hits
