# RV-C Debug

Comprehensive RV-C protocol debugging, testing, and validation workflow for message encoding/decoding, PGN/SPN analysis, and real-time protocol monitoring.

## RV-C Configuration Validation

### 1. Validate RV-C Specification
```bash
# Validate RV-C JSON configuration file
echo "Validating RV-C specification..."
poetry run python dev_tools/validate_rvc_json.py

# Check RV-C configuration loading
poetry run python -c "
from backend.integrations.rvc.config_loader import load_rvc_config
from pathlib import Path

try:
    config = load_rvc_config()

    if config:
        pgns = config.get('pgns', {})
        spns = config.get('spns', {})

        print(f'✓ RV-C configuration loaded successfully')
        print(f'✓ PGNs defined: {len(pgns)}')
        print(f'✓ SPNs defined: {len(spns)}')

        # Show sample PGNs
        print(f'\\nSample PGNs:')
        for i, (pgn_id, pgn_data) in enumerate(list(pgns.items())[:5]):
            name = pgn_data.get('name', 'Unknown')
            print(f'  PGN {pgn_id}: {name}')

        if len(pgns) > 5:
            print(f'  ... and {len(pgns) - 5} more PGNs')
    else:
        print('✗ Failed to load RV-C configuration')

except Exception as e:
    print(f'✗ RV-C configuration error: {e}')
"
```

### 2. Test RV-C Feature Enablement
```bash
# Check RV-C feature status
poetry run python -c "
import asyncio
from backend.services.feature_manager import FeatureManager

async def check_rvc_feature():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    if feature_manager.is_enabled('rvc'):
        print('✓ RV-C feature is enabled')

        rvc_feature = feature_manager.get_feature('rvc')
        print(f'✓ RV-C feature health: {rvc_feature.health}')

        # Check feature configuration
        feature_config = feature_manager.get_feature_config('rvc')
        print(f'✓ Encoder enabled: {feature_config.get(\"enable_encoder\", False)}')
        print(f'✓ Validator enabled: {feature_config.get(\"enable_validator\", False)}')
        print(f'✓ Security enabled: {feature_config.get(\"enable_security\", False)}')

    else:
        print('✗ RV-C feature is disabled')
        print('Enable with COACHIQ_FEATURES__ENABLE_RVC=true')

    await feature_manager.shutdown()

asyncio.run(check_rvc_feature())
"
```

## RV-C Message Decoding Tests

### 3. Test RV-C Decoder with Sample Messages
```bash
# Test RV-C message decoding with known message types
echo "Testing RV-C message decoding..."

poetry run python -c "
from backend.integrations.rvc.decode import decode_rvc_message
from backend.integrations.rvc.config_loader import load_rvc_config

# Load RV-C configuration
config = load_rvc_config()

# Test cases with known RV-C messages
test_messages = [
    {
        'name': 'DC Dimmer Status (PGN 65240)',
        'pgn': 0x1FED8,  # 131032 decimal
        'data': bytes.fromhex('FF0A0000FFFF0000'),
        'expected': 'dimmer status message'
    },
    {
        'name': 'DC Load Command (PGN 65241)',
        'pgn': 0x1FED9,  # 131033 decimal
        'data': bytes.fromhex('010000FFFFFFFFFF'),
        'expected': 'load command message'
    },
    {
        'name': 'DateTime Status (PGN 65265)',
        'pgn': 0x1FEF1,  # 131057 decimal
        'data': bytes.fromhex('FFFFFFFFFFFFFFFF'),
        'expected': 'datetime status'
    },
    {
        'name': 'AC Load Status (PGN 65202)',
        'pgn': 0x1FECA,  # 130762 decimal
        'data': bytes.fromhex('FF00FFFFFFFFFFFF'),
        'expected': 'AC load status'
    }
]

print('Testing RV-C message decoding...')
print()

success_count = 0
for test in test_messages:
    try:
        result = decode_rvc_message(test['pgn'], test['data'], config)

        if result:
            print(f'✓ {test[\"name\"]}:')
            print(f'  PGN: 0x{test[\"pgn\"]:04X} ({test[\"pgn\"]})')
            print(f'  Data: {test[\"data\"].hex().upper()}')
            print(f'  Decoded: {result}')
            success_count += 1
        else:
            print(f'⚠ {test[\"name\"]}: No decoding result')

    except Exception as e:
        print(f'✗ {test[\"name\"]}: Decoding error - {e}')

    print()

print(f'Decoding test results: {success_count}/{len(test_messages)} successful')
"
```

