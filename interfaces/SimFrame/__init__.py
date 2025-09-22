import os
import re
from badger import interface
from SimulationFramework import Framework
from tempfile import TemporaryDirectory
from pydantic import Field

beam_evaluate = (
    "sigma_x",
    "sigma_y",
    "sigma_t",
    "sigma_z",
    "sigma_cp",
    "linear_chirp_z",
    "beta_x",
    "beta_y",
    "alpha_x",
    "alpha_y",
    "peak_current",
    "enx",
    "eny",
    "mean_energy",
    "mean_cp",
    "momentum_spread",
)


class SimFrameInterface(interface.Interface):
    name = "SimFrameInterface"
    base_dir: str = Field(default=".", description="SimFrame base directory")
    settings_file: str = Field(
        default="Lattices/clara400_v13.def",
        description="SimFrame Settings file to load",
    )
    start_lattice: str | None = Field(
        default=None, description="SimFrame starting lattice to track"
    )
    end_lattice: str | None = Field(
        default=None, description="SimFrame end lattice to track"
    )
    prefix: str | None = Field(default=".", description="SimFrame prefix")
    sampling: int = Field(default=3, description="SimFrame sub-sampling")

    # Private variables
    _states: dict

    def __init__(self, **data):
        super().__init__(**data)
        # print("SimFrameInterface init", data)
        self._states = {}

    def set_values(self, channel_inputs):
        for channel, value in channel_inputs.items():
            self._states[channel] = value

    def get_values(self, channel_names):
        channel_outputs = {}

        for channel in channel_names:
            try:
                value = self._states[channel]
            except KeyError:
                self._states[channel] = value = 0

            channel_outputs[channel] = value

        return channel_outputs

    def track(self):
        with TemporaryDirectory(dir=self.base_dir) as tmpdir:
            _framework = Framework.Framework(directory=self.base_dir, verbose=False)
            _framework.loadSettings(self.settings_file)
            _framework.setSubDirectory(tmpdir)
            _framework.change_Lattice_Code(
                "All", "elegant", exclude=["generator", "injector400"]
            )
            _startfile = (
                self.start_lattice
                if self.start_lattice is not None
                else _framework.lines[0]
            )
            _endfile = (
                self.end_lattice if self.end_lattice is not None else _framework.lines[-1]
            )
            _framework[_startfile].sample_interval = 2 ** (3 * self.sampling)
            _framework[_startfile].prefix = self.prefix

            for elem, val in self._states.items():
                name, param = elem.split(":")
                if name == "generator":
                    setattr(_framework.generator, param, val)
                elif name in _framework.elements:
                    _framework.modifyElement(name, param, val)
                elif name in _framework.groups:
                    _framework[name].change_Parameter(param, val)
            _framework.track(startfile=_startfile, endfile=_endfile)

            fwdir = Framework.load_directory(tmpdir, beams=True, framework=_framework)
            for index in range(len(fwdir.beams)):
                beam = fwdir.beams[index]
                scr = re.split(r" |/|\\", beam["filename"])[-1].split(".")[0]
                for param in beam_evaluate:
                    self._states.update({f"{scr}:{param}": float(getattr(beam, param))})
            return self._states

    def get_observables(self, observable_names: list[str]) -> dict:
        self.track()
        return {
            name: self._states[name]
            for name in observable_names
            if name in self._states
        }
