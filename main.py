# outside modules
try:
    import numpy as np
    import pygame
    import tkinter as tk
    import time
    from tkinter.filedialog import askopenfilename
except Exception as e:
    print(f'Error while importing modules: {e}, exiting', flush=True)
    exit()

# folder files
import tools.debug_tools as debug_tools
import tools.parse_tools as parse_tools
import tools.camera_tools as camera_tools
import tools.render_tools as render_tools
debugErrors = True
debugLogs = False


def fileBrowse():   # file dialog function
    global filePath
    filePath = askopenfilename()
    if filePath:
        if filePath.lower().endswith('.obj'):
            button.config(text=filePath)
            close = tk.Button(root, text='Render', command=root.destroy)
            close.pack(pady=10)
        else:
            button.config(text='File must be .obj')

# tkinter root for file dialog
root = tk.Tk()
button = tk.Button(root, text='Browse for OBJ file', command=fileBrowse)
button.pack(pady=20)
lightingOn = tk.IntVar()
lightingOn.set(True)
lightButton = tk.Checkbutton(root, text='Enable Lighting', variable=lightingOn)
lightButton.pack()
root.mainloop()
lightingOn = lightingOn.get()

##PARSE THE FILE
try:
    vertices, normals, facesArray, centerPoint = parse_tools.parseOBJFile(
        filePath, debugErrors
    )
except Exception as e:
    print(f"File error: {e}, exiting")
    exit()
if debugLogs:
    debug_tools.writeFacesArrayToFile(
        facesArray, 'debug_output.txt'
    )   # write faces array to file for debugging
# functions
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


def rotatePoint(point, angle, axis):
    axis = axis / np.linalg.norm(axis)        # ensure normalized
    cos_a = np.cos(angle)   # rodrigues' rotation formula
    sin_a = np.sin(angle)
    return (
        point * cos_a
        + np.cross(axis, point) * sin_a
        + axis * np.dot(axis, point) * (1 - cos_a)
    )


def createAxes(length, step, centerPoint):
    points = []
    for i in np.arange(0 + centerPoint[0], length + step + centerPoint[0], step):
        points.append([i, centerPoint[1], centerPoint[2]])  # X-axis
    for i in np.arange(0 + centerPoint[1], length + step + centerPoint[1], step):
        points.append([centerPoint[0], i, centerPoint[2]])  # Y-axis
    for i in np.arange(0 + centerPoint[2], length + step + centerPoint[2], step):
        points.append([centerPoint[0], centerPoint[1], i])  # Z-axis
    return np.array(points)


#--CONFIG--#
axesOn = True
boundaryCubeOn = False
objScale = 5
drawMesh = False
focalLength = 500
dragMoveSpeed = 0.01
panMoveSpeed = 2
zoomSpeed = 0.1
rotateSpeed = 5 #deg per frame
lightSource = [1, 0, 0]
timingPrintOut = True