### 4. Test RV-C Encoder Functionality
```bash
# Test RV-C message encoding (if encoder is available)
echo "Testing RV-C message encoding..."

poetry run python -c "
try:
    from backend.integrations.rvc.encoder import encode_rvc_message
    encoder_available = True
except ImportError:
    print('ℹ RV-C encoder not available (encoder.py not implemented)')
    encoder_available = False

if encoder_available:
    from backend.integrations.rvc.config_loader import load_rvc_config

    config = load_rvc_config()

    # Test encoding common RV-C commands
    test_commands = [
        {
            'name': 'Turn on light (instance 1)',
            'pgn': 0x1FED9,  # DC Load Command
            'command': {
                'instance': 1,
                'command': 'on',
                'brightness': 100
            }
        },
        {
            'name': 'Dim light to 50% (instance 2)',
            'pgn': 0x1FED9,
            'command': {
                'instance': 2,
                'command': 'set',
                'brightness': 50
            }
        }
    ]

    print('Testing RV-C message encoding...')

    for test in test_commands:
        try:
            encoded_data = encode_rvc_message(test['pgn'], test['command'], config)

            if encoded_data:
                print(f'✓ {test[\"name\"]}:')
                print(f'  Command: {test[\"command\"]}')
                print(f'  Encoded: {encoded_data.hex().upper()}')
            else:
                print(f'⚠ {test[\"name\"]}: No encoding result')

        except Exception as e:
            print(f'✗ {test[\"name\"]}: Encoding error - {e}')

        print()
else:
    print('Skipping encoder tests - encoder not available')
"
```

## PGN and SPN Analysis

### 5. Analyze PGN Coverage and Definitions
```bash
# Analyze PGN definitions and coverage
echo "Analyzing PGN coverage..."

poetry run python -c "
from backend.integrations.rvc.config_loader import load_rvc_config
import json

config = load_rvc_config()
pgns = config.get('pgns', {})

# Analyze PGN categories
categories = {}
pgn_ranges = {
    'System': (65280, 65535),  # 0xFF00-0xFFFF
    'Proprietary': (61440, 65279),  # 0xF000-0xFEFF
    'Standard': (0, 61439)  # 0x0000-0xEFFF
}

for pgn_id_str, pgn_data in pgns.items():
    try:
        pgn_id = int(pgn_id_str)
        pgn_name = pgn_data.get('name', 'Unknown')

        # Categorize PGN
        category = 'Unknown'
        for cat_name, (min_val, max_val) in pgn_ranges.items():
            if min_val <= pgn_id <= max_val:
                category = cat_name
                break

        if category not in categories:
            categories[category] = []
        categories[category].append((pgn_id, pgn_name))

    except (ValueError, TypeError):
        continue

print(f'PGN Analysis ({len(pgns)} total PGNs):')
print()

for category, pgn_list in sorted(categories.items()):
    print(f'{category} PGNs ({len(pgn_list)}):')

    # Show first few PGNs in each category
    for pgn_id, pgn_name in sorted(pgn_list)[:5]:
        print(f'  0x{pgn_id:04X} ({pgn_id:5d}): {pgn_name}')

    if len(pgn_list) > 5:
        print(f'  ... and {len(pgn_list) - 5} more {category.lower()} PGNs')
    print()

# Check for common RV-C PGNs
common_pgns = {
    0x1FED8: 'DC Dimmer Status',
    0x1FED9: 'DC Load Command',
    0x1FECA: 'AC Load Status',
    0x1FECB: 'AC Load Command',
    0x1FEF1: 'DateTime Status'
}

print('Common RV-C PGN Coverage:')
for pgn_id, expected_name in common_pgns.items():
    pgn_str = str(pgn_id)
    if pgn_str in pgns:
        actual_name = pgns[pgn_str].get('name', 'Unknown')
        print(f'✓ 0x{pgn_id:04X}: {actual_name}')
    else:
        print(f'✗ 0x{pgn_id:04X}: Missing ({expected_name})')
"
```

