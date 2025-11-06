import numpy as np
def sphericalToCartesian(r,theta,phi):
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.cos(phi)
    z = r * np.sin(phi) * np.sin(theta)
    return np.array([x, y, z])
def rotatePoint(point, angle, axis):
    axis = axis / np.linalg.norm(axis)        # ensure normalized
    cos_a = np.cos(angle)   # rodrigues' rotation formula
    sin_a = np.sin(angle)
    return (
        point * cos_a
        + np.cross(axis, point) * sin_a
        + axis * np.dot(axis, point) * (1 - cos_a)
    )

def getAxes(cameraPoint, lookAt, worldUp):
    zCam = lookAt - cameraPoint
    zCam = zCam / np.linalg.norm(
        zCam
    )   # z axis of camera (positive is foward)
    xCam = np.cross(worldUp, zCam)
    xCam = xCam / np.linalg.norm(xCam)   # x axis of camera
    yCam = np.cross(zCam, xCam)
    yCam = yCam / np.linalg.norm(yCam)   # y axis of camera
    return xCam, yCam, zCam
