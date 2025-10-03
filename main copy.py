import numpy as np
import pygame
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
    angle=np.radians(angle)
    rotatedPoint = axis*np.dot(axis,point)+(np.cos(angle))*np.cross(np.cross(axis,point),axis)+np.sin(angle)*np.cross(axis,point)
    return rotatedPoint
#main
ortho=True
orbit=False
#define points temp
surfacePoints=createCube(np.array([0,0,0]),10,0.5)
print(surfacePoints)
cameraPoint=np.array([10,10,50])
cameraPoint = cameraPoint.astype(float)
lookAt=np.array([0,0,0])
worldUp=np.array([0,0,1])
angle=0.0
angleIncrement=0.5
angleIncrement=np.radians(angleIncrement)
dragMoveSpeed=0.5
dragging=False

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
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                #get movement and axes of camera
                dx,dy = event.rel
                xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
                movementVec = dx*xCam+(dy)*yCam
                movementVec = movementVec/np.linalg.norm(movementVec)
                angle=np.linalg.norm([dx,dy])*dragMoveSpeed #angle proportional to mouse movement
                #axis of rotation is equal to screen movement vector (in cam x and y) crossed w cam z
                axisOfRot = np.cross(movementVec,zCam)
                axisOfRot = axisOfRot/np.linalg.norm(axisOfRot)
                #compute rotation
                cameraPoint = rotatePoint(cameraPoint-lookAt,angle,axisOfRot)+lookAt
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                orbit = not orbit
                if orbit:
                    #update current angle based on current camera position
                    cameraXtoCenter = cameraPoint[0] - lookAt[0]
                    cameraYtoCenter = cameraPoint[1] - lookAt[1]
                    angle = (np.arctan2(cameraXtoCenter, cameraYtoCenter))
                    orbitRadius = np.linalg.norm([cameraXtoCenter, cameraYtoCenter])  # use current distance
            if event.key == pygame.K_r:
                angle = 0
                cameraPoint=np.array([10,10,50])
    screen.fill("black")
    if orbit:
        angle = angle + angleIncrement
        cameraPoint = simpleRotation(cameraPoint,angle,lookAt,50)
    camPoints = worldToCamera(surfacePoints,cameraPoint,lookAt,worldUp)
    drawPoints(camPoints)
    pygame.display.flip()
    clock.tick(60)  #FPS limit
pygame.quit()
