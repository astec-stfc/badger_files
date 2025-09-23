from badger import environment
from badger.errors import (
    BadgerNoInterfaceError,
)
from interfaces.CATAP import CATAPInterface


class Environment(environment.Environment):
    name = "CATAPExample"

    variables = {
        "magnet:CLA-S07-MAG-QUAD-01:seti": [-10., 10.],
        "magnet:CLA-S07-MAG-QUAD-02:seti": [-10., 10.],
        "magnet:CLA-S07-MAG-QUAD-03:seti": [-10., 10.],
        "magnet:CLA-S07-MAG-QUAD-04:seti": [-10., 10.],
    }

    observables = [
        "charge:CLA-S01-DIA-WCM-01:q",
    ]

    _machine_areas = {
        "magnet": ['S07'],
        "charge": ['S01']
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the interface if not already set
        if not self.interface:
            self.interface = CATAPInterface(machine_areas=self._machine_areas)

    def get_observables(self, observable_names: list[str]) -> dict:
        if not self.interface:
            raise BadgerNoInterfaceError

        return self.interface.get_observables(observable_names)
