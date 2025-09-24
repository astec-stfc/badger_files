import numpy as np
from scipy.optimize import curve_fit
from image_saving import load_image


def gaussian_2d(xy, amp, x0, y0, sigma_x, sigma_y, offset):
    x, y = xy
    return (
        offset
        + amp
        * np.exp(
            -(((x - x0) ** 2) / (2 * sigma_x**2) + ((y - y0) ** 2) / (2 * sigma_y**2))
        ).ravel()
    )


def compute_rms_beam_size(image):
    total = np.sum(image)
    indices = np.indices(image.shape)
    x = indices[1]
    y = indices[0]
    x_mean = np.sum(x * image) / total
    y_mean = np.sum(y * image) / total
    x_rms = np.sqrt(np.sum(((x - x_mean) ** 2) * image) / total)
    y_rms = np.sqrt(np.sum(((y - y_mean) ** 2) * image) / total)
    return x_mean, y_mean, x_rms, y_rms


def fit_gaussian_beam_size(image):
    x_mean, y_mean, x_rms, y_rms = compute_rms_beam_size(image)
    y_size, x_size = image.shape
    x = np.arange(x_size)
    y = np.arange(y_size)
    x, y = np.meshgrid(x, y)
    initial_guess = (
        image.max() - image.min(),
        x_mean,
        y_mean,
        x_rms,
        y_rms,
        image.min(),
    )
    popt, pcov = curve_fit(gaussian_2d, (x, y), image.ravel(), p0=initial_guess)
    amplitude, x0, y0, sigma_x, sigma_y, offset = popt
    return popt


def otsu(gray, scale: float = 2**16):
    pixel_number = gray.shape[0] * gray.shape[1]
    mean_weight = 1.0 / pixel_number
    his, bins = np.histogram(gray, np.arange(0, scale))
    final_thresh = -1
    final_value = -1
    intensity_arr = np.arange(scale - 1)
    for t in bins[2:-1]:
        pcb = np.sum(his[:t])
        pcf = np.sum(his[t:])
        Wb = pcb * mean_weight
        Wf = pcf * mean_weight

        mub = np.sum(intensity_arr[:t] * his[:t]) / float(pcb)
        muf = np.sum(intensity_arr[t:] * his[t:]) / float(pcf)
        value = Wb * Wf * (mub - muf) ** 2

        if value > final_value:
            final_thresh = t
            final_value = value
    final_img = gray.copy()
    final_img[gray > final_thresh] = scale
    final_img[gray < final_thresh] = final_thresh
    return final_img


def fit_array_image(entry: dict[str, str], cut: int = 1):

    img = entry["image_data"]
    if "background_image_data" in entry:
        bg = entry["background_image_data"]

    if bg:
        img_sub = img.astype(float) - bg.astype(float)
    else:
        img_sub = img.astype(float)

    img_sub[img_sub < 0] = 0

    img_sub_otsu = otsu(img_sub)
    img_sub_sub = img_sub_otsu[::cut, ::cut]

    fit_x, fit_y, popt = fit_gaussian_beam_size(img_sub_sub)
    fit_x *= cut
    fit_y *= cut
    popt *= cut

    return popt


def fit_saved_image(entry: dict[str, str], cut: int = 1):
    base_image_path = "\\\\claraserv3.dl.ac.uk"
    img_path = base_image_path + entry["image_file"] + "_full.hdf"
    if "background_image_file" in entry:
        bg_path = base_image_path + entry["background_image_file"] + "_full.hdf"
    else:
        bg_path = False

    try:
        img = load_image(img_path)
        if bg_path:
            bg = load_image(bg_path)
    except Exception as e:
        print(f"Skipping {img_path} or {bg_path}: {e}")

    if bg_path:
        img_sub = img.astype(float) - bg.astype(float)
    else:
        img_sub = img.astype(float)

    img_sub[img_sub < 0] = 0

    img_sub_otsu = otsu(img_sub)
    img_sub_sub = img_sub_otsu[::cut, ::cut]

    fit_x, fit_y, popt = fit_gaussian_beam_size(img_sub_sub)
    fit_x *= cut
    fit_y *= cut
    popt *= cut

    return popt
