from pylabrobot.magnetic_modules.magnet_module import MagnetModule
from pylabrobot.magnetic_modules.opentrons_backend import OTMagnetModuleBackend
from pylabrobot.resources.coordinate import Coordinate


def opentronsMagnetModule(name: str) -> MagnetModule:
    return MagnetModule(
        backend=OTMagnetModuleBackend(slot=1),
        name=name,
        size_x=134,     # measured by hand (mm)
        size_z=98.5,    # measured by hand (mm)
        size_y=90,      # measured by hand (mm)
        child_location=Coordinate(x=-1.2, y=0, z=82)    # measured by hand (mm)
    )
