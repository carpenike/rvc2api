# Spec-Aware Decoder: Live RV-C Definition and Validation via FAISS

## 1. Objective

### 1.1. Purpose
- Automatically identify and suggest decoder structures for unknown DGNs observed on the CANbus.
- Validate and improve existing `rvc.json` entries against the official RV-C spec (via semantic embedding).
- Enable faster, more accurate development of coach-specific decoder mappings.

### 1.2. Scope
- Affected: `rvc.json`, FastAPI backend, decoder engine, UI (developer panel).
- Unchanged: CANbus reader, core FastAPI routing, spec chunking/indexing.
- Boundaries: This feature reads FAISS index and logs or suggests decoder changes — it does not automatically update persistent files.

---

## 2. Current State Analysis

### 2.1. Decoder Structure
- `rvc.json` contains hard-coded decoder definitions keyed by DGN ID.
- Unknown DGNs are either dropped or logged with no semantic analysis.
- Validation of existing entries requires manual review of PDF spec.

### 2.2. Limitations
- Unknown DGNs require manual research and YAML entry.
- No mechanism to detect stale, inaccurate, or incomplete `rvc.json` entries.
- Missed opportunity to leverage the existing FAISS spec embedding index.

---

## 3. Functional Design

### 3.1. Runtime Decoder Pipeline Enhancements
- For each CAN message:
  - If DGN is unknown:
    - Query FAISS for spec chunk
    - Suggest decoder structure in UI/API
  - If DGN is known:
    - Query FAISS
    - Compare structure to `rvc.json`
    - Log or expose mismatches

### 3.2. Suggested Decoder Structure Output
- Section title and text from spec
- Proposed JSON structure with field names, types, and units
- Optional UI copy-paste block

### 3.3. Mismatch Detection
- Field-level diff between `rvc.json` and spec:
  - Missing bytes
  - Name differences
  - Byte offset misalignment
- Displayed in a validation panel in UI or exposed via:
  ```
  GET /spec/mismatches
  ```

---

## 4. Implementation Strategy

### 4.1. Modules and Interfaces
- `seen_dgn_cache.py`: In-memory (or persistent) cache of unknown DGNs + suggestions
- `validate_dgn_fields.py`: Validator for known DGNs
- `GET /spec/unrecognized`: List of undefined DGNs + spec matches
- `GET /spec/mismatches`: List of mismatched DGN validations
- UI: “New DGNs” panel for spec-based decoder suggestions
- UI: “Decoder Conflicts” panel for existing entry validation

### 4.2. UI Enhancements
- “New DGNs” panel for spec-based decoder suggestions
- “Decoder Conflicts” panel for existing entry validation

---

## 5. Testing Strategy

- Unit tests for suggestion and validation logic
- Mocked FAISS index queries with synthetic DGN inputs
- UI tests to validate developer panels render expected output
- Optional golden test set comparing `rvc.json` against fixed FAISS chunks

---

## 6. Documentation Updates

- Update `rvc.json` format documentation to include `"proposed": true` and `"source": "faiss"` fields.
- Add dev guide for running decoder validator tools.
- Include reference to `validate_rvc_json.py` and `/spec/mismatches` endpoint.

---

## 7. Execution Checklist

### 7.1. API and Decoder Engine
- [ ] Add runtime DGN hook for unknown DGN capture
- [ ] Implement FAISS lookup for unknown DGN
- [ ] Build `seen_dgn_cache` structure
- [ ] Build validation function for existing DGN entries
- [ ] Add FastAPI endpoints

### 7.2. UI Integration
- [ ] Add “New DGNs” panel
- [ ] Add “Decoder Conflicts” panel

### 7.3. Developer Tooling
- [ ] Integrate `validate_rvc_json.py` into dev workflow
- [ ] Add support for exporting proposed decoders

---

## 8. Future Enhancements

- Allow user confirmation of decoder suggestions via UI
- Auto-generate pull requests for `rvc.json` updates
- Add similarity confidence scoring to UI
- Periodic batch re-validation of all DGNs

---

## 9. References

- [LangChain FAISS integration](https://docs.langchain.com/docs/integrations/vectorstores/faiss)
- [RV-C Specification PDF, 2023 Edition]
- [`generate_embeddings.py` / `generate_faiss_index.py` scripts]
- [Existing spec: Refactor Web UI to Standalone React App]
