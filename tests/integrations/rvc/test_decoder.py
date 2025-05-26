"""
Tests for RVC decoder integration.

This module contains tests for the RVC feature and decoder, ensuring correct loading of
configuration, coach info, and decoding logic.
"""

from pathlib import Path

import pytest

from backend.integrations.rvc.feature import RVCFeature
from backend.models.common import CoachInfo


@pytest.fixture
def rvc_feature() -> RVCFeature:
    """
    Create an RVCFeature instance for testing, using the default coach mapping file.

    Returns:
        RVCFeature: Configured RVC feature instance.
    """
    mapping_path = str(
        Path(__file__).parent.parent.parent.parent
        / "backend/integrations/rvc/config/coach_mapping.default.yml"
    )
    return RVCFeature(
        name="rvc", enabled=True, core=True, config={"device_mapping_path": mapping_path}
    )


@pytest.mark.asyncio
async def test_rvc_feature_startup(rvc_feature: RVCFeature) -> None:
    """
    Test that the RVC feature can start up and load data.

    Asserts that data is loaded, coach_info is present, and DGN/entity data is available.
    """
    await rvc_feature.startup()
    assert rvc_feature.is_data_loaded() is True, "Feature should report data loaded."
    assert isinstance(rvc_feature.coach_info, CoachInfo), "coach_info should be CoachInfo instance."
    assert len(rvc_feature.dgn_dict) > 0, "DGN dictionary should not be empty."
    assert len(rvc_feature.entity_ids) > 0, "Entity IDs should not be empty."
    await rvc_feature.shutdown()


@pytest.mark.asyncio
async def test_rvc_decode_basics() -> None:
    """
    Test basic RVC decoding functionality.

    Verifies bit extraction from CAN payload using decode.get_bits.
    """
    from backend.integrations.rvc import decode

    data = bytes([1, 2, 0, 0, 0, 0, 0, 0])  # 0x0201 in little-endian
    assert decode.get_bits(data, 0, 8) == 1, "First byte should be 1."
    assert decode.get_bits(data, 8, 8) == 2, "Second byte should be 2."
    assert decode.get_bits(data, 0, 16) == 513, "First two bytes as 16-bit int should be 513."


@pytest.mark.asyncio
async def test_rvc_feature_config_and_mapping(rvc_feature: RVCFeature) -> None:
    """
    Test that the RVC feature loads config and device mapping data correctly.
    """
    await rvc_feature.startup()
    assert hasattr(rvc_feature, "config"), "RVCFeature should have a config attribute."
    assert rvc_feature.config is not None, "Config should not be None."
    assert hasattr(rvc_feature, "dgn_dict"), "RVCFeature should have a dgn_dict attribute."
    assert isinstance(rvc_feature.dgn_dict, dict), "dgn_dict should be a dict."
    assert all(isinstance(k, int) for k in rvc_feature.dgn_dict), "All dgn_dict keys should be int."
    await rvc_feature.shutdown()


@pytest.mark.asyncio
async def test_rvc_feature_coach_info_fields(rvc_feature: RVCFeature) -> None:
    """
    Test that coach_info fields are populated correctly (allow fallback values).
    """
    await rvc_feature.startup()
    coach_info = rvc_feature.coach_info
    assert coach_info is not None, "coach_info should not be None."
    assert hasattr(coach_info, "make"), "coach_info should have 'make' attribute."
    assert hasattr(coach_info, "model"), "coach_info should have 'model' attribute."
    assert hasattr(coach_info, "year"), "coach_info should have 'year' attribute."
    if coach_info.make is not None:
        assert isinstance(coach_info.make, str), "coach_info.make should be a string."
    if coach_info.model is not None:
        assert isinstance(coach_info.model, str), "coach_info.model should be a string."
    if coach_info.year is not None:
        assert isinstance(coach_info.year, str), "coach_info.year should be a string."
    await rvc_feature.shutdown()


@pytest.mark.asyncio
async def test_rvc_decode_entity_mapping(rvc_feature: RVCFeature) -> None:
    """
    Test decoding a sample CAN message and mapping to an entity/state.
    """
    from backend.integrations.rvc import decode

    await rvc_feature.startup()
    dgns = list(rvc_feature.dgn_dict.keys())
    if not dgns:
        pytest.skip("No DGN definitions available for test.")
    dgn = dgns[0]
    dgn_def = rvc_feature.dgn_dict[dgn]
    payload_len = dgn_def.get("length", 8)
    payload = bytes([0] * payload_len)
    decoded, raw = decode.decode_payload(dgn_def, payload)
    assert isinstance(decoded, dict), "Decoded payload should be a dict."
    assert isinstance(raw, dict), "Raw payload should be a dict."
    assert len(decoded) > 0 or len(raw) > 0, "Decoded or raw dict should not be empty."
    await rvc_feature.shutdown()


@pytest.mark.asyncio
async def test_rvc_decode_error_handling() -> None:
    """
    Test error handling for invalid payloads.
    """
    from backend.integrations.rvc import decode

    dgn_def = {"length": 8, "signals": []}
    payload = bytes([1, 2])  # Too short
    decoded, raw = decode.decode_payload(dgn_def, payload)
    assert decoded == {}, "Decoded dict should be empty for invalid payload."
    assert raw == {}, "Raw dict should be empty for invalid payload."


@pytest.mark.asyncio
async def test_rvc_feature_shutdown_clears_state(rvc_feature: RVCFeature) -> None:
    """
    Test that shutdown clears or resets feature state.
    """
    await rvc_feature.startup()
    await rvc_feature.shutdown()
    assert not rvc_feature.is_data_loaded(), "Data should not be loaded after shutdown."
