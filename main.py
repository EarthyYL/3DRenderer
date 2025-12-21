# outside modules
try:
    import numpy as np
    import pygame
    import tkinter as tk
    import time
    from tkinter.filedialog import askopenfilename
    from OpenGL.GL import *
    from OpenGL.GLU import *
except Exception as e:
    print(f'Error while importing modules: {e}, exiting', flush=True)
    exit()

# folder files
import tools.debug_tools as debug_tools
import tools.parse_tools as parse_tools
import tools.camera_tools as camera_tools
import tools.render_tools as render_tools

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
def f32(array):
    return np.asarray(array, dtype=np.float32)

# tkinter root for file dialog
root = tk.Tk()
button = tk.Button(root, text='Browse for OBJ file', command=fileBrowse)
button.pack(pady=20)
# lighting button
lightingOn = tk.IntVar()
lightingOn.set(True)
lightButton = tk.Checkbutton(root, text='Enable Lighting', variable=lightingOn)
lightButton.pack()
# debug button
debugErrors = tk.IntVar()
debugErrors.set(False)
debugButton = tk.Checkbutton(
    root, text='Dump debug info to console', variable=debugErrors
)
debugButton.pack()
root.mainloop()
lightingOn = lightingOn.get()
debugErrors = debugErrors.get()

##PARSE THE FILE
vertices, normals, facesArray, centerPoint = parse_tools.parseOBJFileTriangulator(
    filePath, debugErrors
    )
if debugLogs:
    debug_tools.writeFacesArrayToFile(
        facesArray, 'debug_output.txt'
    )   # write faces array to file for debugging
# functions

def createAxes(length, step, centerPoint):
    points = []
    for i in np.arange(
        0 + centerPoint[0], length + step + centerPoint[0], step
    ):
        points.append([i, centerPoint[1], centerPoint[2]])  # X-axis
    for i in np.arange(
        0 + centerPoint[1], length + step + centerPoint[1], step
    ):
        points.append([centerPoint[0], i, centerPoint[2]])  # Y-axis
    for i in np.arange(
        0 + centerPoint[2], length + step + centerPoint[2], step
    ):
        points.append([centerPoint[0], centerPoint[1], i])  # Z-axis
    return np.array(points)


# --CONFIG--#
axesOn = True
boundaryCubeOn = False
objScale = 5
drawMesh = True
focalLength = 500
dragMoveSpeed = 0.01
panMoveSpeed = 2
zoomSpeed = 0.1
rotateSpeed = 5   # deg per frame
lightSource = [1, 0, 0]
timingPrintOut = True

