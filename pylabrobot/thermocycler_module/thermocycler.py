from pylabrobot.thermocycler_module import ThermocyclerBackend
from pylabrobot.machines.machine import Machine, need_setup_finished
from pylabrobot.resources import Coordinate, ResourceHolder, Resource, Plate
from pylabrobot.resources.opentrons import OTModule
from typing import Optional, cast, List, Dict

import asyncio


class Thermocycler(ResourceHolder, Machine, OTModule):
    """
    Thermocycler module for temperature cycling operations (e.g., PCR).

    Features:
    - Dual temperature control (block + lid)
    - Lid automation (open/close)
    - Temperature profile execution with repetitions
    - Hold times and ramp rate control
    """

    def __init__(
            self,
            name: str,
            backend: ThermocyclerBackend,
            size_x: float,
            size_y: float,
            size_z: float,
            child_location: Coordinate,
            model: Optional[str] = None,
            category: Optional[str] = None,
            labware_z_offset: float = 0,
    ) -> None:
        ResourceHolder.__init__(
            self,
            name=name,
            size_x=size_x,
            size_y=size_y,
            size_z=size_z,
            category=category,
            model=model,
            child_location=child_location,
        )
        Machine.__init__(self, backend=backend)
        self.backend: ThermocyclerBackend = backend
        self.labware_z_offset = labware_z_offset

    # ========================================================================
    # LID CONTROL
    # ========================================================================

    @need_setup_finished
    async def open_lid(self):
        """Open the thermocycler lid"""
        await self.backend.open_lid()

    @need_setup_finished
    async def close_lid(self):
        """Close the thermocycler lid"""
        await self.backend.close_lid()

    @need_setup_finished
    async def set_lid_temperature(self, temperature: float):
        """
        Set the lid temperature in Celsius.

        Args:
            temperature: Target lid temperature in Celsius (typically 105°C for PCR)
        """
        await self.backend.set_lid_temperature(temperature)

    @need_setup_finished
    async def deactivate_lid(self):
        """Deactivate the lid heater"""
        await self.backend.deactivate_lid()

    @need_setup_finished
    async def get_lid_temperature(self) -> float:
        """
        Get the current lid temperature.

        Returns:
            Current lid temperature in Celsius
        """
        return await self.backend.get_lid_temperature()

    @need_setup_finished
    async def get_lid_state(self) -> str:
        """
        Get the current lid state.

        Returns:
            Lid state: 'open', 'closed', 'in_between', or 'unknown'
        """
        return await self.backend.get_lid_state()

    # ========================================================================
    # BLOCK CONTROL
    # ========================================================================

    @need_setup_finished
    async def set_block_temperature(
        self,
        temperature: float,
        hold_time_seconds: Optional[float] = None,
        volume: Optional[float] = None,
        ramp_rate: Optional[float] = None
    ):
        """
        Set the block temperature in Celsius.

        Args:
            temperature: Target block temperature in Celsius (4-99°C)
            hold_time_seconds: Optional hold time at target temperature
            volume: Optional sample volume in µL for thermal calculations
            ramp_rate: Optional ramp rate in °C/s (max 4.25°C/s)
        """
        await self.backend.set_block_temperature(
            temperature=temperature,
            hold_time_seconds=hold_time_seconds,
            volume=volume,
            ramp_rate=ramp_rate
        )

    @need_setup_finished
    async def deactivate_block(self):
        """Deactivate the block heater/cooler"""
        await self.backend.deactivate_block()

    @need_setup_finished
    async def get_block_temperature(self) -> float:
        """
        Get the current block temperature.

        Returns:
            Current block temperature in Celsius
        """
        return await self.backend.get_block_temperature()

    @need_setup_finished
    async def wait_for_block_temp(self):
        """Wait for the block to reach its target temperature"""
        await self.backend.wait_for_block_temp()

    @need_setup_finished
    async def wait_for_lid_temp(self):
        """Wait for the lid to reach its target temperature"""
        await self.backend.wait_for_lid_temp()

    # ========================================================================
    # PROFILE EXECUTION
    # ========================================================================

    @need_setup_finished
    async def execute_profile(
        self,
        steps: List[Dict[str, float]],
        repetitions: int = 1,
        volume: Optional[float] = None
    ):
        """
        Execute a temperature profile (e.g., for PCR).

        Args:
            steps: List of temperature steps, each with 'temperature' and 'hold_time_seconds'
                   Example: [{'temperature': 95, 'hold_time_seconds': 30},
                            {'temperature': 60, 'hold_time_seconds': 30},
                            {'temperature': 72, 'hold_time_seconds': 60}]
            repetitions: Number of times to repeat the profile (default 1)
            volume: Optional sample volume in µL for thermal calculations

        Example:
            # PCR profile: 30 cycles of 95°C (30s), 60°C (30s), 72°C (60s)
            await tc.execute_profile(
                steps=[
                    {'temperature': 95, 'hold_time_seconds': 30},
                    {'temperature': 60, 'hold_time_seconds': 30},
                    {'temperature': 72, 'hold_time_seconds': 60}
                ],
                repetitions=30,
                volume=50
            )
        """
        await self.backend.execute_profile(
            steps=steps,
            repetitions=repetitions,
            volume=volume
        )

    # ========================================================================
    # STATUS & DEACTIVATION
    # ========================================================================

    @need_setup_finished
    async def get_state(self) -> dict:
        """
        Returns the current state of the thermocycler.

        Returns:
            Dictionary with block temp, lid temp, lid state, and target temps
        """
        return await self.backend.get_state()

    @need_setup_finished
    async def deactivate(self):
        """Deactivate both block and lid heaters"""
        await self.backend.deactivate()

    # ========================================================================
    # PLATE MANAGEMENT
    # ========================================================================

    def assign_child(self,
                     resource: Resource,
                     location: Optional[Coordinate] = None,
                     reassign: bool = True,
                     ):
        """
        Assign a plate to the thermocycler.

        Args:
            resource: Plate to assign (must be a Plate instance)
            location: Optional location override
            reassign: Whether to allow reassignment
        """
        if len(self.children) >= 1:
            raise ValueError("There already is a plate in the thermocycler.")
        if not isinstance(resource, Plate):
            raise ValueError("The resource must be a Plate.")

        super().assign_child_resource(resource, location=location, reassign=reassign)

    @property
    def child(self) -> Optional[Plate]:
        """
        Return the plate on the thermocycler, or None if empty.
        Required by OpentronsBackend.assigned_resource_callback.
        """
        if len(self.children) == 0:
            return None
        return cast(Plate, self.children[0])

    def get_plate(self) -> Plate:
        """
        Get the plate on the thermocycler.

        Returns:
            The Plate instance

        Raises:
            ValueError: If no plate is assigned
        """
        if len(self.children) == 0:
            raise ValueError("There is no plate in the thermocycler.")
        return cast(Plate, self.children[0])
