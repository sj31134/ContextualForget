"""Tests for utility functions."""
import pytest
import tempfile
import os
from contextualforget.core import (
    read_jsonl, write_jsonl, extract_ifc_entities, parse_bcf_zip
)


class TestUtils:
    def test_read_write_jsonl(self):
        """Test JSONL read/write functionality."""
        test_data = [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"},
            {"id": 3, "name": "test3"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            temp_path = f.name
        
        try:
            # Write data
            write_jsonl(temp_path, test_data)
            
            # Read data
            read_data = list(read_jsonl(temp_path))
            
            assert len(read_data) == 3
            assert read_data[0]["id"] == 1
            assert read_data[1]["name"] == "test2"
            
        finally:
            os.unlink(temp_path)
    
    def test_extract_ifc_entities(self):
        """Test IFC entity extraction."""
        ifc_text = """
        #100= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Sample',$,$,$,$,$,$);
        #500= IFCBUILDING('2FCZDorxHDT8NI01kdXi8P',$,'Test Building',$,$,$,$,$,.ELEMENT.,$,$,$);
        #1000= IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',$,'P-1','sample',$,$,$,$,$);
        """
        
        entities = extract_ifc_entities(ifc_text)
        
        assert len(entities) == 3
        assert any(e["guid"] == "0xScRe4drECQ4DMSqUjd6d" for e in entities)
        assert any(e["type"] == "BUILDING" for e in entities)
        assert any(e["type"] == "BUILDINGELEMENTPROXY" for e in entities)
    
    def test_extract_ifc_entities_duplicates(self):
        """Test IFC entity extraction with duplicates."""
        ifc_text = """
        #100= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Sample',$,$,$,$,$,$);
        #200= IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',$,'Duplicate',$,$,$,$,$,$);
        """
        
        entities = extract_ifc_entities(ifc_text)
        
        # Should deduplicate by GUID
        assert len(entities) == 1
        assert entities[0]["guid"] == "0xScRe4drECQ4DMSqUjd6d"
