# Synthetic Data Generation Methodology

**Document Version**: 1.0  
**Last Updated**: 2025-10-09  
**Purpose**: Transparent documentation of synthetic BIM data generation

---

## Overview

**Purpose**: To supplement limited real-world BIM collaboration data for research purposes

**Approach**: Template-based generation with domain expert knowledge

**Transparency Level**: FULL - All generation logic is open-source

---

## IFC File Generation

### Method
Programmatic IFC entity creation using ifcopenshell library

### Building Templates
- Residential buildings (1-3 floors)
- Office buildings (2-5 floors)
- Industrial facilities
- Healthcare facilities
- Educational facilities

### Elements Per Building
15-25 IFC entities (Walls, Slabs, Columns, Doors, Windows)

### Realism Factors
- ✅ Standard building dimensions
- ✅ Typical floor-to-floor heights (3.0-3.5m)
- ✅ Realistic element relationships (Wall contains Door)
- ✅ Valid IFC schema (IFC2X3, IFC4)

### Known Limitations
- ⚠️ Simplified geometry (no complex curves)
- ⚠️ Limited element types
- ⚠️ No MEP systems
- ⚠️ No structural analysis data


---

## BCF Issue Generation

### Method
Template-based issue generation with random variation

### Issue Templates by Category

#### Structural
- Column section insufficient
- Beam deflection concern
- Slab thickness verification
- Seismic design issue
- Foundation depth change
- Rebar placement error
- Connection detail missing

#### Architectural
- Wall thickness mismatch
- Window position interference
- Door width insufficient
- Ceiling height shortage
- Finish material change
- Waterproofing detail
- Balcony railing height

#### Mechanical
- Duct interference
- Pipe routing change
- Equipment room space
- Ventilation capacity
- Boiler capacity
- Cooling load exceeded

#### Electrical
- Power capacity shortage
- Lighting layout change
- Outlet position
- Emergency light missing
- Grounding system

#### Fire Safety
- Sprinkler head spacing
- Emergency exit sign
- Fire hydrant access
- Fire compartment penetration

#### Construction
- Construction sequence change
- Material delivery route
- Crane lifting plan
- Temporary facility location


### Generation Parameters

| Parameter | Value |
|-----------|-------|
| Issues per file | 3-10 |
| Author pool | 5 unique authors |
| Status options | Open, InProgress, Resolved, Closed |
| Temporal range | Past 90 days (uniform distribution) |
| GUID linking | 1-3 random IFC GUIDs per issue |

### Realism Factors
- ✅ Based on real BIM collaboration workflows
- ✅ Issue categories reflect actual construction practice
- ✅ Temporal distribution mimics project lifecycle
- ✅ Author diversity represents multi-disciplinary teams

### Known Limitations
- ⚠️ Templates cover limited issue types (~40 templates)
- ⚠️ No actual project context
- ⚠️ Simplified issue descriptions
- ⚠️ No image attachments
- ⚠️ No threaded comments
- ⚠️ Random GUID assignment (not semantically meaningful)


---

## Reproducibility

### Seed Policy
**FIXED - All random operations use fixed seed for reproducibility**

**Seed Value**: `42`

### Randomized Aspects
- 🎲 Issue template selection
- 🎲 Author assignment
- 🎲 Status assignment
- 🎲 Timestamp generation
- 🎲 GUID selection
- 🎲 Number of issues per file

### Deterministic Aspects
- 🔒 Template content
- 🔒 IFC element types
- 🔒 BCF file structure
- 🔒 XML schema compliance


### Reproduction Instructions

```bash
# Set seed in generation script
export SYNTHETIC_SEED=42

# Regenerate data
python scripts/generate_sample_data.py --seed 42
python scripts/generate_more_bcf.py --seed 42

# Verify checksums
sha256sum data/synthetic/*.bcfzip > checksums.txt
```

---

## Quality Assurance

### Validation Checks
- ✅ IFC schema compliance (ISO 10303-21)
- ✅ BCF XML schema validation
- ✅ GUID format verification
- ✅ Timestamp validity
- ✅ File integrity (ZIP structure)

### Expert Review Plan

- **Target Reviewers**: 2 BIM domain experts
- **Required Expertise**: 5+ years BIM experience

**Review Aspects**:
- Issue realism
- Terminology accuracy
- Workflow plausibility


---

## Academic Integrity

### Declaration

> This dataset includes synthetically generated BCF collaboration issues 
> for research purposes. The generation methodology is fully transparent 
> and documented. All code is open-source and available for inspection.
> 
> We explicitly acknowledge the limitations of synthetic data and 
> recommend validation with real-world project data when available.

### Ethical Considerations

1. **No Misrepresentation**: Synthetic data is clearly labeled
2. **Transparency**: Full methodology disclosure
3. **Reproducibility**: Fixed seed and open-source code
4. **Limitations**: Clearly stated
5. **Validation Plan**: Expert review and real data comparison

---

## Citation

If you use this synthetic dataset, please cite:

```bibtex
@misc{contextualforget_synthetic2025,
  author = {Lee, Junyong},
  title = {ContextualForget Synthetic BIM Collaboration Dataset},
  year = {2025},
  howpublished = {\url{https://github.com/YOUR_REPO}},
  note = {Synthetic BCF issues generated for research purposes. 
          Full methodology: data/synthetic/GENERATION_METHODOLOGY.md}
}
```

---

**Document Hash**: e470f4a1479eba99  
**Maintained By**: ContextualForget Research Team  
**License**: MIT
