import numpy as np
import pygame 
import tkinter as tk
#funcitons
def worldToCamera(surfacePoints,cameraPoint,lookAt,worldUp): #coordinate transform func
    #create camera axes
    zCam=(lookAt-cameraPoint) 
    zCam=zCam/np.linalg.norm(zCam) #z axis of camera (positive is foward)
    xCam=np.cross(worldUp,zCam)
    xCam=xCam/np.linalg.norm(xCam) #x axis of camera
    yCam=np.cross(zCam,xCam)
    yCam=yCam/np.linalg.norm(yCam) #y axis of camera
    #create rotation matrix
    rotMatrix=np.array([xCam,yCam,zCam])
    #translate points to camera origin
    transPoints=surfacePoints-cameraPoint
    #rotate points to camera axes
    camPoints=rotMatrix @ transPoints.T
    camPoints=camPoints.T
    return camPoints
def drawPoints(points):
    for point in points:
        x=point[0]*10+640
        y=point[1]*10+360
        pygame.draw.circle(screen,"white",(int(x),int(y)),2)
def simpleRotation(camera,angle,center,orbitRadius):
    camera[0]=orbitRadius*np.cos(angle)+center[0]
    camera[1]=orbitRadius*np.sin(angle)+center[1]
    return camera.astype(float)
def createCube(center,sideLength,step):
    halfSide=sideLength/2
    sideLow=center[0]-halfSide
    sideHigh=center[0]+halfSide
    #coordinate range
    coords = np.arange(sideLow, sideHigh+step,step)
    points = []
    #create points on cube surface by holding one axis constant at a time
    for x in [sideLow, sideHigh]: #constant x
        for y in [sideLow, sideHigh]:
            for z in coords:
                points.append([x, y, z])
        for z in [sideLow, sideHigh]:
            for y in coords:
                points.append([x, y, z])
    for y in [sideLow, sideHigh]: #constant y
        for x in [sideLow, sideHigh]:
            for z in coords:
                points.append([x, y, z])
        for z in [sideLow, sideHigh]:
            for x in coords:
                points.append([x, y, z])
    for z in [sideLow, sideHigh]: #constant z
        for x in [sideLow, sideHigh]:
            for y in coords:
                points.append([x, y, z])
        for y in [sideLow, sideHigh]:
            for x in coords:
                points.append([x, y, z])
    return np.unique(np.array(points), axis=0) 
def getAxes(cameraPoint,lookAt,worldUp):
    zCam=(lookAt-cameraPoint) 
    zCam=zCam/np.linalg.norm(zCam) #z axis of camera (positive is foward)
    xCam=np.cross(worldUp,zCam)
    xCam=xCam/np.linalg.norm(xCam) #x axis of camera
    yCam=np.cross(zCam,xCam)
    yCam=yCam/np.linalg.norm(yCam) #y axis of camera
    
    return xCam,yCam,zCam
def rotatePoint(point,angle,axis):
    axis = axis / np.linalg.norm(axis)        # ensure normalized
    cos_a = np.cos(angle) #rodrigues' rotation formula
    sin_a = np.sin(angle)
    return (point * cos_a +
            np.cross(axis, point) * sin_a +
            axis * np.dot(axis, point) * (1 - cos_a))
#shapes
def createSphere(center,radius,step):
    points = []
    for phi in np.arange(0, np.pi + step, step):  # polar angle
        for theta in np.arange(0, 2 * np.pi + step, step):  # azimuthal angle
            x = center[0] + radius * np.sin(phi) * np.cos(theta)
            y = center[1] + radius * np.sin(phi) * np.sin(theta)
            z = center[2] + radius * np.cos(phi)
            points.append([x, y, z])
    return np.array(points)
#main
ortho=True
orbit=False
#define points temp
surfacePoints=createCube(np.array([0,0,0]),10,0.10)
cameraPoint=np.array([10,10,50])
cameraPoint = cameraPoint.astype(float)
lookAt=np.array([0,0,0])
worldUp=np.array([0,0,1])
angle=0.0
angleIncrement=0.5
angleIncrement=np.radians(angleIncrement)
dragMoveSpeed=0.01
moveSpeed=2
dragging=False
orbitRadius = np.linalg.norm(cameraPoint - lookAt)
angleX=0.0
angleY=0.0
#init for orbits
last_drag_vec = np.array([0.0, 0.0, 0.0])   # world-space drag vector
angular_velocity = 0.0                      # radians per frame
axisOfRot = np.array([0.0, 0.0, 1.0])       # fallback axis
damping = 0.95                              # inertia damping per frame (0..1)
orbitRadius = np.linalg.norm(cameraPoint - lookAt)
#pygame display
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  
                dragging = True 
                orbit=False   
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging=False  
                if angularVelocity <= 1e-6:
                    orbit = False
                else:
                    orbit = True
                    axisOfOrbit=axisOfRot
                    orbitVelocity=angularVelocity
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                #get movement and axes of camera
                dx,dy = event.rel #screen space drag
                xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
                dragWorld = dx*xCam+(dy)*yCam
                dragVelocity = np.linalg.norm(dragWorld)
                dragWorld = dragWorld/dragVelocity
                speed=np.hypot(dx,dy)
                if np.linalg.norm(dragVelocity) <1e-8:
                    continue
                angularVelocity=speed*dragMoveSpeed #angle proportional to mouse movement
                #axis of rotation is equal to screen movement vector (in cam x and y) crossed w cam z
                axisOfRot = np.cross(dragWorld,zCam)
                axisOfRot = axisOfRot/np.linalg.norm(axisOfRot)
                #compute rotation
                cameraPoint = rotatePoint(cameraPoint-lookAt,angularVelocity,axisOfRot)+lookAt
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                angle = 0
                cameraPoint=np.array([10,10,50])
    screen.fill("black")
    if orbit:
        #compute rotation
        pass    
    camPoints = worldToCamera(surfacePoints,cameraPoint,lookAt,worldUp)
    drawPoints(camPoints)
    pygame.display.flip()
    clock.tick(60)  #FPS limit
pygame.quit()
