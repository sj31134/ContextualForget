PY := python
VENV := conda activate contextualforget && 

.PHONY: setup data ingest_ifc ingest_bcf link build_graph query eval all clean

setup:
	conda create -n contextualforget python=3.11 -y || true
	$(VENV) pip install -U pip
	$(VENV) pip install -e ".[dev]"

data: data/raw/sample.ifc data/raw/sample.bcfzip data/sources.json
	@echo ">> sample IFC & BCF prepared"

data/raw/sample.ifc:
	@mkdir -p data/raw
	@cat > data/raw/sample.ifc <<'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [notYetAssigned]'),'2;1');
FILE_NAME('sample.ifc','2025-10-05T00:00:00',('author'),('org'),'ifc text','ifc text','ref');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#100= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Sample',$,$,$,$,$,$);
#500= IFCBUILDING('2FCZDorxHDT8NI01kdXi8P',$,'Test Building',$,$,$,$,$,.ELEMENT.,$,$,$);
#1000= IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',$,'P-1','sample',$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;
EOF

data/raw/bcf_min/Topics/0001/markup.bcf:
	@mkdir -p data/raw/bcf_min/Topics/0001
	@cat > data/raw/bcf_min/Topics/0001/markup.bcf <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Topic Guid="11111111-1111-1111-1111-111111111111" TopicType="Issue" TopicStatus="Open">
  <Title>Increase clearance of proxy element</Title>
  <CreationDate>2025-10-05T09:00:00Z</CreationDate>
  <CreationAuthor>engineer_a</CreationAuthor>
  <ReferenceLink>ifc://1kTvXnbbzCWw8lcMd1dR4o</ReferenceLink>
  <Description>Adjust dimensions of GUID 1kTvXnbbzCWw8lcMd1dR4o at Level 1</Description>
  <Labels><Label>HVAC</Label><Label>Clearance</Label></Labels>
</Topic>
EOF

data/raw/bcf_min/bcf.version:
	@mkdir -p data/raw/bcf_min
	@cat > data/raw/bcf_min/bcf.version <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Version VersionId="2.1" DetailedVersion="2.1"/>
EOF

data/raw/sample.bcfzip: data/raw/bcf_min/Topics/0001/markup.bcf data/raw/bcf_min/bcf.version
	@cd data/raw/bcf_min && zip -qr ../sample.bcfzip .

data/sources.json:
	@$(PY) - <<'PY'
import json,hashlib,os
def sha(p):
  h=hashlib.sha256()
  with open(p,'rb') as f: h.update(f.read())
  return h.hexdigest()
os.makedirs('data',exist_ok=True)
j={
 "sample.ifc":{"path":"data/raw/sample.ifc","sha256":sha("data/raw/sample.ifc"),"size":os.path.getsize("data/raw/sample.ifc"),"source":"synthetic"},
 "sample.bcfzip":{"path":"data/raw/sample.bcfzip","sha256":sha("data/raw/sample.bcfzip"),"size":os.path.getsize("data/raw/sample.bcfzip"),"source":"synthetic"}
}
json.dump(j,open("data/sources.json","w"),indent=2)
PY

ingest_ifc:
	$(VENV) python -m contextualforget.data.ingest_ifc --ifc data/raw/sample.ifc --out data/processed/ifc.jsonl

ingest_bcf:
	$(VENV) python -m contextualforget.data.ingest_bcf --bcf data/raw/sample.bcfzip --out data/processed/bcf.jsonl

link:
	$(VENV) python -m contextualforget.data.link_ifc_bcf --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --out data/processed/links.jsonl

build_graph:
	$(VENV) python -m contextualforget.data.build_graph --ifc data/processed/ifc.jsonl --bcf data/processed/bcf.jsonl --links data/processed/links.jsonl --out data/processed/graph.gpickle

query:
	$(VENV) ctxf query 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5

eval:
	$(VENV) python -m contextualforget.core.eval_metrics --q queries/queries.jsonl --gold eval/gold.jsonl --run results/run.json

optimize:
	$(VENV) python -c "from contextualforget.performance import optimize_for_production; optimize_for_production('data/processed/graph.gpickle', 'data/processed/graph_optimized.gpickle')"

visualize:
	$(VENV) ctxf visualize --output-dir visualizations

test_advanced:
	$(VENV) ctxf stats
	$(VENV) ctxf search "clearance" "HVAC" --topk 5
	$(VENV) ctxf author "engineer_a" --topk 5

demo:
	$(VENV) python examples/quick_start.py

jupyter:
	$(VENV) jupyter lab examples/demo.ipynb

all: setup data ingest_ifc ingest_bcf link build_graph query

all_advanced: setup data ingest_ifc ingest_bcf link build_graph query optimize visualize test_advanced

clean:
	rm -rf .venv data/processed data/raw/sample.bcfzip visualizations cache
