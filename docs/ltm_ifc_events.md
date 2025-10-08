Building Long-Term Memory with IFC and Dynamic Events

Introduction
Engineering digital twins are living representations of physical assets. A digital twin of a building or plant is not just a set of static CAD/BIM files – it must also encode the ongoing history of changes and decisions (who modified what, when, and why). Large language models (LLMs) that answer questions about the state of an asset therefore need a long-term memory that fuses both the static geometry and dynamic event log. This study explores how such a memory can be constructed without using proprietary data. We combine a publicly available IFC (Industry Foundation Classes) model with synthetic change events to demonstrate a graph-based retrieval-augmented generation (RAG) system with a forgetting mechanism. The underlying repository used for this work is an empty public repository on GitHubapi.github.com, which we populate locally with data and code.

Data Sources
IFC sample file: We obtained basic_shape_CSG.ifc from the IfcOpenShell/files project on GitHub (a repository of sample IFC files). The file defines a minimal building model containing a project (#100), a building (#500) and a proxy element (#1000) representing a box shape. Each entity has a globally unique identifier (GUID) embedded in the IFC definition (e.g. IFCBUILDING('2FCZDorxHDT8NI01kdXi8P',...) for the building and IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',...) for the proxy). These GUIDs form the static keys in our graph.
Synthetic event log: Because the repository cannot access private industrial data, we created a small JSON file (events.json) with three change events. Each event has an ID, a title and description, a list of affected GUIDs, a timestamp and an author. For instance, one event updates the height of the proxy element and another renames the building.

Methodology
Parsing IFC entities. We wrote a Python script (graph_rag.py) that uses a regular expression to find patterns of the form IFC<Type>('GUID', … in the IFC file. For each match the script records the entity type, the GUID and the raw line. It ignores duplicate GUIDs. For example, the building element proxy is extracted as guid=1kTvXnbbzCWw8lcMd1dR4o, type=BUILDINGELEMENTPROXY.
Loading events. The script deserialises the JSON event log into Event objects. ISO 8601 timestamps are converted to naive UTC datetimes. It then builds a mapping from each GUID to the list of events referencing that GUID.
Querying the graph. Given a GUID, the script retrieves all events that reference that GUID. A time-to-live (TTL) parameter can be supplied to forget events older than a specified number of days. Without TTL, all historical events are returned; with TTL, only recent events are retained.
Summarisation. To make responses concise, the script sorts the relevant events chronologically and concatenates their titles with dates. More sophisticated natural-language generation could be used here, but this simple method is sufficient to demonstrate the concept.

Experiments
We ran the script to query the proxy element GUID 1kTvXnbbzCWw8lcMd1dR4o. Without a TTL, the system returned one event:
Querying GUID: 1kTvXnbbzCWw8lcMd1dR4o
Entity type: BUILDINGELEMENTPROXY
Number of related events (after TTL filter): 1
2024-02-15: Update sample CSG proxy
This output shows that the proxy element has one recorded change event, which occurred on 15 February 2024. When we applied a TTL of 200 days, representing a "forget after seven months" policy, the event fell outside the window (because the current date is 4 October 2025) and was omitted:
Number of related events (after TTL filter): 0
No recent events.
This simple experiment demonstrates how a long-term memory can incorporate forgetting. In a larger system with many events, the TTL, decay weights or summarisation frequency can be tuned to balance freshness and completeness.

Discussion
This prototype addresses two core challenges in long-term memory for engineering digital twins:
Combining static and dynamic data. By linking IFC entities (static geometry) with event logs (dynamic context) via GUIDs, the system can answer questions such as "What changes were made to this component?" The same approach works with real BCF (BIM Collaboration Format) files, where each issue is linked to an IFC element by its GUID. Using open data ensures that the method is reproducible.
Forgetting irrelevant events. Over time, a digital twin accumulates a large number of events. A TTL or weight-decay policy removes outdated or low-value events, reducing memory usage and preventing the model from citing obsolete information. Our experiment shows how a single event can be filtered out when it exceeds the TTL.
In a production setting, the event log would come from version control systems, change management systems or BCF repositories rather than synthetic data. The forgetting policy could incorporate additional criteria (importance scores, summarisation) beyond simple age filtering. Nevertheless, the small demo illustrates the end-to-end workflow: parsing, linking, querying, summarising and forgetting.

Conclusion
We demonstrated a lightweight framework for building a long-term memory that fuses IFC models with event histories. Using only open data and synthetic events, we were able to parse the model, link change events by GUID, answer queries about specific elements, and apply a TTL-based forgetting mechanism. The experiment underscores the feasibility of studying LLM-assisted digital twins without proprietary datasets and lays a foundation for richer research using BCF or other real event sources.
