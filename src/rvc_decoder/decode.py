"""
rvc_decoder.decode

Core decoding logic for RV-C CAN frames, including loading of spec and device mapping data.

Functions:
    - get_bits: Extracts a little-endian bitfield from a CAN payload
    - decode_payload: Decodes all signals in a spec entry
    - load_config_data: Loads and parses RVC spec and device mapping,
    returning all lookup tables and coach metadata

Notes:
    - CoachInfo includes year, make, model, trim, filename, and notes fields.
    - Mapping/model selection logic supports model-specific mapping files and full-path overrides.
"""

import json
import logging
import os
import sys
from importlib import resources

import yaml

from common.models import CoachInfo

logger = logging.getLogger(__name__)  # Added named logger


def _default_paths():
    """
    Determine default paths for the rvc spec and device mapping files bundled as package data.
    """
    # Expect config files to live under the 'config' directory in this package
    cfg_dir = resources.files(__package__) / "config"
    return (
        str(cfg_dir / "rvc.json"),
        str(cfg_dir / "device_mapping.yml"),
    )


def get_bits(data_bytes: bytes, start_bit: int, length: int) -> int:
    """
    Extract a little-endian bitfield from an 8-byte CAN payload.
    """
    raw_int = int.from_bytes(data_bytes, byteorder="little")
    mask = (1 << length) - 1
    return (raw_int >> start_bit) & mask


def decode_payload(entry: dict, data_bytes: bytes) -> tuple[dict[str, str], dict[str, int]]:
    """
    Decode all 'signals' in a spec entry:
      - raw_values: the integer bitfields
      - decoded: human-readable strings (with scale/offset/enum logic)

    Returns:
      tuple(decoded: dict[str,str], raw_values: dict[str,int])
    """
    decoded = {}
    raw_values = {}

    for sig in entry.get("signals", []):
        raw = get_bits(data_bytes, sig["start_bit"], sig["length"])
        raw_values[sig["name"]] = raw

        # apply scale/offset
        val = raw * sig.get("scale", 1) + sig.get("offset", 0)
        unit = sig.get("unit", "")

        # enum lookup if present
        if "enum" in sig:
            formatted = sig["enum"].get(str(raw))
            if formatted is None:
                formatted = f"UNKNOWN ({raw})"
        elif sig.get("scale", 1) != 1 or sig.get("offset", 0) != 0 or isinstance(val, float):
            formatted = f"{val:.2f}{unit}"
        else:
            formatted = f"{int(val)}{unit}"

        decoded[sig["name"]] = formatted

    return decoded, raw_values


