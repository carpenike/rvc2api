# Setup CAN Testing

Set up virtual CAN environment and run comprehensive CAN bus message testing for RV-C development.

## Virtual CAN Environment Setup

### 1. Initialize Virtual CAN Interfaces
```bash
# Set up vcan interfaces using project script
chmod +x scripts/add_vcan_test_task.sh
./scripts/add_vcan_test_task.sh

# Verify interfaces are created
ip link show | grep vcan
```

### 2. Validate CAN Interface Configuration
```bash
# Check CAN interface status
candump vcan0 &
CANDUMP_PID=$!

# Send test message to verify interface works
cansend vcan0 123#DEADBEEF

# Stop candump
kill $CANDUMP_PID 2>/dev/null || true
```

## RV-C Message Testing

### 3. Test Virtual CAN Setup
```bash
# Run comprehensive vcan test
poetry run python dev_tools/test_vcan.py

# Test vcan setup validation
poetry run python dev_tools/test_vcan_setup.py
```

### 4. Validate CAN Bus Configuration
```bash
# Test CAN bus configuration parsing
poetry run python dev_tools/test_canbus_config.py

# Verify RV-C JSON configuration loads correctly
poetry run python dev_tools/validate_rvc_json.py
```

## RV-C Protocol Validation

### 5. Test RV-C Message Decoding
```bash
# Test RV-C decoder with sample messages
poetry run python -c "
from backend.integrations.rvc.decode import decode_rvc_message
from backend.integrations.rvc.config_loader import load_rvc_config

# Load RV-C configuration
config = load_rvc_config()
print(f'Loaded {len(config.get(\"pgns\", {}))} PGNs from RV-C spec')

# Test decoding sample message (DC Dimmer Status)
sample_data = bytes.fromhex('FF0A0000FFFF0000')
result = decode_rvc_message(0x1FEDB, sample_data, config)
print(f'Decoded message: {result}')
"
```

### 6. Monitor CAN Message Flow
```bash
# Start backend with CAN interfaces enabled
COACHIQ_CAN__INTERFACES=vcan0,vcan1 poetry run python run_server.py --debug &
BACKEND_PID=$!

# Allow startup time
sleep 3

# Send sample RV-C messages and monitor processing
echo "Sending sample RV-C messages..."
cansend vcan0 1FEDB023#FF0A0000FFFF0000  # DC Dimmer Status
cansend vcan0 1FED9023#010000FFFFFFFFFF  # DC Load Command
cansend vcan0 1FEF1023#FFFFFFFFFFFFFFFF  # DateTime

# Check backend logs for message processing
echo "Check backend logs for CAN message processing..."

# Cleanup
kill $BACKEND_PID 2>/dev/null || true
```

## Entity State Testing

### 7. Test Entity State Updates
```bash
# Verify entities are created and updated by CAN messages
COACHIQ_CAN__INTERFACES=vcan0 poetry run python -c "
import asyncio
import time
from backend.core.config import get_settings
from backend.services.feature_manager import FeatureManager
from backend.core.state import AppState

async def test_entity_updates():
    # Initialize feature manager
    feature_manager = FeatureManager()
    await feature_manager.startup()

    # Get entity manager
    entity_feature = feature_manager.get_feature('entity_manager')
    entity_manager = entity_feature.get_entity_manager()

    print(f'Initial entities: {len(entity_manager.get_all_entities())}')

    # Send CAN message that should create/update entity
    import subprocess
    subprocess.run(['cansend', 'vcan0', '1FEDB023#FF0A0000FFFF0000'])

    # Wait for processing
    await asyncio.sleep(0.5)

    entities = entity_manager.get_all_entities()
    print(f'Entities after CAN message: {len(entities)}')

    # Show entity details
    for entity_id, entity in entities.items():
        print(f'Entity {entity_id}: {entity.state}')

    await feature_manager.shutdown()

asyncio.run(test_entity_updates())
"
```

## Memory Management Testing

### 8. Test CAN Message Buffer Management
```bash
# Test memory management under high message load
poetry run python -c "
import asyncio
import time
import subprocess
from backend.services.can_service import CANService
from backend.core.config import get_settings

async def test_memory_management():
    settings = get_settings()
    can_service = CANService(settings.can)

    # Start CAN service
    await can_service.startup()

    print('Sending high-frequency CAN messages...')

    # Send burst of messages to test buffer limits
    for i in range(100):
        subprocess.run(['cansend', 'vcan0', f'1FEDB02{i%10:01X}#FF0A0000FFFF000{i%10:01X}'])
        if i % 10 == 0:
            await asyncio.sleep(0.01)  # Brief pause every 10 messages

    # Wait for processing
    await asyncio.sleep(1)

    # Check buffer status
    status = await can_service.get_queue_status()
    print(f'CAN queue status: {status}')

    await can_service.shutdown()

asyncio.run(test_memory_management())
"
```

## Cleanup and Verification

### 9. Health Check and Cleanup
```bash
# Verify all CAN interfaces are working
echo "=== CAN Interface Status ==="
ip link show | grep vcan

# Check for any stuck processes
echo "=== Process Check ==="
ps aux | grep -E "(candump|cansend|run_server)" | grep -v grep || echo "No CAN processes running"

# Verify configuration files are accessible
echo "=== Configuration Files ==="
[ -f "config/rvc.json" ] && echo "✓ RV-C spec found" || echo "✗ RV-C spec missing"
[ -f "config/coach_mapping.default.yml" ] && echo "✓ Coach mapping found" || echo "✗ Coach mapping missing"

echo "=== CAN Testing Complete ==="
echo "Virtual CAN environment is ready for development"
echo "Use 'candump vcan0' to monitor CAN traffic"
echo "Use 'cansend vcan0 <id>#<data>' to send test messages"
```

## Arguments

$ARGUMENTS can specify:
- `--interfaces <list>` - Specify which vcan interfaces to set up (default: vcan0,vcan1)
- `--skip-validation` - Skip RV-C message validation tests
- `--no-cleanup` - Leave test processes running for debugging
- `--load-test` - Run high-frequency message load testing
- `--verbose` - Show detailed output from all test commands

## Development Notes

### Common CAN Message IDs for Testing
- `1FEDB023` - DC Dimmer Status (lights)
- `1FED9023` - DC Load Command (switches)
- `1FEF1023` - DateTime Status
- `1FECA023` - AC Load Status
- `1FECB023` - AC Load Command

### Troubleshooting
- If vcan interfaces fail to create, run with `sudo` or check kernel modules
- If no messages are received, verify `COACHIQ_CAN__INTERFACES` environment variable
- If decoder fails, check `config/rvc.json` file permissions and syntax
- For performance issues, monitor backend logs during message bursts

This command sets up a complete CAN testing environment for RV-C development, including virtual interfaces, message validation, entity state testing, and memory management verification.
