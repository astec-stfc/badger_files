import os
import time
from badger import interface
from CATAP.diagnostics.camera import CameraFactory
from CATAP.diagnostics.charge import ChargeFactory
from CATAP.laser.pi_laser import PILaserFactory
from CATAP.magnet import MagnetFactory
from image_saving import get_beam_image_with_background

os.environ["EPICS_CA_ADDR_LIST"] = "192.168.83.255 192.168.119.255"
os.environ["EPICS_CA_SERVER_PORT"] = ""
os.environ["EPICS_CA_AUT_ADDR_LIST"] = "NO"

factories = {}
machine_areas = {}


def get_factory(factory_name: str):
    if factory_name not in factories:
        if factory_name not in machine_areas:
            machine_areas[factory_name] = None
        print(f'Initialising {factory_name} factory with areas: {machine_areas[factory_name]}!')
        if factory_name == "magnet":
            _magnetFactory = MagnetFactory(is_virtual=False, areas=machine_areas[factory_name])
            factories[factory_name] = _magnetFactory
        elif factory_name == "charge":
            _chargeFactory = ChargeFactory(is_virtual=False, areas=machine_areas[factory_name])
            factories[factory_name] = _chargeFactory
        elif factory_name == "camera":
            _cameraFactory = CameraFactory(is_virtual=False, areas=machine_areas[factory_name])
            factories[factory_name] = _cameraFactory
        elif factory_name == "pilaser":
            _laserFactory = PILaserFactory(is_virtual=False, areas=machine_areas[factory_name])
            factories[factory_name] = _laserFactory
    return factories[factory_name]


class Interface(interface.Interface):
    name = "CATAP"

    # Private variables
    _states: dict = {}

    def set_values(self, channel_inputs):
        for channel, value in channel_inputs.items():
            factory, element_name, method = channel.split(":")
            print(f'CATAP setting {element_name} from factory {factory} to {value} via {method}')
            element = get_factory(factory).get_hardware(element_name)
            setattr(element, method, value)

            self._states[channel] = value
        time.sleep(1)

    def get_values(self, channel_names):
        channel_outputs = {}

        for channel in channel_names:
            try:
                factory, element_name, method = channel.split(":")
                element = get_factory(factory).get_hardware(element_name)
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
            if ':' in observable:
                factory, element_name, method = observable.split(":")
                print(f'CATAP observing {method} for {element_name} from factory {factory}')
                if factory == "camera" or factory == "screen":
                    outputs[observable] = self.fit_image(element_name, method)
                else:
                    element = get_factory(factory).get_hardware(element_name)
                    outputs[observable] = getattr(element, method)
                print(f'\tvalue = {outputs[observable]}')
            else:
                outputs[observable] = 0.
        return outputs

    def fit_image(self, camera: str, method: str):
        camera = get_factory['camera'].get_hardware(camera)
        laser = get_factory['pilaser'].get_hardware('PILaser')
        get_beam_image_with_background(laser_shutter=laser, camera=camera, scalefactor=1)
