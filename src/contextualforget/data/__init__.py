"""Data processing and ingestion modules."""

from .ingest_ifc import main as ingest_ifc_main
from .ingest_bcf import main as ingest_bcf_main
from .link_ifc_bcf import main as link_ifc_bcf_main
from .build_graph import main as build_graph_main

__all__ = [
    "ingest_ifc_main",
    "ingest_bcf_main", 
    "link_ifc_bcf_main",
    "build_graph_main"
]
