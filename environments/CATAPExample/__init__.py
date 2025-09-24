from copy import deepcopy
from badger import environment
from badger.errors import (
    BadgerNoInterfaceError,
)
from badger.formula import interpret_expression
from SimulationFramework.Modules.optimisation.constraints import constraintsClass
from interfaces.CATAP import Interface


class Environment(environment.Environment):
    name = "CATAPExample"

    variables = {
        # "magnet:CLA-S02-MAG-QUAD-01:seti": [-10., 10.],
        # "magnet:CLA-S02-MAG-QUAD-02:seti": [-10., 10.],
        # "magnet:CLA-S02-MAG-QUAD-03:seti": [-10., 10.],
        # "magnet:CLA-S02-MAG-QUAD-04:seti": [-10., 10.],

        # "magnet:CLA-S03-MAG-QUAD-01:seti": [-10., 10.],

        # "magnet:CLA-S04-MAG-QUAD-01:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-02:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-03:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-04:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-05:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-06:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-07:seti": [-10., 10.],
        # "magnet:CLA-S04-MAG-QUAD-08:seti": [-10., 10.],

        # "magnet:CLA-S05-MAG-QUAD-01:seti": [-10., 10.],
        # "magnet:CLA-S05-MAG-QUAD-02:seti": [-10., 10.],

        "magnet:CLA-S06-MAG-QUAD-01:seti": [-10., 10.],
        "magnet:CLA-S06-MAG-QUAD-02:seti": [-10., 10.],

        "magnet:CLA-S07-MAG-QUAD-01:seti": [-10., 10.],
        "magnet:CLA-S07-MAG-QUAD-02:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-03:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-04:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-05:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-06:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-07:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-08:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-09:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-10:seti": [-10., 10.],
        # "magnet:CLA-S07-MAG-QUAD-11:seti": [-10., 10.],
    }

    observables = [
        "charge:CLA-S01-DIA-WCM-01:q",
        # "charge:CLA-SP3-DIA-FCUP-01:q",
        "charge:CLA-S07-DIA-FCUP-01:q",
        "constraintsList"

    ]

    _machine_areas = {
        "magnet": ['S06', 'S07'],
        "charge": ['S01', 'S07']
    }

    _constraintsList = {
        "charge_ratio": {
            "type": "greaterthan",
            "value": ["`charge:CLA-S07-DIA-FCUP-01:q`"],
            "limit": "`charge:CLA-S01-DIA-WCM-01:q`",
            "weight": 1,
        },
    }

    def model_post_init(self, context):
        self._cons = constraintsClass()
        return super().model_post_init(context)

    def process_value(self, value, observables: dict):
        if isinstance(value, (list, tuple)):
            return [self.process_value(v, observables) for v in value]
        else:
            if isinstance(value, str):
                return interpret_expression(value, observables)
        return value

    def get_constraintsList(self, observables: dict):
        con_list = deepcopy(self._constraintsList)
        for cons in self._constraintsList:
            for key in ["value", "limit"]:
                con_list[cons][key] = self.process_value(con_list[cons][key], observables)

        return self._cons.constraints(con_list)

    def get_observables(self, observable_names: list[str]) -> dict:
        if not self.interface:
            raise BadgerNoInterfaceError

        observables = self.interface.get_observables(observable_names)
        if "constraintsList" in observable_names and self._constraintsList:
            observables["constraintsList"] = self.get_constraintsList(observables)
        return observables