### 6. Validate SPN Definitions
```bash
# Analyze SPN (Suspect Parameter Number) definitions
echo "Analyzing SPN definitions..."

poetry run python -c "
from backend.integrations.rvc.config_loader import load_rvc_config

config = load_rvc_config()
spns = config.get('spns', {})

if spns:
    print(f'SPN Analysis ({len(spns)} total SPNs):')
    print()

    # Group SPNs by type/category
    spn_types = {}

    for spn_id_str, spn_data in spns.items():
        try:
            spn_id = int(spn_id_str)
            spn_name = spn_data.get('name', 'Unknown')
            data_type = spn_data.get('type', 'unknown')

            if data_type not in spn_types:
                spn_types[data_type] = []
            spn_types[data_type].append((spn_id, spn_name))

        except (ValueError, TypeError):
            continue

    for data_type, spn_list in sorted(spn_types.items()):
        print(f'{data_type.title()} SPNs ({len(spn_list)}):')

        for spn_id, spn_name in sorted(spn_list)[:3]:
            print(f'  SPN {spn_id}: {spn_name}')

        if len(spn_list) > 3:
            print(f'  ... and {len(spn_list) - 3} more {data_type} SPNs')
        print()

else:
    print('ℹ No SPN definitions found in configuration')
"
```

## Real-time RV-C Monitoring

### 7. Monitor Live RV-C Messages
```bash
# Set up real-time RV-C message monitoring
echo "Setting up RV-C message monitoring..."

# Start backend with RV-C enabled
COACHIQ_FEATURES__ENABLE_RVC=true COACHIQ_CAN__INTERFACES=vcan0,vcan1 poetry run python run_server.py --debug &
BACKEND_PID=$!

# Wait for startup
sleep 5

# Monitor RV-C messages in background
echo "Starting RV-C message monitoring..."

poetry run python -c "
import asyncio
import signal
import sys
from backend.services.feature_manager import FeatureManager
from backend.core.config import get_settings

class RVCMonitor:
    def __init__(self):
        self.running = True
        self.message_count = 0

    def signal_handler(self, signum, frame):
        print(f'\\nStopping RV-C monitor... (processed {self.message_count} messages)')
        self.running = False

    async def monitor_messages(self):
        settings = get_settings()
        feature_manager = FeatureManager()
        await feature_manager.startup()

        if not feature_manager.is_enabled('rvc'):
            print('✗ RV-C feature not enabled')
            return

        print('✓ RV-C monitoring started (Ctrl+C to stop)')
        print('Waiting for RV-C messages...')
        print()

        # This is a simplified monitor - in real implementation,
        # you would hook into the CAN message processing pipeline
        try:
            while self.running:
                await asyncio.sleep(1)
                # In real implementation, process actual CAN messages here

        except KeyboardInterrupt:
            pass
        finally:
            await feature_manager.shutdown()

monitor = RVCMonitor()
signal.signal(signal.SIGINT, monitor.signal_handler)
asyncio.run(monitor.monitor_messages())
" &
MONITOR_PID=$!

# Send test RV-C messages
echo "Sending test RV-C messages..."
sleep 2

# Send sample messages to trigger RV-C processing
cansend vcan0 1FED8023#FF0A0000FFFF0000  # DC Dimmer Status
sleep 1
cansend vcan0 1FED9023#010000FFFFFFFFFF  # DC Load Command
sleep 1
cansend vcan0 1FECA023#FF00FFFFFFFFFFFF  # AC Load Status
sleep 1

# Let monitor run for a few seconds
sleep 3

# Cleanup
kill $MONITOR_PID 2>/dev/null || true
kill $BACKEND_PID 2>/dev/null || true

echo "✓ RV-C monitoring test complete"
```

