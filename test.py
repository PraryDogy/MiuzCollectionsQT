import io
import numpy as np
import tifffile
from PIL import Image, ImageCms

jpg_path = "/Users/Loshkarev/Desktop/N01-MLN2782H_2.jpg"  # ваш jpg
tif_path = "/Users/Loshkarev/Desktop/N01-MLN2782H_2.tif"  # ваш tif

# JPG через PIL
pj = Image.open(jpg_path)
print("JPG mode:", pj.mode, pj.size, "ICC:", "icc_profile" in pj.info)
if "icc_profile" in pj.info:
    p = ImageCms.ImageCmsProfile(io.BytesIO(pj.info["icc_profile"]))
    print("  JPG profile:", ImageCms.getProfileDescription(p).strip())
aj = np.array(pj.convert("RGB")).astype(np.float64)

# TIF через tifffile
at = tifffile.imread(tif_path)
print("TIF shape:", at.shape, "dtype:", at.dtype, "min/max:", at.min(), at.max())
if at.ndim == 3 and at.shape[-1] == 4:
    at = at[..., :3]
at = at.astype(np.float64)

# Если TIF 16-битный, приводим к 8-битному диапазону для сравнения
if at.max() > 255:
    at = at / 257.0

print("JPG mean RGB:", aj.reshape(-1, 3).mean(0).round(1))
print("TIF mean RGB:", at.reshape(-1, 3).mean(0).round(1))