def load_config_data(
    rvc_spec_path_override: str | None = None,  # Renamed parameter
    device_mapping_path_override: str | None = None,  # Renamed parameter
) -> tuple[
    dict[int, dict],
    dict,
    dict[tuple[str, str], dict],
    dict[tuple[str, str], dict],
    set[str],
    dict[str, dict],
    dict[str, dict],
    dict[str, str],  # Added for pgn_hex_to_name_map
    dict,  # Added for dgn_pairs
    CoachInfo,  # Return CoachInfo model instead of dict
]:
    """
    Load and parse:
      1. RVC spec JSON → decoder_map (PGN→spec entry, adds 'dgn_hex')
      2. device_mapping YAML →
         • device_lookup ((dgn_hex,inst)→config)
         • status_lookup ((status_dgn,inst)→config)
         • entity_id_lookup (id→config)
         • light_entity_ids (set of IDs)
         • light_command_info (id→{dgn,instance,interface})
         • coach_info (year, make, model, trim, filename, notes)

    Path selection logic:
      - If device_mapping_path_override is provided and valid, use it.
      - Else, if the CAN_MODEL_SELECTOR environment variable is set, use
        <config_dir>/<model>.yml as the mapping file (e.g., 2021_Entegra_Aspire_44R.yml).
      - Else, use the default device_mapping.yml.
      - This allows flake.nix to set a model selector, but a full path can still override.

    Args:
        rvc_spec_path_override (str | None): Optional path to an RVC specification JSON file.
        device_mapping_path_override (str | None): Optional path to a device mapping YAML file.

    Returns:
      decoder_map: dict[int,dict],
      device_mapping: dict,
      device_lookup: dict[tuple[str,str],dict],
      status_lookup: dict[tuple[str,str],dict],
      light_entity_ids: set[str],
      entity_id_lookup: dict[str,dict],
      light_command_info: dict[str,dict],
      pgn_hex_to_name_map: dict[str, str],
      dgn_pairs: dict,
      coach_info: CoachInfo  # coach/model metadata (year, make, model, trim, filename, notes)
    """
    # --- MODIFICATION START: Path selection logic ---
    default_spec_path, default_mapping_path = _default_paths()

    # Determine final spec path
    rvc_spec_path = default_spec_path  # Default
    if rvc_spec_path_override:
        if os.path.exists(rvc_spec_path_override) and os.access(rvc_spec_path_override, os.R_OK):
            logger.info(f"Using RVC spec override: {rvc_spec_path_override}")
            rvc_spec_path = rvc_spec_path_override
        else:
            logger.warning(
                f"RVC spec override path provided but not found/readable: "
                f"{rvc_spec_path_override}. Using default: {default_spec_path}"
            )
    else:
        logger.info(f"Using default RVC spec path: {default_spec_path}")

    # Determine final mapping path
    device_mapping_path = default_mapping_path  # Default
    mapping_source = "default"
    model_selector = None
    available_mappings = []
    if device_mapping_path_override:
        if os.path.exists(device_mapping_path_override) and os.access(
            device_mapping_path_override, os.R_OK
        ):
            logger.info(f"Using explicit device mapping override: {device_mapping_path_override}")
            device_mapping_path = device_mapping_path_override
            mapping_source = "override"
        else:
            logger.warning(
                f"Device mapping override path provided but not found/readable: "
                f"{device_mapping_path_override}. Will check model selector or fallback."
            )
    else:
        # Check for CAN_MODEL_SELECTOR env var
        # (case-insensitive, extension-flexible, flexible delimiters)
        model_selector = os.getenv("CAN_MODEL_SELECTOR")
        if model_selector:
            config_dir = os.path.dirname(default_mapping_path)
            # Normalize selector: replace spaces with underscores,
            # lowercase, strip extension if present
            selector_norm = os.path.splitext(model_selector.replace(" ", "_").lower())[0]
            try:
                available_mappings = [
                    fname
                    for fname in os.listdir(config_dir)
                    if os.path.splitext(fname)[1].lower() in (".yml", ".yaml")
                ]
                found = False
                for fname in available_mappings:
                    base, ext = os.path.splitext(fname)
                    base_norm = base.replace(" ", "_").lower()
                    if base_norm == selector_norm:
                        candidate = os.path.join(config_dir, fname)
                        if os.path.exists(candidate) and os.access(candidate, os.R_OK):
                            logger.info(
                                f"Model selector requested: '{model_selector}' "
                                f"→ Using mapping file: {candidate}"
                            )
                            device_mapping_path = candidate
                            mapping_source = f"modelSelector ({model_selector})"
                            found = True
                            break
                if not found:
                    logger.warning(
                        f"Requested model mapping '{model_selector}' not found in {config_dir}."
                    )
                    logger.warning(f"Available mapping files: {available_mappings}")
                    logger.warning(f"Falling back to default mapping: {default_mapping_path}")
            except Exception as e:
                logger.warning(f"Could not scan mapping directory '{config_dir}': {e}")
        else:
            logger.info(
                f"No device mapping override or model selector set. "
                f"Using default mapping: {default_mapping_path}"
            )

    logger.info(
        f"Device mapping file in use: {device_mapping_path} (source: "
        f"{mapping_source if mapping_source != 'default' else 'default/fallback'})"
    )

    # --- MODIFICATION END ---

    # 1) Load spec
    if not os.path.exists(rvc_spec_path) or not os.access(rvc_spec_path, os.R_OK):
        logger.error(f"Cannot read RVC spec: {rvc_spec_path}")  # Changed to logger.error
        sys.exit(1)
    with open(rvc_spec_path) as f:
        spec_content = json.load(f)

    specs = spec_content.get("messages", [])
    decoder_map: dict[int, dict] = {}
    for entry in specs:
        sid = entry.get("id")
        if sid is None:
            # logger.warning(f"Skipping spec without 'id': {entry}")
            continue
        try:
            dec_id = sid if isinstance(sid, int) else int(sid, 16)
        except ValueError:
            # logger.warning(f"Invalid 'id' in spec: {sid}")
            continue
        entry["dgn_hex"] = f"{(dec_id >> 8) & 0x3FFFF:X}"
        decoder_map[dec_id] = entry
    # logger.info(f"Loaded {len(decoder_map)} spec entries.")

    # Create a map from PGN hex string to PGN name for unmapped entry enrichment
    pgn_hex_to_name_map: dict[str, str] = {}
    if decoder_map:  # Check if decoder_map was successfully populated
        for spec_entry in decoder_map.values():
            pgn_val_int = spec_entry.get("pgn")
            pgn_name_str = spec_entry.get("name")
            if pgn_val_int is not None and pgn_name_str:
                current_pgn_hex_key = f"{pgn_val_int:X}".upper()
                if current_pgn_hex_key not in pgn_hex_to_name_map:
                    pgn_hex_to_name_map[current_pgn_hex_key] = pgn_name_str

    # 2) Load device mapping
    device_mapping: dict = {}
    device_lookup: dict = {}
    status_lookup: dict = {}
    entity_id_lookup: dict = {}
    light_entity_ids: set = set()
    light_command_info: dict = {}
    coach_info = {}

    if os.path.exists(device_mapping_path):
        with open(device_mapping_path) as f:
            raw_map = yaml.safe_load(f) or {}
        templates = raw_map.get("templates", {})
        device_mapping = raw_map

        # --- Coach info extraction ---
        if "coach_info" in raw_map and isinstance(raw_map["coach_info"], dict):
            coach_info = dict(raw_map["coach_info"])
            # Normalize year to string if present
            if "year" in coach_info and coach_info["year"] is not None:
                coach_info["year"] = str(coach_info["year"])
            coach_info.setdefault("filename", os.path.basename(device_mapping_path))
        else:
            # Fallback: parse filename for year/make/model/trim (supports underscores or spaces)
            fname = os.path.basename(device_mapping_path)
            base, _ = os.path.splitext(fname)
            # Try underscores first, then spaces
            parts = base.split("_", 3) if "_" in base else base.split(" ", 3)
            if len(parts) == 4 and parts[0].isdigit():
                coach_info = {
                    "year": str(parts[0]),
                    "make": parts[1],
                    "model": parts[2],
                    "trim": parts[3],
                    "filename": fname,
                    "notes": "(parsed from filename)",
                }
            elif len(parts) == 3 and parts[0].isdigit():
                coach_info = {
                    "year": str(parts[0]),
                    "make": parts[1],
                    "model": parts[2],
                    "filename": fname,
                    "notes": "(parsed from filename)",
                }
            else:
                coach_info = {
                    "filename": fname,
                    "notes": "No coach_info in YAML; could not parse model from filename.",
                }

        # Extract dgn_pairs mapping if present
        dgn_pairs = raw_map.get("dgn_pairs", {})

        for dgn_hex, instances in raw_map.items():
            if dgn_hex in ("templates", "dgn_pairs") or not isinstance(instances, dict):
                continue
            for inst_str, configs in instances.items():
                if not isinstance(configs, list):
                    continue
                for cfg in configs:
                    if not isinstance(cfg, dict):
                        continue
                    tmpl = cfg.pop("<<", None)
                    merged = {**templates.get(tmpl, {}), **cfg} if tmpl else cfg

                    eid = merged.get("entity_id")
                    fname = merged.get("friendly_name")
                    # log_msg_processing = (
                    #     f"Processing entry: DGN={dgn_hex}, Inst={inst_str}, "
                    #     f"Raw Cfg EID={cfg.get('entity_id')}, Merged EID={eid}, "
                    #     f"Merged FName={fname}"
                    # )
                    # logger.info(log_msg_processing)
                    if eid and fname:
                        # log_msg_adding = (
                        #     f"Adding to entity_id_lookup: eid='{eid}', fname='{fname}' "
                        #     f"with merged data: {json.dumps(merged, indent=2)}"
                        # )
                        # logger.info(log_msg_adding)
                        key = (dgn_hex.upper(), str(inst_str))
                        device_lookup[key] = merged
                        entity_id_lookup[eid] = merged

                        sd = merged.get("status_dgn")
                        if sd:
                            status_lookup[(sd.upper(), str(inst_str))] = merged

                        if merged.get("device_type") == "light":
                            light_entity_ids.add(eid)
                            light_command_info[eid] = {
                                "dgn": int(dgn_hex, 16),
                                "instance": int(inst_str),
                                "interface": merged.get("interface"),
                            }
                    else:
                        # log_msg_skipping = (
                        #     f"Skipping entry for entity_id_lookup:
                        #     DGN={dgn_hex}, Inst={inst_str}, "
                        #     f"Raw Cfg EID={cfg.get('entity_id')}, Merged EID={eid}, "
                        #     f"Merged FName={fname}. "
                        #     "eid and fname must be present and non-empty."
                        # )
                        # logger.warning(log_msg_skipping)
                        pass
        # logger.info(f"Loaded {len(device_lookup)} device_lookup entries.")
        # logger.info(f"Loaded {len(status_lookup)} status_lookup entries.")
        # status_keys_to_log = list(status_lookup.keys())
        # if len(status_keys_to_log) > 50:
        #     logger.info(f"status_lookup keys (first 50): {status_keys_to_log[:50]}")
        # else:
        #     logger.info(f"status_lookup keys: {status_keys_to_log}")
    else:
        logger.error(f"Device mapping file NOT FOUND: {device_mapping_path}")
        # fallback: still try to provide coach_info from path
        fname = os.path.basename(device_mapping_path)
        base, _ = os.path.splitext(fname)
        parts = base.split("_", 3) if "_" in base else base.split(" ", 3)
        if len(parts) == 4 and parts[0].isdigit():
            coach_info = {
                "year": str(parts[0]),
                "make": parts[1],
                "model": parts[2],
                "trim": parts[3],
                "filename": fname,
                "notes": "(parsed from filename; mapping file not found)",
            }
        elif len(parts) == 3 and parts[0].isdigit():
            coach_info = {
                "year": str(parts[0]),
                "make": parts[1],
                "model": parts[2],
                "filename": fname,
                "notes": "(parsed from filename; mapping file not found)",
            }
        else:
            coach_info = {
                "filename": fname,
                "notes": "Mapping file not found; no coach_info available.",
            }

    coach_info_model = CoachInfo(**coach_info)
    return (
        decoder_map,
        device_mapping,
        device_lookup,
        status_lookup,
        light_entity_ids,
        entity_id_lookup,
        light_command_info,
        pgn_hex_to_name_map,  # Return the new map
        dgn_pairs,  # Return dgn_pairs as the 9th item
        coach_info_model,  # Return as CoachInfo model
    )