### 8. Test Entity State Updates from RV-C
```bash
# Test that RV-C messages properly update entity states
echo "Testing RV-C to entity state updates..."

COACHIQ_FEATURES__ENABLE_RVC=true COACHIQ_CAN__INTERFACES=vcan0 poetry run python -c "
import asyncio
import subprocess
import time
from backend.services.feature_manager import FeatureManager

async def test_entity_updates():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    # Get entity manager
    entity_feature = feature_manager.get_feature('entity_manager')
    entity_manager = entity_feature.get_entity_manager()

    print('Initial entity state:')
    initial_entities = entity_manager.get_all_entities()
    print(f'Entities before RV-C messages: {len(initial_entities)}')

    # Send RV-C messages that should create/update entities
    test_messages = [
        '1FED8023#FF0A0000FFFF0000',  # DC Dimmer Status - should create light entity
        '1FED9023#010000FFFFFFFFFF',  # DC Load Command - should create switch entity
        '1FECA023#FF00FFFFFFFFFFFF',  # AC Load Status - should create AC load entity
    ]

    print()
    print('Sending RV-C messages to trigger entity updates...')

    for i, message in enumerate(test_messages):
        print(f'Sending message {i+1}: {message}')
        subprocess.run(['cansend', 'vcan0', message])

        # Wait for message processing
        await asyncio.sleep(0.5)

        # Check entity state
        current_entities = entity_manager.get_all_entities()
        print(f'  Entities after message {i+1}: {len(current_entities)}')

    # Final entity state
    print()
    print('Final entity state:')
    final_entities = entity_manager.get_all_entities()

    if len(final_entities) > len(initial_entities):
        print(f'✓ Entity creation successful: {len(final_entities) - len(initial_entities)} new entities')

        # Show new entities
        for entity_id, entity in final_entities.items():
            if entity_id not in initial_entities:
                print(f'  New entity: {entity_id} - {entity.state}')
    else:
        print('ℹ No new entities created (may indicate decoding issues)')

    await feature_manager.shutdown()

asyncio.run(test_entity_updates())
"
```

## RV-C Protocol Debugging

### 9. Debug RV-C Message Processing Pipeline
```bash
# Debug the complete RV-C message processing pipeline
echo "Debugging RV-C message processing pipeline..."

poetry run python -c "
import asyncio
from backend.integrations.rvc.decode import decode_rvc_message
from backend.integrations.rvc.config_loader import load_rvc_config
from backend.services.can_service import CANService
from backend.core.config import get_settings

async def debug_rvc_pipeline():
    # Load RV-C configuration
    print('Step 1: Loading RV-C configuration...')
    config = load_rvc_config()

    if not config:
        print('✗ Failed to load RV-C configuration')
        return

    pgns = config.get('pgns', {})
    print(f'✓ Loaded {len(pgns)} PGN definitions')

    # Test message parsing
    print()
    print('Step 2: Testing message parsing...')

    test_can_id = 0x1FED8023  # DC Dimmer Status with source address 0x23
    test_data = bytes.fromhex('FF0A0000FFFF0000')

    # Extract PGN from CAN ID (RV-C uses J1939 addressing)
    pgn = (test_can_id >> 8) & 0x3FFFF  # Extract PGN bits
    source_address = test_can_id & 0xFF

    print(f'CAN ID: 0x{test_can_id:08X}')
    print(f'Extracted PGN: 0x{pgn:04X} ({pgn})')
    print(f'Source Address: 0x{source_address:02X}')
    print(f'Data: {test_data.hex().upper()}')

    # Test decoding
    print()
    print('Step 3: Testing RV-C decoding...')

    try:
        decoded = decode_rvc_message(pgn, test_data, config)

        if decoded:
            print(f'✓ Decoding successful: {decoded}')
        else:
            print('⚠ Decoding returned no result')

            # Check if PGN is defined
            pgn_str = str(pgn)
            if pgn_str in pgns:
                pgn_def = pgns[pgn_str]
                print(f'  PGN {pgn} is defined: {pgn_def.get(\"name\", \"Unknown\")}')
            else:
                print(f'  PGN {pgn} not found in configuration')

    except Exception as e:
        print(f'✗ Decoding error: {e}')

    print()
    print('Step 4: Testing CAN service integration...')

    # Test CAN service (if available)
    try:
        settings = get_settings()
        can_service = CANService(settings.can)

        print('✓ CAN service created successfully')

        # Check if interfaces are available
        interfaces = settings.can.interfaces
        print(f'✓ Configured interfaces: {interfaces}')

    except Exception as e:
        print(f'⚠ CAN service error: {e}')

asyncio.run(debug_rvc_pipeline())
"
```

