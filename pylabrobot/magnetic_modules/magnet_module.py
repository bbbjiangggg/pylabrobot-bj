from pylabrobot.magnetic_modules import MagnetModuleBackend
from pylabrobot.machines.machine import Machine, need_setup_finished
from pylabrobot.resources import Coordinate, ResourceHolder, Resource, Plate
from pylabrobot.resources.opentrons import OTModule
from typing import Optional, cast

import asyncio


class MagnetModule(ResourceHolder, Machine, OTModule):
    def __init__(
            self,
            name: str,
            backend: MagnetModuleBackend,
            size_x: float,
            size_y: float,
            size_z: float,
            child_location: Coordinate,
            model: Optional[str] = None,
            category: Optional[str] = None,
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
        self.backend: MagnetModuleBackend = backend

    @need_setup_finished
    async def engage(self, height):
        await self.backend.engage(height=height)

    @need_setup_finished
    async def disengage(self):
        await self.backend.disengage()

    def assign_child(self,
                     resource: Resource,
                     location: Optional[Coordinate] = None,
                     reassign: bool = True,
                     ):
        if len(self.children) >= 1:
            raise ValueError("There already is a plate in the plate reader.")
        if not isinstance(resource, Plate):
            raise ValueError("The resource must be a Plate.")

        super().assign_child_resource(resource, location=location, reassign=reassign)

    @property
    def child(self) -> Optional[Plate]:
        """Return the plate on the magnetic module, or None if empty.
        Required by OpentronsBackend.assigned_resource_callback."""
        if len(self.children) == 0:
            return None
        return cast(Plate, self.children[0])

    def get_plate(self) -> Plate:
        if len(self.children) == 0:
            raise ValueError("There is no plate in the plate reader.")
        return cast(Plate, self.children[0])
