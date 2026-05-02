from abc import ABCMeta, abstractmethod

from typing import Optional

from pylabrobot.machines.backend import MachineBackend
from pylabrobot.resources import Plate


class MagnetModuleBackend(MachineBackend, metaclass=ABCMeta):
    '''Abstract class on which to base all MagnetModules (usually used for separation such as SPRI)'''

    @abstractmethod
    async def setup(self) -> None:
        '''Sets up the magnet module, should be called before any other method'''

    @abstractmethod
    async def engage(self, height: float) -> None:
        '''engage the magnetic component from the local plate, will set the height of the magnetic module to the known height of the specific plate
        if the plate has a given height, otherwise it will raise to the default value of _______. Raises ValueError when there is no plate.'''
        # TODO

    @abstractmethod
    async def disengage(self) -> None:
        '''disengage the magnetic component from the local plate'''

    @abstractmethod
    async def stop(self) -> None:
        '''Closes all connection to the magnetic module, setup may be run again'''

    @abstractmethod
    async def get_state(self) -> dict:
        '''returns the boolean state of the magnet module, True corresponds to engaged.'''

    @abstractmethod
    async def assign_child(self, plate: Optional[Plate]):
        '''assigns a child plate to the magnet module'''

    @abstractmethod
    async def unassign_child(self):
        '''unassigns child plate from the Magnet Module, if no plate, raises a ValueError'''

    @abstractmethod
    async def get_child(self) -> Optional[Plate]:
        '''Returns a Plate object or None if there is no Plate on the Magnetic Module.'''
