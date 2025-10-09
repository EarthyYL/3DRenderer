import numpy as np
def sphericalToCartesian(r,theta,phi):
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.cos(phi)
    z = r * np.sin(phi) * np.sin(theta)
    return np.array([x, y, z])
