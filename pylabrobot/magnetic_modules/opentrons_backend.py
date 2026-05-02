from typing import Optional
import sys
import asyncio
from typing import Union, List

from .backend import MagnetModuleBackend
from pylabrobot.resources.opentrons.module import OTModule

# Import ot_api regardless of Python version
try:
    import ot_api
    USE_OT = True
except ImportError:
    USE_OT = False


class OTMagnetModuleBackend(MagnetModuleBackend, OTModule):
    def __init__(self, host: str, slot: int = 1) -> None:
        """
        Initialize the magnetic module backend.

        Args:
            host: IP address of the Opentrons robot (e.g., "10.146.93.225")
            slot: Deck slot where the magnetic module is installed (1-11)
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
        Discover the magnetic module before setup. Call this before assigning to deck.
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
                # Support both V1 and V2 magnetic modules
                if 'magnetic' in module_model.lower() and 'Module' in module_model:
                    self._mod_id = mod['id']
                    self._module_model = module_model
                    self.opentrons_id = mod['id']
                    print(f"Found magnetic module: {module_model} (ID: {self._mod_id})")
                    return
            except KeyError:
                pass

        raise ValueError(
            'MagnetModule not found in connected devices. '
            f'Connected modules: {[m.get("moduleModel", "unknown") for m in self._connected_mods]}. '
            'Ensure the magnetic module is plugged into the robot USB ports and powered on.')

    async def setup(self) -> None:
        """Initialize API and load the magnetic module."""
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

    async def engage(self, height: float = 10.0) -> None:
        """Raise magnet to specified height."""
        self._ensure_ready()
        ot_api.runs.enqueue_command("magneticModule/engage",
                                    {'height': height, "moduleId": self._mod_id}, intent="setup", run_id=self._run_id)

    async def disengage(self) -> None:
        """Lower the magnet."""
        self._ensure_ready()
        ot_api.runs.enqueue_command("magneticModule/disengage",
                                    {"moduleId": self._mod_id}, intent="setup", run_id=self._run_id)

    async def get_state(self) -> dict:
        """Return current module status."""
        self._ensure_ready()
        for mod in self._connected_mods:
            try:
                if mod.get('id') == self._mod_id:
                    return mod.get('data', {})
            except KeyError:
                pass
        return {}

    def _ensure_ready(self) -> None:
        if self._mod_id is None:
            raise RuntimeError("Module not initialized. Call `setup()` first.")

    async def assign_child(self, plate):
        raise NotImplementedError('feature has not yet been implemented')

    async def get_child(self):
        raise NotImplementedError('feature has not yet been implemented')

    async def stop(self):
        pass  # Nothing to clean up

    async def unassign_child(self):
        raise NotImplementedError('feature has not yet been implemented')