#non configuration initliazation
surfacePoints = vertices * objScale
rotationMatrix90DegX = np.array(
    [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
)   # rotate 90 deg around x axis to convert from obj coord system to standard
surfacePoints = surfacePoints @ rotationMatrix90DegX.T
surfacePointsOriginalCopy = surfacePoints
centerPoint= centerPoint @ rotationMatrix90DegX.T
if axesOn:
    axes = createAxes(50, 5, centerPoint)
    axesOriginalCopy = axes
if lightingOn:
    cullOn = True
else:
    cullOn = False
cameraPoint = np.array([1, 1, 100]) + centerPoint
cameraPoint = cameraPoint.astype(float)
lookAt = centerPoint.astype(float)
worldUp = np.array([0, 0, -1])
dragging = False
shiftHeld = False
movementScheme = 1
rotateAndPan = 1
freeFly = 2
angleCamTilt = 0
frameCount= 0
# pygame display
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
print('Opening visualization window', flush=True)
while running:
    # -- input handling --
    frameStart = time.perf_counter()
    t0 = time.perf_counter()
    pressed = pygame.key.get_pressed()   # for holding key behavior
    xCam, yCam, zCam = getAxes(cameraPoint, lookAt, worldUp)
    if pressed[pygame.K_LSHIFT]:   # shift toggle
        shiftHeld = True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT:  # shift toggle
                shiftHeld = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:   # reset
                lookAt = centerPoint.astype(float)
                angleCamTilt = 0
            if event.key == pygame.K_BACKSPACE:   # close
                running = False
            if event.key == pygame.K_m:   # toggle mesh
                drawMesh = not drawMesh
            if event.key == pygame.K_1:
                movementScheme = rotateAndPan
            if event.key == pygame.K_2:
                movementScheme = freeFly
        if movementScheme == rotateAndPan: # all controls for this scheme are in here
            if event.type == pygame.MOUSEBUTTONDOWN:  # start drag
                    if event.button == 1:
                        dragging = True
                        orbit = False
            elif event.type == pygame.MOUSEBUTTONUP:   # stop drag
                    if event.button == 1:
                        dragging = False #0 is placeholder for angular velocity
                        if 0 <= 1e-6:
                            orbit = False
                        else:
                            orbit = True
                            axisOfOrbit = axisOfRot
                            orbitVelocity = 0
            elif event.type == pygame.MOUSEMOTION:   # mouse drag to rotate
                    if dragging and not shiftHeld:
                        # get movement and axes of camera
                        dx, dy = event.rel   # screen space drag
                        xCam, yCam, zCam = getAxes(cameraPoint, lookAt, worldUp)
                        dragWorld = (
                            -dx * xCam + (-dy) * yCam
                        )   # y is inverted for pygame inverted axis
                        dragVelocity = np.linalg.norm(dragWorld)
                        dragWorld = dragWorld / dragVelocity
                        speed = np.hypot(dx, dy)
                        if np.linalg.norm(dragVelocity) < 1e-8:
                            continue
                        angularVelocity = (
                            speed * dragMoveSpeed
                        )   # angle proportional to mouse movement
                        # axis of rotation is equal to screen movement vector (in cam x and y) crossed w cam z
                        axisOfRot = np.cross(dragWorld, zCam)
                        axisOfRot = axisOfRot / np.linalg.norm(axisOfRot)
                        # compute rotation
                        cameraPoint = (
                            rotatePoint(
                                cameraPoint - lookAt, angularVelocity, axisOfRot
                            )
                            + lookAt
                        )
                        worldUp = rotatePoint(worldUp, angularVelocity, axisOfRot)
                    elif dragging and shiftHeld:   # pan
                        dx, dy = event.rel   # screen space drag
                        cameraPoint += (
                            -dx * xCam + (-dy) * yCam
                        )   # y is inverted for pygame inverted axis
                        lookAt += -dx * xCam + (-dy) * yCam
                        axes += -dx * xCam + (-dy) * yCam
            elif event.type == pygame.MOUSEWHEEL:   # zoom in/out
                if event.y == 1:
                    cameraPoint = cameraPoint - (cameraPoint - lookAt) * zoomSpeed
                elif event.y == -1:
                    cameraPoint = cameraPoint + (cameraPoint - lookAt) * zoomSpeed
    if movementScheme == rotateAndPan:
        if pressed[pygame.K_d]:
            angleCamTilt += np.deg2rad(rotateSpeed)
        if pressed[pygame.K_a]:
            angleCamTilt -= np.deg2rad(rotateSpeed)
    
    ## -- rendering -- ##
    inputTime = time.perf_counter() - t0
    t1 = time.perf_counter()
    screen.fill('black')
    camPoints = render_tools.worldToCamera(surfacePoints, cameraPoint, lookAt, worldUp)
    if timingPrintOut:
        transformTime = time.perf_counter() - t1
        t2 = time.perf_counter()
    if abs(angleCamTilt)>=1e-4:
        camPoints = render_tools.twoDimRot(camPoints,angleCamTilt)
    if not drawMesh:
        render_tools.drawPoints(camPoints, focalLength, screen, debugErrors)
        axesCam=render_tools.worldToCamera(axes, cameraPoint, lookAt, worldUp)
        if abs(angleCamTilt)>=1e-4:
            axesCam = render_tools.twoDimRot(axesCam,angleCamTilt)
        render_tools.drawPoints(axesCam, focalLength, screen, debugErrors)
    if drawMesh:
        #sort faces by Z so it renders in order
        facesSorted = render_tools.sortFacesByDepth(facesArray, camPoints)
        # perspective projection
        camZs = camPoints[:, 2]
        validMask = camZs > 0
        xScreen = (camPoints[:, 0] / camZs) * focalLength + 640
        yScreen = (camPoints[:, 1] / camZs) * focalLength + 360
        projectedPointsXY = np.stack([xScreen, yScreen], axis=1).astype(int)
    
        for face in facesSorted: 
            validIndices = face[:, 0][~np.isnan(face[:, 0])].astype(int)
            if len(validIndices) < 3:
                continue
            faceCam = camPoints[validIndices]
            #compute face normal in camera space

            #NOTE TO SELF IF YOU JUST INDEX INTO THE PREMADE LIST OF NORMALS THAT IS IN WORLD SPACE
            #THEN CALCULATE LIGHTING FROM THAT SO IT IS WORLD AGAINST WORLD
            #SO THE LIGHT IS FROM ONE LOCATION
            # only thing is that you need to dot it against the camera location vector to check for orientation for culling
            v1 = faceCam[1] - faceCam[0]
            v2 = faceCam[2] - faceCam[0]
            faceNormal = np.cross(v1, v2)
            faceNormal = faceNormal / np.linalg.norm(faceNormal)
            # cull if facing away and skip faces w vertices behind camera
            if cullOn and faceNormal[2] >= 0:
                continue
            if (np.any(faceCam[:, 2] <= 0)) | (len(validIndices) <= 2):
                continue
            projectedXY = projectedPointsXY[validIndices]
            # calculate lighting
            lightIntensity = np.dot(faceNormal, lightSource)
            color = [int(lightIntensity * 255)] * 3
            try:
                if (lightIntensity > 0) & lightingOn:
                    pygame.draw.polygon(screen, color, projectedXY)
                elif not lightingOn:
                    pygame.draw.polygon(screen, 'grey', projectedXY, 1)
            except Exception as e:
                if debugErrors:
                    print(
                        f'Error drawing polygon with points {projected} and color {color}: {e}',
                        flush=True,
                    )
    renderTime = time.perf_counter() - t2
    t3 = time.perf_counter()
    pygame.display.flip()
    clock.tick(60)  # FPS limit
    displayTime = time.perf_counter() - t3
    frameTotal = time.perf_counter() - frameStart
    fps = 1.0 / frameTotal if frameTotal > 0 else 0.0
    # Print summary every few frames
    frameCount += 1
    if frameCount % 30 == 0:
        if timingPrintOut:
            print(
                f"FPS: {fps:6.1f} | "
                f"Input: {inputTime*1000:5.2f} ms | "
                f"Transform: {transformTime*1000:5.2f} ms | "
                f"Render: {renderTime*1000:5.2f} ms | "
                f"Display: {displayTime*1000:5.2f} ms",
                flush=True,
            )
pygame.quit()
print('Exiting', flush=True)
