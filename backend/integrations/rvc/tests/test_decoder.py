"""
Unit and integration tests for the RVC decoder feature.

This file is colocated with the backend.integrations.rvc package for best monorepo practices.
"""

from pathlib import Path

import pytest

from backend.integrations.rvc.feature import RVCFeature
from backend.models.common import CoachInfo


@pytest.fixture
def rvc_feature() -> RVCFeature:
    """
    Create an RVCFeature instance for testing, using the default coach mapping file.
    """
    mapping_path = str(Path(__file__).parent.parent / "config/coach_mapping.default.yml")
    return RVCFeature(
        name="rvc", enabled=True, core=True, config={"device_mapping_path": mapping_path}
    )


@pytest.mark.asyncio
async def test_rvc_feature_startup(rvc_feature: RVCFeature) -> None:
    """
    Test that the RVC feature can start up and load data.
    """
    await rvc_feature.startup()
    assert rvc_feature.is_data_loaded() is True
    assert isinstance(rvc_feature.coach_info, CoachInfo)
    assert len(rvc_feature.dgn_dict) > 0
    assert len(rvc_feature.entity_ids) > 0
    await rvc_feature.shutdown()


@pytest.mark.asyncio
async def test_rvc_decode_basics() -> None:
    """
    Test basic RVC decoding functionality.
    """
    from backend.integrations.rvc import decode

    data = bytes([1, 2, 0, 0, 0, 0, 0, 0])
    assert decode.get_bits(data, 0, 8) == 1
    assert decode.get_bits(data, 8, 8) == 2
    assert decode.get_bits(data, 0, 16) == 513
