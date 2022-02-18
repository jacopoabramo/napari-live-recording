import napari
from skimage.data import astronaut

viewer = napari.view_image(astronaut(), rgb=True)

napari.run()