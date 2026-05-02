from pylabrobot.thermocycler_module.thermocycler import Thermocycler
from pylabrobot.thermocycler_module.opentrons_backend import OTThermocyclerBackend
from pylabrobot.resources.coordinate import Coordinate


def opentrons_thermocycler(name: str, host: str, slot: int = 7, labware_z_offset: float = 15) -> Thermocycler:
    """
    Factory function to create an Opentrons Thermocycler Module.

    Physical dimensions based on Opentrons Thermocycler Module V1 specs:
    - Accommodates full-skirted 96-well, 0.2 mL PCR plates
    - Block temperature range: 4-99°C
    - Max heating ramp rate: 4.25°C/s (between ambient and 95°C)
    - Lid temperature control available

    Args:
        name: Name for the thermocycler instance
        host: IP address of the Opentrons robot (e.g., "10.146.93.225")
        slot: Deck slot where thermocycler is installed (default 7)
              Note: Thermocycler spans slots 7, 8, 10, 11 on OT-2
        labware_z_offset: Z-axis offset for labware on thermocycler in mm (default 15)
                         Adjust this if tips hit the thermocycler or are too high
                         Positive values raise the plate, negative values lower it

    Returns:
        Thermocycler instance ready to be assigned to deck

    Example:
        >>> from pylabrobot.thermocycler_module import opentrons_thermocycler
        >>> tc = opentrons_thermocycler("my_tc", host="10.146.93.225", slot=7)
        >>> tc_backend = tc.backend
        >>> tc_backend.discover_module()  # Discover before deck assignment
        >>> lh.deck.assign_child_at_slot(tc, slot=7)
        >>> await tc.setup()
        >>> await tc.close_lid()
        >>> await tc.set_block_temperature(95)
    """
    return Thermocycler(
        backend=OTThermocyclerBackend(host=host, slot=slot),
        name=name,
        size_x=172,         # Width in mm (from tech specs)
        size_y=244.95,      # Length in mm (from tech specs)
        size_z=180,         # Height in mm (slightly increased for clearance)
        child_location=Coordinate(x=0, y=0, z=110),  # Plate surface height above TC base
        labware_z_offset=labware_z_offset  # Z offset to correct Opentrons API height
    )
