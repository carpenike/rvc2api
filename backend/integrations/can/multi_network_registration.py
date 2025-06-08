"""
Multi-Network CAN Feature Registration

Registers the multi-network CAN feature with the feature management system.
"""

from backend.integrations.can.multi_network_feature import MultiNetworkCANFeature


def register_multi_network_feature(**kwargs) -> MultiNetworkCANFeature:
    """Factory function for MultiNetworkCANFeature."""
    return MultiNetworkCANFeature(**kwargs)
