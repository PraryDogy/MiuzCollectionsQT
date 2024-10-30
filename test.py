from utils import ImageUtils, ResizeImg

src = "/Users/Loshkarev/Desktop/BF-9х16-0001.jpg"
img = ImageUtils.read_image(src)
img = ResizeImg.crop_to_square(img)