from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def read_jsonl(p: str):
    with Path(p).open(encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                yield json.loads(s)

def write_jsonl(p: str, rows):
    path = Path(p)
    if path.parent:  # parent가 비어있지 않을 때만 mkdir 호출
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def extract_ifc_entities(text: str):
    """
    Minimal fallback: capture IFC<UPPER>( '<GUID>',
    Returns list of dicts: {guid, type, name}
    """
    ents = []
    for m in re.finditer(r"IFC([A-Z0-9_]+)\('([A-Za-z0-9_]{10,24})'", text):
        etype = m.group(1)
        guid = m.group(2)
        ents.append({"guid": guid, "type": etype, "name": guid})
    # Deduplicate by GUID
    uniq = {}
    for e in ents:
        uniq[e["guid"]] = e
    return list(uniq.values())

def parse_bcf_zip(bcf_path: str):
    rows = []
    with zipfile.ZipFile(bcf_path) as z:
        for n in z.namelist():
            if n.endswith("markup.bcf"):
                try:
                    root = ET.fromstring(z.read(n))
                    # Topic 태그 찾기
                    topic = root.find("Topic")
                    if topic is not None:
                        topic_id = topic.attrib.get("Guid", "")
                        title = topic.findtext("Title", "")
                        created = topic.findtext("CreationDate", "")
                        author = topic.findtext("CreationAuthor", "")
                        description = topic.findtext("Description", "")
                        
                        # ReferenceLink는 Viewpoints에서 찾기
                        ref = ""
                        viewpoints = root.find("Viewpoints")
                        if viewpoints is not None:
                            related_topic = viewpoints.find("RelatedTopic")
                            if related_topic is not None:
                                ref = related_topic.attrib.get("Guid", "")
                        
                        rows.append({
                            "topic_id": topic_id,
                            "title": title,
                            "created": created,
                            "author": author,
                            "description": description,
                            "ref": ref
                        })
                except ET.ParseError as e:
                    print(f"XML 파싱 오류 in {n}: {e}")
                    continue
    return rows
