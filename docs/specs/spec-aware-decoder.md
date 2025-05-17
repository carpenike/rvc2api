# RV-C Spec-Aware Decoder Enhancement Plan

This spec outlines the architecture and behavior for enhancing the `rvc2api` CANbus decoder with semantic awareness of the official RV-C specification. It allows for real-time detection of unknown or incorrectly defined DGNs by leveraging a FAISS vector index built from the spec PDF.

---

## Goals

- Detect CAN messages with DGNs not defined in `rvc.json` and suggest matching decoder structures based on the official spec.
- Validate existing `rvc.json` entries against the FAISS-indexed spec content.
- Present suggestions and mismatches in the web UI and/or API endpoints for developer review.
- Enable developers to maintain decoder accuracy over time as new messages appear or the spec evolves.

---

## System Components

### 1. FAISS Vector Index
- Built from chunked RV-C spec (PDF)
- Each chunk includes:
  - `section`, `title`, `pages`, `text`, `source`, and `chunking` in metadata
- Embedded using `text-embedding-3-large`

---

## Features

### A. **Unrecognized DGN Detection**
When a message is received with a DGN not defined in `rvc.json`:

1. Backend performs a semantic search using the DGN ID and/or context.
2. Retrieves the best matching spec chunk.
3. Suggests a decoder definition based on that content.
4. Logs and surfaces it via:

   ```json
   {
     "dgn": "1FABC",
     "first_seen": "2025-05-17T10:32:00Z",
     "found_in_json": false,
     "suggestion": {
       "section": "7.3.12",
       "title": "Inverter Output Status",
       "text": "Byte 0: Inverter State..."
     }
   }
   ```

5. Displayed in a **“New DGNs” UI panel** and optionally returned via:

   ```
   GET /spec/unrecognized
   ```

---

### B. **Existing DGN Validation**
For messages with a DGN defined in `rvc.json`:

1. Query FAISS using DGN ID and name.
2. Retrieve matching spec chunk.
3. Compare `rvc.json` definition to spec content:
   - Missing fields
   - Name mismatches
   - Byte offset mismatches

4. Log results as:

   ```json
   {
     "dgn": "1F510",
     "status": "mismatch",
     "issues": [
       {
         "type": "missing_field",
         "byte": 2,
         "description": "Byte 2 is defined in spec but not in rvc.json"
       },
       {
         "type": "name_diff",
         "byte": 1,
         "rvc": "operating status",
         "spec": "status"
       }
     ]
   }
   ```

5. Displayed in a **“Decoder Conflicts” UI panel** and exposed via:

   ```
   GET /spec/mismatches
   ```

---

## Architecture Overview

```
[ CAN Message ]
      ↓
[ rvc.json Lookup ]
      ↓
  ┌────────────┬─────────────┐
  │ Not Found  │ Found       │
  │ (unknown)  │ (defined)   │
  └────┬───────┴───────┬─────┘
       ↓               ↓
  [ FAISS Query ]   [ FAISS Query ]
       ↓               ↓
 [ Best Chunk ]     [ Best Chunk ]
       ↓               ↓
[ Suggest Decoder ] [ Validate Fields ]
       ↓               ↓
[ Store Suggestion ] [ Store Mismatch ]
       ↓               ↓
[ UI Panel + API ] [ UI Panel + API ]
```

---

## Implementation Modules

| Component | Description |
|----------|-------------|
| `seen_dgn_cache` | Tracks first-seen unknown DGNs + suggestions |
| `validate_dgn_fields(dgn_id, rvc_entry)` | Compares `rvc.json` vs FAISS spec |
| `GET /spec/unrecognized` | Returns unknown DGN suggestions |
| `GET /spec/mismatches` | Returns mismatched DGN validations |
| UI: “Suggested Decoders” | List of unknown DGNs with spec context |
| UI: “Decoder Conflicts” | Known DGNs with validation issues |

---

## Future Enhancements

- Allow user to confirm or ignore suggestions via API or UI.
- Output `rvc.json` patch suggestions or diffs.
- Visualize match confidence scores in the UI.
- Support batching re-validation after spec or `rvc.json` update.

---

## Prerequisites

- `rvc.json` loaded in memory or as a file
- FAISS index built from `rvc-spec-*.pdf` using `text-embedding-3-large`
- `langchain`, `faiss`, `openai` Python libraries available
