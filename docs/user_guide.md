# napari-live-recording user guide

## Installation

You can install `napari-live-recording` via [pip]. It is reccomended to install `napari-live-recording` in a virtual environment. This can be do so via:

- [venv], for example:
    
        python -m venv nlr
        nlr\Scripts\activate
        pip install napari-live-recording

- [conda] or [mamba]

        mamba create -n nlr python=3.10 napari-live-recording

Alternatively, if you want to install the plugin using the source code, you can do so by cloning the project and installing locally:

    git clone https://github.com/jacopoabramo/napari-live-recording
    cd napari-live-recording
    pip install .