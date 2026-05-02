# Thermocycler Module - Usage Guide

## Overview

The `thermocycler_module` provides PyLabRobot integration for the Opentrons Thermocycler Module, enabling automated temperature cycling operations like PCR.

## Installation

Ensure you have the required dependencies:
```bash
pip install ot-api
```

## Quick Start

### Basic Setup

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.resources.opentrons import OTDeck
from pylabrobot.liquid_handling.backends.opentrons_backend import OpentronsBackend
from pylabrobot.thermocycler_module import opentrons_thermocycler

# Robot configuration
ROBOT_HOST = "10.146.93.225"
TC_SLOT = 7  # Thermocycler primary slot (spans 7, 8, 10, 11)

# Setup liquid handler
backend = OpentronsBackend(host=ROBOT_HOST)
lh = LiquidHandler(backend=backend, deck=OTDeck())
await lh.setup()

# Create thermocycler using factory function
tc = opentrons_thermocycler(name="my_thermocycler", host=ROBOT_HOST, slot=TC_SLOT)

# IMPORTANT: Discover module BEFORE assigning to deck
tc.backend.discover_module()

# Assign to deck
lh.deck.assign_child_at_slot(tc, slot=TC_SLOT)

# Setup the thermocycler
await tc.setup()
print("Thermocycler ready!")
```

## Usage Examples

### 1. Basic Temperature Control

```python
# Close the lid
await tc.close_lid()

# Set lid temperature (typically 105°C for PCR)
await tc.set_lid_temperature(105)
await tc.wait_for_lid_temp()

# Set block temperature
await tc.set_block_temperature(95, hold_time_seconds=30)
await tc.wait_for_block_temp()

# Hold at temperature for specific time
await tc.set_block_temperature(
    temperature=72,
    hold_time_seconds=120,  # Hold for 2 minutes
    volume=50  # 50µL sample volume
)
```

### 2. PCR Profile Execution

```python
# Close lid and set lid temperature
await tc.close_lid()
await tc.set_lid_temperature(105)

# Define PCR profile steps
pcr_steps = [
    {'temperature': 95, 'hold_time_seconds': 30},  # Denaturation
    {'temperature': 60, 'hold_time_seconds': 30},  # Annealing
    {'temperature': 72, 'hold_time_seconds': 60}   # Extension
]

# Execute 30 cycles of PCR
await tc.execute_profile(
    steps=pcr_steps,
    repetitions=30,
    volume=50  # 50µL sample volume
)

# Final extension
await tc.set_block_temperature(72, hold_time_seconds=300)  # 5 min

# Cool down
await tc.set_block_temperature(4)
```

### 3. Complete PCR Protocol

```python
# Initial denaturation
await tc.close_lid()
await tc.set_lid_temperature(105)
await tc.set_block_temperature(95, hold_time_seconds=180)  # 3 min
await tc.wait_for_block_temp()

# Cycling
pcr_steps = [
    {'temperature': 95, 'hold_time_seconds': 30},
    {'temperature': 60, 'hold_time_seconds': 30},
    {'temperature': 72, 'hold_time_seconds': 60}
]
await tc.execute_profile(steps=pcr_steps, repetitions=30, volume=50)

# Final extension
await tc.set_block_temperature(72, hold_time_seconds=600)  # 10 min
await tc.wait_for_block_temp()

# Hold at 4°C
await tc.set_block_temperature(4)

# Open lid when done
await tc.open_lid()
```

### 4. Lid Control

```python
# Open lid to access plate
await tc.open_lid()
print(f"Lid state: {await tc.get_lid_state()}")  # 'open'

# Close lid for thermal cycling
await tc.close_lid()
print(f"Lid state: {await tc.get_lid_state()}")  # 'closed'
```

### 5. Temperature Monitoring

```python
# Get current temperatures
block_temp = await tc.get_block_temperature()
lid_temp = await tc.get_lid_temperature()
print(f"Block: {block_temp}°C, Lid: {lid_temp}°C")

# Get full state
state = await tc.get_state()
print(state)  # Contains all module data
```

### 6. Deactivation

```python
# Deactivate just the block
await tc.deactivate_block()

# Deactivate just the lid
await tc.deactivate_lid()

# Deactivate both (recommended at end of protocol)
await tc.deactivate()
```

## Integration with Existing Protocols

You can use the thermocycler alongside other modules like the magnetic module:

```python
from pylabrobot.magnetic_modules import MagnetModule, OTMagnetModuleBackend
from pylabrobot.thermocycler_module import opentrons_thermocycler

# Setup both modules
magnet_backend = OTMagnetModuleBackend(host=ROBOT_HOST, slot=4)
magnet_backend.discover_module()
magnet_module = MagnetModule(...)

tc = opentrons_thermocycler(name="thermocycler", host=ROBOT_HOST, slot=7)
tc.backend.discover_module()

# Assign both to deck
lh.deck.assign_child_at_slot(magnet_module, slot=4)
lh.deck.assign_child_at_slot(tc, slot=7)

# Setup both
await magnet_module.setup()
await tc.setup()

# Use in protocol
# ... transfer samples to thermocycler plate
await tc.close_lid()
await tc.execute_profile(...)
# ... continue protocol
```

## API Reference

### Lid Control Methods
- `await tc.open_lid()` - Open the lid
- `await tc.close_lid()` - Close the lid
- `await tc.set_lid_temperature(celsius)` - Set lid temperature
- `await tc.deactivate_lid()` - Turn off lid heater
- `await tc.get_lid_temperature()` - Get current lid temp
- `await tc.get_lid_state()` - Get lid status ('open'/'closed')

### Block Control Methods
- `await tc.set_block_temperature(temp, hold_time_seconds=None, volume=None)` - Set block temp
- `await tc.deactivate_block()` - Turn off block heating/cooling
- `await tc.get_block_temperature()` - Get current block temp
- `await tc.wait_for_block_temp()` - Wait until block reaches target
- `await tc.wait_for_lid_temp()` - Wait until lid reaches target

### Profile Execution
- `await tc.execute_profile(steps, repetitions=1, volume=None)` - Run temp profile

### Status & Deactivation
- `await tc.get_state()` - Get full module state
- `await tc.deactivate()` - Deactivate both block and lid

## Technical Specifications

- **Dimensions**: 172mm (W) × 244.95mm (L) × 170.35mm (H, closed)
- **Deck Slots**: Spans slots 7, 8, 10, 11 (primary slot 7)
- **Block Temperature Range**: 4-99°C
- **Max Ramp Rate**: 4.25°C/s (between ambient and 95°C)
- **Plate Compatibility**: Full-skirted 96-well, 0.2 mL PCR plates
- **Lid Temperature Control**: Yes (typically set to 105°C for PCR)

## Troubleshooting

### Module Not Found
```python
# Make sure to discover before assigning to deck
tc.backend.discover_module()  # Must be called first!
lh.deck.assign_child_at_slot(tc, slot=7)
```

### Module Already Loaded Error
This is normal if the OpentronsBackend already loaded the module. The code handles this automatically.

### Temperature Not Reaching Target
- Ensure lid is closed for block heating
- Check that volume parameter matches your actual sample volume
- Allow sufficient time for temperature equilibration

## Notes

- Always close the lid before running temperature profiles
- Lid temperature is typically set to 105°C for PCR to prevent condensation
- The `volume` parameter helps optimize heating/cooling rates
- Use `await tc.wait_for_block_temp()` to ensure temperature is reached before proceeding
- Always call `await tc.deactivate()` at the end of your protocol to turn off heaters
