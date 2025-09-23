import os
from badger import interface
from CATAP.diagnostics.camera import CameraFactory
from CATAP.diagnostics.charge import ChargeFactory
from CATAP.magnet import MagnetFactory


os.environ["EPICS_CA_ADDR_LIST"] = "192.168.83.255 192.168.119.255"
os.environ["EPICS_CA_SERVER_PORT"] = ""
os.environ["EPICS_CA_AUT_ADDR_LIST"] = "NO"


class CATAPInterface(interface.Interface):
    name = "CATAPInterface"

    # Private variables
    _factories = {}
    _states: dict

    def __init__(self, machine_areas: dict, **data):
        super().__init__(**data)
        self._machine_areas = machine_areas
        self._states = {}

    def get_factory(self, factory_name: str):
        if factory_name not in self._factories:
            if factory_name not in self._machine_areas:
                self._machine_areas[factory_name] = None
            print(f'Initialising {factory_name} factory with areas: {self._machine_areas[factory_name]}!')
            if factory_name == "magnet":
                self._magnetFactory = MagnetFactory(is_virtual=False, areas=self._machine_areas[factory_name])
                self._factories[factory_name] = self._magnetFactory
            elif factory_name == "charge":
                self._chargeFactory = ChargeFactory(is_virtual=False, areas=self._machine_areas[factory_name])
                self._factories[factory_name] = self._chargeFactory
            elif factory_name == "camera":
                self._cameraFactory = CameraFactory(is_virtual=False, areas=self._machine_areas[factory_name])
                self._factories[factory_name] = self._cameraFactory
        return self._factories[factory_name]

    def set_values(self, channel_inputs):
        for channel, value in channel_inputs.items():
            factory, element_name, method = channel.split(":")
            print(f'CATAP setting {element_name} from factory {factory} to {value} via {method}')
            element = self.get_factory(factory).get_hardware(element_name)
            setattr(element, method, value)
            
            self._states[channel] = value

    def get_values(self, channel_names):
        channel_outputs = {}

        for channel in channel_names:
            try:
                factory, element_name, method = channel.split(":")
                element = self.get_factory(factory).get_hardware(element_name)
                print(f'CATAP getting {method} for {element_name} from factory {factory}')
                value = getattr(element, method)
                print(f'\tvalue = {value}')
                self._states[channel] = value
            except Exception:
                self._states[channel] = value = 0

            channel_outputs[channel] = value

        return channel_outputs

    def get_observables(self, observable_names: list[str]) -> dict:
        outputs = {}

        for observable in observable_names:
            factory, element_name, method = observable.split(":")
            print(f'CATAP observing {method} for {element_name} from factory {factory}')
            if factory == "camera" or factory == "screen":
                outputs[observable] = self.fit_image(element_name, method)
            else:
                element = self.get_factory(factory).get_hardware(element_name)
                outputs[observable] = getattr(element, method)
        return outputs

    def fit_image(self, camera: str, method: str):
        self._cameraFactory.get_camera(camera)
