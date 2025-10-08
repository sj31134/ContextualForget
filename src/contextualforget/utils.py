from __future__ import annotations
import os, re, json, zipfile, xml.etree.ElementTree as ET

def read_jsonl(p: str):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                yield json.loads(s)

def write_jsonl(p: str, rows):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
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
                root = ET.fromstring(z.read(n))
                topic_id = root.attrib.get("Guid", "")
                title = root.findtext("Title", "")
                created = root.findtext("CreationDate", "")
                author = root.findtext("CreationAuthor", "")
                ref = root.findtext("ReferenceLink", "") or ""
                rows.append({
                    "topic_id": topic_id,
                    "title": title,
                    "created": created,
                    "author": author,
                    "ref": ref
                })
    return rows
