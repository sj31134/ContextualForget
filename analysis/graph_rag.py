"""
graph_rag.py
================

This script implements a simple prototype of a graph‑based retrieval
augmented generation (RAG) system with a long‑term memory and
forgetting mechanism.  It reads an IFC file to extract building
entities and their globally unique identifiers (GUIDs), associates
synthetic change events from a JSON file with those entities, and
provides query functions to retrieve the events connected to a given
entity.  A configurable time‑to‑live (TTL) policy can be used to
forget older events.

The goal of this script is not to provide a production‑ready
implementation but to demonstrate how a small, open dataset can be
used to explore research questions around long‑term memory and
forgetting in the context of engineering digital twins.  It is
intentionally kept simple so that the core ideas are easy to follow.
"""

import json
import re
import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional


@dataclass
class IfcEntity:
    """Represents an entity parsed from an IFC file."""
    guid: str
    type: str
    raw_line: str


@dataclass
class Event:
    """Represents a change event associated with one or more IFC entities."""
    id: int
    title: str
    description: str
    guids: List[str]
    timestamp: datetime.datetime
    author: str

    @staticmethod
    def from_json(d: Dict[str, object]) -> "Event":
        # Convert ISO8601 timestamps (with trailing 'Z' or without) into naive UTC datetimes
        ts_str: str = d["timestamp"]  # type: ignore[index]
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1]
        ts = datetime.datetime.fromisoformat(ts_str)
        return Event(
            id=int(d["id"]),  # type: ignore[index]
            title=str(d["title"]),
            description=str(d["description"]),
            guids=list(d["guids"]),  # type: ignore[index]
            timestamp=ts,
            author=str(d.get("author", "")),
        )


def parse_ifc_entities(ifc_path: str) -> Dict[str, IfcEntity]:
    """Parse an IFC file and extract entities with GUIDs.

    The parser uses a simple regular expression to find patterns of the form
    `IFC<Type>('GUID', ...` on each line.  It does not attempt to fully
    parse the IFC grammar but is sufficient for demonstration.  The
    resulting dictionary maps GUID strings to IfcEntity objects.

    Parameters
    ----------
    ifc_path : str
        Path to an IFC file on disk.

    Returns
    -------
    Dict[str, IfcEntity]
        A mapping from GUID to IfcEntity.
    """
    entity_pattern = re.compile(r"IFC([A-Za-z0-9_]+)\('\s*([^']+)'")
    entities: Dict[str, IfcEntity] = {}
    with open(ifc_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            m = entity_pattern.search(line)
            if m:
                type_name, guid = m.group(1), m.group(2)
                # Some IFC lines may reference the same GUID multiple times; keep first occurrence.
                if guid not in entities:
                    entities[guid] = IfcEntity(guid=guid, type=type_name, raw_line=line)
    return entities


def load_events(events_path: str) -> List[Event]:
    """Load events from a JSON file.

    Parameters
    ----------
    events_path : str
        Path to the events JSON file.

    Returns
    -------
    List[Event]
        A list of Event objects.
    """
    with open(events_path, "r", encoding="utf-8") as f:
        raw_events = json.load(f)
    return [Event.from_json(ev) for ev in raw_events]


def build_element_event_map(events: Iterable[Event]) -> Dict[str, List[Event]]:
    """Construct a mapping from entity GUIDs to a list of associated events.

    Parameters
    ----------
    events : Iterable[Event]
        Iterable of Event objects.

    Returns
    -------
    Dict[str, List[Event]]
        Mapping from GUID to list of events referencing that GUID.
    """
    mapping: Dict[str, List[Event]] = {}
    for ev in events:
        for guid in ev.guids:
            mapping.setdefault(guid, []).append(ev)
    return mapping


def filter_events_by_ttl(events: Iterable[Event], ttl_days: Optional[int]) -> List[Event]:
    """Filter a list of events according to a time‑to‑live (TTL) policy.

    Events older than the specified number of days (based on their timestamp)
    are excluded.  If `ttl_days` is None, no events are filtered.

    Parameters
    ----------
    events : Iterable[Event]
        Iterable of Event objects.
    ttl_days : Optional[int]
        Number of days after which events should be forgotten.  If None,
        all events are returned.

    Returns
    -------
    List[Event]
        Events that fall within the TTL window.
    """
    if ttl_days is None:
        return list(events)
    now = datetime.datetime.utcnow()
    cutoff = now - datetime.timedelta(days=ttl_days)
    return [ev for ev in events if ev.timestamp >= cutoff]


def query_events_for_guid(guid: str, mapping: Dict[str, List[Event]], ttl_days: Optional[int] = None) -> List[Event]:
    """Retrieve events associated with a specific entity GUID, applying TTL if provided.

    Parameters
    ----------
    guid : str
        The GUID of the entity.
    mapping : Dict[str, List[Event]]
        Mapping from GUID to events referencing that entity.
    ttl_days : Optional[int]
        Time‑to‑live in days; events older than this are excluded.

    Returns
    -------
    List[Event]
        Events referencing the specified GUID within the TTL window.
    """
    events = mapping.get(guid, [])
    return filter_events_by_ttl(events, ttl_days)


def summarise_events(events: List[Event]) -> str:
    """Produce a simple textual summary of a list of events.

    For demonstration purposes, this function concatenates the titles
    of the events in chronological order.  More sophisticated
    summarisation could use natural language generation techniques.

    Parameters
    ----------
    events : List[Event]
        Events to summarise.

    Returns
    -------
    str
        A human‑readable summary of the events.
    """
    if not events:
        return "No recent events."
    # Sort by timestamp ascending
    sorted_events = sorted(events, key=lambda ev: ev.timestamp)
    lines = [f"{ev.timestamp.date()}: {ev.title}" for ev in sorted_events]
    return "; ".join(lines)


def main(ifc_path: str, events_path: str, query_guid: Optional[str] = None, ttl_days: Optional[int] = None) -> None:
    """Run the demonstration.

    If a `query_guid` is provided, the script prints a summary of
    events associated with that GUID.  Otherwise it lists all entity
    GUIDs and counts of associated events.

    Parameters
    ----------
    ifc_path : str
        Path to the IFC file.
    events_path : str
        Path to the events JSON file.
    query_guid : Optional[str]
        Specific GUID to query; if None, summarise all.
    ttl_days : Optional[int]
        TTL in days for forgetting events.
    """
    entities = parse_ifc_entities(ifc_path)
    events = load_events(events_path)
    mapping = build_element_event_map(events)

    if query_guid:
        print(f"Querying GUID: {query_guid}")
        ent = entities.get(query_guid)
        if ent is None:
            print("GUID not found in IFC file.")
            return
        relevant_events = query_events_for_guid(query_guid, mapping, ttl_days)
        print(f"Entity type: {ent.type}")
        print(f"Number of related events (after TTL filter): {len(relevant_events)}")
        print(summarise_events(relevant_events))
    else:
        # Summarise all entities
        for guid, ent in entities.items():
            count = len(query_events_for_guid(guid, mapping, ttl_days))
            if count > 0:
                print(f"{guid} ({ent.type}): {count} event(s)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Graph‑based RAG demo with IFC and events.")
    parser.add_argument("ifc", help="Path to IFC file")
    parser.add_argument("events", help="Path to events JSON file")
    parser.add_argument("--guid", help="GUID of entity to query", default=None)
    parser.add_argument("--ttl", type=int, help="TTL in days; events older than this are forgotten", default=None)
    args = parser.parse_args()

    main(args.ifc, args.events, query_guid=args.guid, ttl_days=args.ttl)