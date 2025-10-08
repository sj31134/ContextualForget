import json, typer, networkx as nx
from .query import find_by_guid

app = typer.Typer()

@app.command()
def query(
    guid: str,
    ttl: int = 365,
    topk: int = 5,
    graph: str = "data/processed/graph.gpickle"
):
    import pickle
    with open(graph, 'rb') as f:
        G = pickle.load(f)
    hits = find_by_guid(G, guid, ttl=ttl)[:topk]
    out = [{
        "topic_id": n[1],
        "created": d.get("created"),
        "edge": {"type": e.get("type"), "confidence": e.get("confidence")}
    } for n, d, e in hits]
    typer.echo(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    app()
