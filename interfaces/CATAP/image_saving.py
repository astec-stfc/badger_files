import os
import time
import h5py
from epics import caput, caget
import numpy as np


def get_camera_ArraySize0(camera_name: str):
    return caget(camera_name + ":CAM2:ArraySize0_RBV")


def get_camera_ArraySize1(camera_name: str):
    return caget(camera_name + ":CAM2:ArraySize1_RBV")


def get_camera_ScaleFactor(camera_name: str):
    caget(camera_name + ":CAM:ScaleFactor")


def set_camera_ScaleFactor(camera_name: str, scalefactor: int = 1):
    caput(camera_name + ":CAM:ScaleFactor", scalefactor)
    time.sleep(0.1)


def get_data_array(camera_name, scalefactor: int = 4):
    original_scalefactor = get_camera_ScaleFactor(camera_name=camera_name)
    scalefactor = max(0, min(4, scalefactor))
    set_camera_ScaleFactor(camera_name=camera_name, scalefactor=int(scalefactor))
    size0 = get_camera_ArraySize0(camera_name=camera_name)
    size1 = get_camera_ArraySize1(camera_name=camera_name)
    data = caget(camera_name + ":CAM2:ArrayData", count=size0 * size1)
    set_camera_ScaleFactor(
        camera_name=camera_name, scalefactor=int(original_scalefactor)
    )
    return np.array(data).reshape((size1, size0))


def get_beam_image(laser_shutter, camera, scalefactor: int = 4):
    laser_shutter.open_shutters()
    return {"image_data": get_data_array(camera, scalefactor)}


def get_background_image(laser_shutter, camera, scalefactor: int = 4):
    laser_shutter.close_shutters()
    return {"background_image_data": get_data_array(camera, scalefactor)}


def get_beam_image_with_background(laser_shutter, camera, scalefactor: int = 4):
    are_shutters_open = laser_shutter.shutters_open
    output = {}
    output.update(
        get_background_image(
            laser_shutter=laser_shutter, camera=camera, scalefactor=scalefactor
        )
    )
    output.update(
        get_beam_image(
            laser_shutter=laser_shutter, camera=camera, scalefactor=scalefactor
        )
    )
    if are_shutters_open:
        laser_shutter.open_shutters()
    else:
        laser_shutter.close_shutters()
    return output


def save_image(camera):
    time.sleep(1)
    camera.save(num_images=1, timeout=1)
    filename = os.path.join(camera.hdf_filepath, camera.hdf_filename)
    attempts = 0
    while filename is None and attempts < 3:
        attempts += 1
        time.sleep(3)
        camera.save(num_images=1, timeout=1)
        filename = os.path.join(camera.hdf_filepath, camera.hdf_filename)
    if not filename:
        print("####  IMAGE ERROR - CARRYING ON  ####")
        return None
    return filename


def save_beam_image(laser_shutter, camera):
    laser_shutter.open_shutters()
    return {"image_file": save_image(camera)}


def save_background_image(laser_shutter, camera):
    laser_shutter.close_shutters()
    return {"background_image_file": save_image(camera)}


def save_image_with_background(laser_shutter, camera):
    background_image_file = save_background_image(
        laser_shutter=laser_shutter, camera=camera
    )["background_image_file"]
    image_file = save_beam_image(laser_shutter=laser_shutter, camera=camera)[
        "image_file"
    ]
    return {"background_image_file": background_image_file, "image_file": image_file}


def load_image(image_path, dataset_name="Capture000001"):
    """Load image from HDF5 file."""
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    with h5py.File(image_path, "r") as f:
        if dataset_name in f:
            img = f[dataset_name][:]
        else:
            ds = list(f.keys())[0]
            img = f[ds][:]
    return img
