import numpy as np
import pygame
def worldToCamera(
    surfacePoints, cameraPoint, lookAt, worldUp
):   # coordinate transform func
    # create camera axes
    zCam = lookAt - cameraPoint
    zCam = zCam / np.linalg.norm(
        zCam
    )   # z axis of camera (positive is foward)
    xCam = np.cross(worldUp, zCam)
    xCam = xCam / np.linalg.norm(xCam)   # x axis of camera
    yCam = np.cross(zCam, xCam)
    yCam = yCam / np.linalg.norm(yCam)   # y axis of camera
    # create rotation matrix
    rotMatrix = np.array([xCam, yCam, zCam])
    # translate points to camera origin
    transPoints = surfacePoints - cameraPoint
    # rotate points to camera axes
    camPoints = rotMatrix @ transPoints.T
    camPoints = camPoints.T
    return camPoints


def drawPoints(points, f, surface, errorBool):   # f is focal length in pixels
    screen_center_x = 640   # set center of screen this is for 1280x720
    screen_center_y = 360
    for point in points:   # iterate through points
        x_cam, y_cam, z_cam = point
        if z_cam <= 0:  # clip points behind camera and off screen
            continue
        # perspective projection
        x_screen = (x_cam / z_cam) * f + screen_center_x
        y_screen = (y_cam / z_cam) * f + screen_center_y
        try:
            pygame.draw.circle(
                surface, 'white', (int(x_screen), int(y_screen)), 2
                )
        except Exception as e:
            if errorBool:
                print(
                    f'Error drawing point at ({x_screen}, {y_screen}): {e}',
                    flush=True,
                )

def twoDimRot(R3CameraCoordinates, angle): #USE RADIANS
     # ignores the z value since we rotating in 2D
    rotationMatrix=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    xyVector = rotationMatrix @ (R3CameraCoordinates[:, [0, 1]]).T
    xyVector = xyVector.T
    R3CameraCoordinates[:, [0, 1]] = xyVector
    return R3CameraCoordinates
