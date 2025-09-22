#         tmpdir = TemporaryDirectory()
#        directory = tmpdir.__enter__()
#        self._framework.set_directory(directory)

import os
from copy import deepcopy
from pydantic import Field
from badger import environment
from badger.errors import (
    BadgerNoInterfaceError,
)
from badger.formula import extract_variable_keys, interpret_expression
from interfaces.SimFrame import SimFrameInterface
from SimulationFramework.Modules.optimisation.constraints import constraintsClass


class Environment(environment.Environment):
    base_dir: str | os.PathLike = os.path.abspath(r"C:\Users\jkj62.CLRC\Documents\GitHub\SimFrame_Examples\badger/")
    settings_file: str = Field(default="./basefiles/FEBE_2_Bunches.def")
    start_lattice: str | None = Field(default="FEBE")
    end_lattice: str | None = Field(default="FEBE")
    prefix: str | os.PathLike = Field(
        default=os.path.abspath(r"../basefiles/")
    )
    sampling: int = Field(default=2)

    name = "SFExample"
    variables = {
        "CLA-L4H-LIN-CAV-01:phase": [-250, -150],
        "bunch_compressor:angle": [0.08, 0.15],
        "CLA-L02-LIN-CAV-01:phase": [0, 45],
        "CLA-L03-LIN-CAV-01:phase": [0, 45],
    }
    observables = [
        "CLA-FEC1-SIM-FOCUS-01:sigma_t",
        "CLA-FEC1-SIM-FOCUS-01:enx",
        "CLA-FEC1-SIM-FOCUS-01:eny",
        "CLA-FEC1-SIM-FOCUS-01:sigma_cp",
        "CLA-FEC1-SIM-FOCUS-01:mean_cp",
        "constraintsList",
    ]

    _generator_params = {
        "reference_point": {
            "1e15 * `CLA-FEC1-SIM-FOCUS-01:sigma_t`": 1.0,
            "1e9 * `CLA-FEC1-SIM-FOCUS-01:enx`": 1.0,
            "1e9 * `CLA-FEC1-SIM-FOCUS-01:eny`": 1.0,
        }
    }

    _constraintsList = {
        "momentum_max": {
            "type": "lessthan",
            "value": ["1e-6 * `CLA-FEC1-SIM-FOCUS-01:mean_cp`"],
            "limit": 255,
            "weight": 250,
        },
        "momentum_min": {
            "type": "greaterthan",
            "value": ["1e-6 * `CLA-FEC1-SIM-FOCUS-01:mean_cp`"],
            "limit": 245,
            "weight": 150,
        },
        "energyspread": {
            "type": "lessthan",
            "value": ["100 * `CLA-FEC1-SIM-FOCUS-01:sigma_cp` / `CLA-FEC1-SIM-FOCUS-01:mean_cp`"],
            "limit": 1,
            "weight": 5,
        },
        "emitx": {
            "type": "lessthan",
            "value": ["1e6 * abs(`CLA-FEC1-SIM-FOCUS-01:enx`)"],
            "limit": 5,
            "weight": 50,
        },
        "sigma_t": {
            "type": "lessthan",
            "value": ["1e15 * abs(`CLA-FEC1-SIM-FOCUS-01:sigma_t`)"],
            "limit": 10,
            "weight": 10,
        },
    }

    _set_variables = {
        "CLA-L02-LIN-CAV-01:phase": 19.64,
        "CLA-L03-LIN-CAV-01:phase": 15.67,
        "CLA-L4H-LIN-CAV-01:phase": -186.7,
        "bunch_compressor:angle": 0.1229,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the interface if not already set
        self._cons = constraintsClass()
        self.interface = SimFrameInterface(
            base_dir=r"C:\Users\jkj62.CLRC\Documents\GitHub\SimFrame_Examples\badger/",
            settings_file=self.settings_file,
            start_lattice=self.start_lattice,
            end_lattice=self.end_lattice,
            prefix=self.prefix,
            params=self.observables,
            sampling=self.sampling,
        )
        self.interface.set_values(self._set_variables)

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
            # print('get_constraints', cons, con_list[cons]["value"], self.process_value(con_list[cons]["value"], observables))
            con_list[cons]["value"] = self.process_value(con_list[cons]["value"], observables)
        # print("Constraints:", self._cons.constraintsList(con_list))
        return self._cons.constraints(con_list)

    @environment.process_formulas
    def get_observables(self, observable_names: list[str]) -> dict:
        if not self.interface:
            raise BadgerNoInterfaceError

        observables = self.interface.get_observables(observable_names)
        if "constraintsList" in observable_names and self._constraintsList:
            observables["constraintsList"] = self.get_constraintsList(observables)
        return observables