### 10. Performance and Validation Summary
```bash
echo "=== RV-C Debug Summary ==="

# Check feature status
echo "Feature Status:"
poetry run python -c "
import asyncio
from backend.services.feature_manager import FeatureManager

async def check_status():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    features_to_check = ['rvc', 'can_interface', 'entity_manager']

    for feature_name in features_to_check:
        if feature_manager.is_enabled(feature_name):
            feature = feature_manager.get_feature(feature_name)
            print(f'✓ {feature_name}: enabled, health={feature.health}')
        else:
            print(f'✗ {feature_name}: disabled')

    await feature_manager.shutdown()

asyncio.run(check_status())
"

# Check configuration files
echo "Configuration Files:"
[ -f "config/rvc.json" ] && echo "✓ RV-C specification found" || echo "✗ RV-C specification missing"
[ -f "config/coach_mapping.default.yml" ] && echo "✓ Coach mapping found" || echo "✗ Coach mapping missing"

# Check for development tools
echo "Development Tools:"
[ -f "dev_tools/validate_rvc_json.py" ] && echo "✓ RV-C validator available" || echo "✗ RV-C validator missing"
[ -f "backend/integrations/rvc/decode.py" ] && echo "✓ RV-C decoder available" || echo "✗ RV-C decoder missing"
[ -f "backend/integrations/rvc/encoder.py" ] && echo "✓ RV-C encoder available" || echo "✗ RV-C encoder missing"

echo "=== RV-C Debugging Complete ==="
echo "Use this command with specific arguments to focus on particular debugging areas"
```

## Arguments

$ARGUMENTS can specify:
- `--decode-only` - Only test message decoding functionality
- `--encode-only` - Only test message encoding functionality
- `--monitor` - Set up real-time message monitoring
- `--performance` - Run performance benchmarks for RV-C processing
- `--validate-config` - Only validate RV-C configuration files
- `--entity-test` - Focus on entity state update testing
- `pgn <number>` - Debug specific PGN (e.g., `pgn 65240`)
- `message <hex>` - Debug specific message data

## Development Notes

### RV-C Protocol Information
- Based on J1939 CAN standard with RV-specific adaptations
- Uses Parameter Group Numbers (PGNs) to identify message types
- Suspect Parameter Numbers (SPNs) define data field meanings
- Source addressing for device identification

### Common RV-C PGNs
- **65240 (0x1FED8)**: DC Dimmer Status
- **65241 (0x1FED9)**: DC Load Command
- **65202 (0x1FECA)**: AC Load Status
- **65203 (0x1FECB)**: AC Load Command
- **65265 (0x1FEF1)**: DateTime Status

### Troubleshooting
- If decoding fails, check PGN definitions in `config/rvc.json`
- For encoding issues, verify encoder implementation exists
- If entities aren't created, check entity manager integration
- For CAN issues, ensure virtual CAN interfaces are set up

This command provides comprehensive RV-C protocol debugging capabilities for development and troubleshooting of the CoachIQ RV-C integration.