# non configuration initliazation
surfacePoints = vertices * objScale
rotationMatrix90DegX = np.array(
    [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
)   # rotate 90 deg around x axis to convert from obj coord system to standard
surfacePoints = surfacePoints @ rotationMatrix90DegX.T
surfacePoints = f32(surfacePoints)
surfacePointsOriginalCopy = surfacePoints
centerPoint = centerPoint @ rotationMatrix90DegX.T
if axesOn:
    axes = createAxes(50, 5, centerPoint)
    axesOriginalCopy = axes
if lightingOn:
    cullOn = True
else:
    cullOn = False
cameraPoint = np.array([1, 1, 100]) + centerPoint
cameraPoint = f32(cameraPoint)
lookAt = centerPoint
lookAt = f32(lookAt)
worldUp = np.array([0, 0, -1])
worldUp = f32(worldUp)
dragging = False
shiftHeld = False
lightingStatic = True
movementScheme = 1
rotateAndPan = 1
freeFly = 2
angleCamTilt = 0
frameCount = 0
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
    xCam, yCam, zCam = camera_tools.getAxes(cameraPoint, lookAt, worldUp)
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
                lookAt = centerPoint
                angleCamTilt = 0
            if event.key == pygame.K_BACKSPACE:   # close
                running = False
            if event.key == pygame.K_m:   # toggle mesh
                drawMesh = not drawMesh
            # if event.key == pygame.K_l:
            # lightingStatic = not lightingStatic
            if event.key == pygame.K_1:
                movementScheme = rotateAndPan
            if event.key == pygame.K_2:
                movementScheme = freeFly
        if (
            movementScheme == rotateAndPan
        ):   # all controls for this scheme are in here
            if event.type == pygame.MOUSEBUTTONDOWN:  # start drag
                if event.button == 1:
                    dragging = True
                    orbit = False
            elif event.type == pygame.MOUSEBUTTONUP:   # stop drag
                if event.button == 1:
                    dragging = False   # 0 is placeholder for angular velocity
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
                    xCam, yCam, zCam = camera_tools.getAxes(cameraPoint, lookAt, worldUp)
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
                        camera_tools.rotatePoint(
                            cameraPoint - lookAt, angularVelocity, axisOfRot
                        )
                        + lookAt
                    )
                    worldUp = camera_tools.rotatePoint(worldUp, angularVelocity, axisOfRot)
                elif dragging and shiftHeld:   # pan
                    dx, dy = event.rel   # screen space drag
                    cameraPoint += (
                        -dx * xCam + (-dy) * yCam
                    )   # y is inverted for pygame inverted axis
                    lookAt += -dx * xCam + (-dy) * yCam
                    axes += -dx * xCam + (-dy) * yCam
            elif event.type == pygame.MOUSEWHEEL:   # zoom in/out
                if event.y == 1:
                    cameraPoint = (
                        cameraPoint - (cameraPoint - lookAt) * zoomSpeed
                    )
                elif event.y == -1:
                    cameraPoint = (
                        cameraPoint + (cameraPoint - lookAt) * zoomSpeed
                    )
    if movementScheme == rotateAndPan:
        if pressed[pygame.K_d]:
            angleCamTilt += np.deg2rad(rotateSpeed)
        if pressed[pygame.K_a]:
            angleCamTilt -= np.deg2rad(rotateSpeed)

    ## -- rendering -- ##
    inputTime = time.perf_counter() - t0
    t1 = time.perf_counter()
    screen.fill('black')
    camPoints = render_tools.worldToCamera(
        surfacePoints, cameraPoint, lookAt, worldUp
    )
    if timingPrintOut:
        transformTime = time.perf_counter() - t1
        t2 = time.perf_counter()
    if abs(angleCamTilt) >= 1e-4:
        camPoints = render_tools.twoDimRot(camPoints, angleCamTilt)
    if not drawMesh:
        render_tools.drawPoints(camPoints, focalLength, screen, debugErrors)
        axesCam = render_tools.worldToCamera(
            axes, cameraPoint, lookAt, worldUp
        )
        if abs(angleCamTilt) >= 1e-4:
            axesCam = render_tools.twoDimRot(axesCam, angleCamTilt)
        render_tools.drawPoints(axesCam, focalLength, screen, debugErrors)
    if drawMesh:
        t21 = time.perf_counter()
        # sort faces by Z value (back to front)
        facesSorted = render_tools.sortFacesByDepth(facesArray, camPoints)
        # perspective projection
        camZs = camPoints[:, 2]
        validMask = camZs > 0
        xScreen = (camPoints[:, 0] / camZs) * focalLength + 640
        yScreen = (camPoints[:, 1] / camZs) * focalLength + 360
        projectedPointsXY = np.stack([xScreen, yScreen], axis=1).astype(int)
        # extract vertex indices (v), normal indices (vn), and clean them too (replace nan w -1)
        vertexIdxs = facesSorted[:, :, 0].astype(int)
        normalIdxs = facesSorted[:, :, 2].astype(int)
        # where Idxs exist, pull from camPoints and put coords into faceVertices, otherwise put 0
        faceVertices = np.where(
            vertexIdxs[..., None] >= 0, camPoints[vertexIdxs], 0
        )
        # shape: (num of faces, max vertices (3), xyz coordinates (3 layer))
        if lightingStatic:
            # find normals in camera space
            v1 = faceVertices[:, 1, :] - faceVertices[:, 0, :]
            v2 = faceVertices[:, 2, :] - faceVertices[:, 0, :]
            faceNormals = np.cross(v1, v2)
        else:
            # Fetch vertex normals for all faces, then average
            faceNormalsRaw = np.where(
                normalIdxs[..., None] >= 0, normals[normalIdxs], 0
            )
            faceNormals = np.nanmean(faceNormalsRaw, axis=1)
        # ensure normalization in either case
        norm = np.linalg.norm(faceNormals, axis=1, keepdims=True)
        faceNormals = np.divide(faceNormals, norm)

        t22 = time.perf_counter()
        projectSortNormalTime = t22 - t21

        if lightingStatic:
            # regular Z culling - cull mask is False for invalid faces and True on valids
            cullMask = ~(cullOn & (faceNormals[:, 2] >= 0))
        else:
            view_dir = lookAt - cameraPoint
            view_dir /= np.linalg.norm(view_dir)
            dot_view = np.einsum(
                'ij,j->i', faceNormals, view_dir
            )   # fancy way of batch dot product
            cullMask = ~(cullOn & (dot_view >= 0))
        # apply culling
        # look "left/right" across each face's Z values and see if any are negative (behind cam)
        behindMask = np.any(faceVertices[:, :, 2] <= 0, axis=1) #remember axis=1 is referring to the 2D matrix gained from indexing
        validMask = cullMask & (~behindMask)   # combine both culls (in the shape of a row vector [True False True..etc.])
        facesVisible = facesSorted[validMask]
        normalsVisible = faceNormals[validMask]
        # calculate light (batch dot product again)
        lightIntensity = np.einsum('ij,j->i', normalsVisible, lightSource)
        lightIntensity = np.clip(lightIntensity, 0.001, 1)

        t23 = time.perf_counter()
        cullAndLightTime = t23-t22
        
        # draw faces
        for faceIdx, face in enumerate(facesVisible):
            valid_indices = face[:, 0][~np.isnan(face[:, 0])].astype(int)
            if len(valid_indices) < 3:
                continue
            projectedXY = projectedPointsXY[valid_indices]
            intensity = lightIntensity[faceIdx]
            color = [int(intensity * 255)] * 3
            try:
                if lightingOn:
                    pygame.draw.polygon(screen, color, projectedXY)
                elif not lightingOn:
                    pygame.draw.polygon(screen, 'grey', projectedXY, 1)
            except Exception as e:
                if debugErrors:
                    print(f'Error drawing polygon {faceIdx}: {e}', flush=True)
        drawTime = time.perf_counter()-t23
        
    renderTime = time.perf_counter() - t2
    t3 = time.perf_counter()
    pygame.display.flip()
    clock.tick(60)  # FPS limit
    displayTime = time.perf_counter() - t3
    frameTotal = time.perf_counter() - frameStart
    fps = 1.0 / frameTotal if frameTotal > 0 else 0.0
    # Print summary every few frames
    frameCount += 1
    if frameCount % 10 == 0:
        if timingPrintOut:
            print(
                f'\rFPS: {fps:6.1f} | '
                f'Input: {inputTime*1000:5.2f} ms | '
                f'Transform: {transformTime*1000:5.2f} ms | '
                f'Point Math: {projectSortNormalTime*1000:5.2f} ms | '
                f'Light/Cull: {cullAndLightTime*1000:5.2f} ms | '
                f'Draw: {drawTime*1000:5.2f} ms | '
                f'Display: {displayTime*1000:5.2f} ms',
                end='',
                flush=True
            )
pygame.quit()
print('\nExiting', flush=True)
