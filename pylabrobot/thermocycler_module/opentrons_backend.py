from typing import Optional, List, Dict
import sys

from .backend import ThermocyclerBackend
from pylabrobot.resources.opentrons.module import OTModule

# Import ot_api regardless of Python version
try:
    import ot_api
    USE_OT = True
except ImportError:
    USE_OT = False


class OTThermocyclerBackend(ThermocyclerBackend, OTModule):
    """Opentrons Thermocycler Module Backend"""

    def __init__(self, host: str, slot: int = 7) -> None:
        """
        Initialize the thermocycler module backend.

        Args:
            host: IP address of the Opentrons robot (e.g., "10.146.93.225")
            slot: Deck slot where the thermocycler is installed (typically slot 7)
                  Note: Thermocycler spans multiple slots (7, 8, 10, 11)
        """
        assert 1 <= slot <= 11
        self.host = host
        self.slot = slot
        self._run_id = None
        self._mod_id = None
        self._module_model = None
        self._connected_mods = None
        self.opentrons_id = None  # Required by OpentronsBackend when assigning to deck

    def discover_module(self) -> None:
        """
        Discover the thermocycler module before setup. Call this before assigning to deck.
        Sets opentrons_id so the OpentronsBackend callback works properly.
        """
        if not USE_OT:
            raise ImportError("ot_api package is required. Install with: pip install ot-api")

        # Configure ot_api with the robot host
        ot_api.set_host(self.host)

        self._connected_mods = ot_api.modules.list_connected_modules()
        print(f"Connected modules: {[m.get('moduleModel', 'unknown') for m in self._connected_mods]}")

        for mod in self._connected_mods:
            try:
                module_model = mod.get('moduleModel', '')
                # Support both V1 and V2 thermocycler modules
                if 'thermocycler' in module_model.lower() and 'Module' in module_model:
                    self._mod_id = mod['id']
                    self._module_model = module_model
                    self.opentrons_id = mod['id']
                    print(f"Found thermocycler module: {module_model} (ID: {self._mod_id})")
                    return
            except KeyError:
                pass

        raise ValueError(
            'Thermocycler not found in connected devices. '
            f'Connected modules: {[m.get("moduleModel", "unknown") for m in self._connected_mods]}. '
            'Ensure the thermocycler is plugged into the robot USB ports and powered on.')

    async def setup(self) -> None:
        """Initialize API and load the thermocycler module."""
        if not USE_OT:
            raise ImportError("ot_api package is required. Install with: pip install ot-api")

        # Configure ot_api with the robot host
        ot_api.set_host(self.host)

        # If not already discovered, do it now
        if self._mod_id is None:
            self.discover_module()

        # Get run ID
        self._run_id = ot_api.runs.get_all()[-1]['id']

        # Load the module (may already be loaded by OpentronsBackend callback)
        try:
            ot_api.modules.load_module(
                slot=self.slot,
                model=self._module_model,
                module_id=self._mod_id
            )
        except Exception as e:
            # Module might already be loaded by OpentronsBackend callback - that's OK
            if "already loaded" not in str(e).lower():
                print(f"Note: load_module returned: {e}")

    # ========================================================================
    # LID CONTROL
    # ========================================================================

    async def open_lid(self) -> None:
        """Open the thermocycler lid"""
        self._ensure_ready()
        # Use enqueue_command directly to avoid blocking/timeout issues
        ot_api.runs.enqueue_command(
            "thermocycler/openLid",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def close_lid(self) -> None:
        """Close the thermocycler lid"""
        self._ensure_ready()
        # Use enqueue_command directly to avoid blocking/timeout issues
        ot_api.runs.enqueue_command(
            "thermocycler/closeLid",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def set_lid_temperature(self, temperature: float) -> None:
        """
        Set the lid temperature in Celsius.

        Args:
            temperature: Target lid temperature in Celsius (typically 105°C for PCR)
        """
        self._ensure_ready()
        ot_api.runs.enqueue_command(
            "thermocycler/setTargetLidTemperature",
            {"celsius": temperature, "moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def deactivate_lid(self) -> None:
        """Deactivate the lid heater"""
        self._ensure_ready()
        ot_api.runs.enqueue_command(
            "thermocycler/deactivateLid",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def get_lid_temperature(self) -> float:
        """Get the current lid temperature"""
        self._ensure_ready()
        state = await self.get_state()
        return state.get('lidTemperature', 0.0)

    async def get_lid_state(self) -> str:
        """
        Get the current lid state.

        Returns:
            Lid state: 'open', 'closed', 'in_between', or 'unknown'
        """
        self._ensure_ready()
        state = await self.get_state()
        return state.get('lidStatus', 'unknown')

    # ========================================================================
    # BLOCK CONTROL
    # ========================================================================

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
        self._ensure_ready()

        params = {"celsius": temperature, "moduleId": self._mod_id}

        if hold_time_seconds is not None:
            params["holdTimeSeconds"] = hold_time_seconds
        if volume is not None:
            params["volume"] = volume

        # Use enqueue_command directly
        ot_api.runs.enqueue_command(
            "thermocycler/setTargetBlockTemperature",
            params,
            intent="setup",
            run_id=self._run_id
        )

    async def deactivate_block(self) -> None:
        """Deactivate the block heater/cooler"""
        self._ensure_ready()
        ot_api.runs.enqueue_command(
            "thermocycler/deactivateBlock",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def get_block_temperature(self) -> float:
        """Get the current block temperature"""
        self._ensure_ready()
        state = await self.get_state()
        return state.get('currentTemperature', 0.0)

    async def wait_for_block_temp(self) -> None:
        """Wait for the block to reach its target temperature"""
        self._ensure_ready()
        ot_api.runs.enqueue_command(
            "thermocycler/waitForBlockTemperature",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    async def wait_for_lid_temp(self) -> None:
        """Wait for the lid to reach its target temperature"""
        self._ensure_ready()
        ot_api.runs.enqueue_command(
            "thermocycler/waitForLidTemperature",
            {"moduleId": self._mod_id},
            intent="setup",
            run_id=self._run_id
        )

    # ========================================================================
    # PROFILE EXECUTION
    # ========================================================================

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
            repetitions: Number of times to repeat the profile
            volume: Optional sample volume in µL for thermal calculations
        """
        self._ensure_ready()

        # Convert steps to Opentrons API format
        profile_steps = []
        for step in steps:
            profile_step = {
                "celsius": step['temperature'],
                "holdSeconds": step['hold_time_seconds']
            }
            profile_steps.append(profile_step)

        params = {
            "moduleId": self._mod_id,
            "profile": profile_steps,
            "blockMaxVolumeUl": volume if volume is not None else 50  # Default 50µL
        }

        # Execute profile for the specified number of repetitions
        for rep in range(repetitions):
            ot_api.runs.enqueue_command(
                "thermocycler/runProfile",
                params,
                intent="setup",
                run_id=self._run_id
            )

    # ========================================================================
    # STATUS & DEACTIVATION
    # ========================================================================

    async def get_state(self) -> dict:
        """
        Return current module status.

        Returns:
            Dictionary with current/target temperatures and lid status
        """
        self._ensure_ready()

        # Refresh module list to get current state (not cached)
        current_mods = ot_api.modules.list_connected_modules()

        for mod in current_mods:
            try:
                if mod.get('id') == self._mod_id:
                    return mod.get('data', {})
            except KeyError:
                pass
        return {}

    async def deactivate(self) -> None:
        """Deactivate both block and lid heaters"""
        await self.deactivate_block()
        await self.deactivate_lid()

    async def stop(self):
        """Close connection"""
        pass  # Nothing to clean up

    # ========================================================================
    # PLATE MANAGEMENT (Not Yet Implemented)
    # ========================================================================

    async def assign_child(self, plate):
        raise NotImplementedError('feature has not yet been implemented')

    async def get_child(self):
        raise NotImplementedError('feature has not yet been implemented')

    async def unassign_child(self):
        raise NotImplementedError('feature has not yet been implemented')

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _ensure_ready(self) -> None:
        """Ensure module is initialized"""
        if self._mod_id is None:
            raise RuntimeError("Module not initialized. Call `setup()` first.")
