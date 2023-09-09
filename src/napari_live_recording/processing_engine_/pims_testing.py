import pims
import tifffile as tf
import numpy as np
from frame_buffer import Framebuffer
import matplotlib.pyplot as plt
from image_filters.gauss import matlab_style_gauss2D
from image_filters.other_gauss import blur

buffer = Framebuffer(18, (512, 512))

tif = tf.TiffFile(
    r"C:\Users\felix\PycharmProjects\Testing\MyCamera-MicroManager-DemoCamera-DCam_Time.ome.tif"
)

for i in range(len(tif.pages)):
    image = tf.imread(
        r"C:\Users\felix\PycharmProjects\Testing\MyCamera-MicroManager-DemoCamera-DCam_Time.ome.tif",
        series=i,
    )
    buffer.addFrame(image)


fig, axs = plt.subplots(1, 3)


image = np.uint8(buffer.buffer[1])
# image_blurred = blur(image)
# image_gauss = matlab_style_gauss2D(image, shape=(3, 3), sigma=0.5)

# axs[0].imshow(image, cmap="gray")

# axs[1].imshow(image_blurred, cmap="gray")

# axs[2].imshow(image_gauss, cmap="gray")
# plt.show()
