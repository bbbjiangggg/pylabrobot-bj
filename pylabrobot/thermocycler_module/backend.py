from abc import ABCMeta, abstractmethod
from typing import Optional, List, Dict

from pylabrobot.machines.backend import MachineBackend
from pylabrobot.resources import Plate


class ThermocyclerBackend(MachineBackend, metaclass=ABCMeta):
    """Abstract class on which to base all Thermocycler backends"""

    @abstractmethod
    async def setup(self) -> None:
        """Sets up the thermocycler, should be called before any other method"""

    @abstractmethod
    async def stop(self) -> None:
        """Closes all connections to the thermocycler, setup may be run again"""

    # ========================================================================
    # LID CONTROL
    # ========================================================================

    @abstractmethod
    async def open_lid(self) -> None:
        """Open the thermocycler lid"""

    @abstractmethod
    async def close_lid(self) -> None:
        """Close the thermocycler lid"""

    @abstractmethod
    async def set_lid_temperature(self, temperature: float) -> None:
        """
        Set the lid temperature in Celsius.

        Args:
            temperature: Target lid temperature in Celsius
        """

    @abstractmethod
    async def deactivate_lid(self) -> None:
        """Deactivate the lid heater"""

    @abstractmethod
    async def get_lid_temperature(self) -> float:
        """
        Get the current lid temperature.

        Returns:
            Current lid temperature in Celsius
        """

    @abstractmethod
    async def get_lid_state(self) -> str:
        """
        Get the current lid state.

        Returns:
            Lid state: 'open', 'closed', 'in_between', or 'unknown'
        """

    # ========================================================================
    # BLOCK CONTROL
    # ========================================================================

    @abstractmethod
    async def set_block_temperature(
        self,
        temperature: float,
        hold_time_seconds: Optional[float] = None,
        volume: Optional[float] = None,
        ramp_rate: Optional[float] = None
    ) -> None:
        """
        Set the block temperature in Celsius.

        Args:
            temperature: Target block temperature in Celsius (4-99°C)
            hold_time_seconds: Optional hold time at target temperature
            volume: Optional sample volume in µL for thermal calculations
            ramp_rate: Optional ramp rate in °C/s (max 4.25°C/s)
        """

    @abstractmethod
    async def deactivate_block(self) -> None:
        """Deactivate the block heater/cooler"""

    @abstractmethod
    async def get_block_temperature(self) -> float:
        """
        Get the current block temperature.

        Returns:
            Current block temperature in Celsius
        """

    @abstractmethod
    async def wait_for_block_temp(self) -> None:
        """Wait for the block to reach its target temperature"""

    @abstractmethod
    async def wait_for_lid_temp(self) -> None:
        """Wait for the lid to reach its target temperature"""

    # ========================================================================
    # PROFILE EXECUTION
    # ========================================================================

    @abstractmethod
    async def execute_profile(
        self,
        steps: List[Dict[str, float]],
        repetitions: int = 1,
        volume: Optional[float] = None
    ) -> None:
        """
        Execute a temperature profile (e.g., for PCR).

        Args:
            steps: List of temperature steps, each with 'temperature' and 'hold_time_seconds'
                   Example: [{'temperature': 95, 'hold_time_seconds': 30},
                            {'temperature': 60, 'hold_time_seconds': 30}]
            repetitions: Number of times to repeat the profile
            volume: Optional sample volume in µL for thermal calculations
        """

    # ========================================================================
    # STATUS & DEACTIVATION
    # ========================================================================

    @abstractmethod
    async def get_state(self) -> dict:
        """
        Returns the current state of the thermocycler.

        Returns:
            Dictionary with block temp, lid temp, lid state, and target temps
        """

    @abstractmethod
    async def deactivate(self) -> None:
        """Deactivate both block and lid heaters"""

    @abstractmethod
    async def assign_child(self, plate: Optional[Plate]):
        """Assigns a child plate to the thermocycler"""

    @abstractmethod
    async def unassign_child(self):
        """Unassigns child plate from the thermocycler"""

    @abstractmethod
    async def get_child(self) -> Optional[Plate]:
        """Returns a Plate object or None if there is no Plate on the thermocycler"""
