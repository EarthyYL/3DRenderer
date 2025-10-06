try: import numpy as np
except ModuleNotFoundError:
    print("numpy not found, exiting", flush=True)
    exit()
try: import pygame
except ModuleNotFoundError:
    pygame = None
    print("pygame not found, display will not work", flush=True)
try: import tkinter as tk
except ModuleNotFoundError:
    tk = None
    print("tkinter not found, file dialogs will not work", flush=True)
import time
from tkinter.filedialog import askopenfilename
import debug_tools
debugErrors=True
def fileBrowse(): #file dialog function
    global filePath
    filePath = askopenfilename()
    if filePath:
        if filePath.lower().endswith('.obj'):
            button.config(text=filePath)
            close=tk.Button(root,text="Render",command=root.destroy)
            close.pack(pady=10)
        else:
            button.config(text="File must be .obj")
#tkinter root for file dialog
root=tk.Tk()
button=tk.Button(root,text="Browse for OBJ file",command=fileBrowse)
button.pack(pady=20)
root.mainloop()
#parse obj file
with open(filePath, 'r') as file: #parser body
    print('File Opened Successfully', flush=True)
    startTime = time.perf_counter()
    faces=[]
    maxVertices=0
    for line in file:
        try:
            if line.startswith('v '):  # vertex line
                parts = line.strip().split()
                vertex = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
                vertices = vertex if 'vertices' not in locals() else np.vstack((vertices, vertex))
            if line.startswith('vn '):  # vertex normal line
                parts = line.strip().split()
                normal = np.array([float(parts[1]), float(parts[2]), float(parts[3])])
                normals = normal if 'normals' not in locals() else np.vstack((normals, normal))
            if line.startswith('f '): # face line
                    parts = line.strip().split()[1:]
                    # parse vertex/texture/normal indices
                    face = np.full((len(parts), 3), np.nan)
                    for j, p in enumerate(parts):
                        vals = p.split('/')
                        #WE CONVERT TO 0-BASED INDEXING HERE
                        face[j, 0] = int(vals[0])-1 if vals[0] else np.nan #grab indexes from face line and handle missing vals
                        face[j, 1] = int(vals[1])-1 if len(vals) > 1 and vals[1] else np.nan #make sure not out of range
                        face[j, 2] = int(vals[2])-1 if len(vals) > 2 and vals[2] else np.nan
                    faces.append(face) # add indices to list of faces
                    maxVertices = max(maxVertices, face.shape[0]) #track max vertices in face
        except Exception as e:
            if debugErrors:
                print(f"Error parsing line: {line.strip()} - {e}", flush=True)
    # Convert faces list to a 3D numpy array, padding with NaNs where necessary
    facesArray = np.full((len(faces), maxVertices, 3), np.nan)
    for i, face in enumerate(faces): 
        facesArray[i, :face.shape[0], :] = face #fill in face data
    #remember, we convert from 1-based to 0-based indexing when reading
    #1 dimension is faces, 2 dimension is each vertex in face, 3 dimension is index of v/vt/vn
    centerPoint=np.array([np.mean(vertices[:,0]),np.mean(vertices[:,1]),np.mean(vertices[:,2])]) #find center of object
    print('File Closed Successfully', flush=True)
    endTime = time.perf_counter()
    print(f"{'Processing time'}: {endTime - startTime:.4f} seconds", flush=True)
debug_tools.writeFacesArrayToFile(facesArray, "debug_output.txt") #write faces array to file for debugging
#functions
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
def drawPoints(points, f): #f is focal length in pixels
    screen_center_x = 640 #set center of screen this is for 1280x720
    screen_center_y = 360
    for point in points: #iterate through points
        x_cam, y_cam, z_cam = point
        if z_cam <= 0:  # clip points behind camera and off screen
            continue
        # perspective projection
        x_screen = (x_cam / z_cam) * f + screen_center_x
        y_screen = (y_cam / z_cam) * f + screen_center_y
        try:
            pygame.draw.circle(screen, "white", (int(x_screen), int(y_screen)), 2) 
        except Exception as e:
            if debugErrors:
                print(f"Error drawing point at ({x_screen}, {y_screen}): {e}", flush=True)
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
def createSphere(center,radius,step):
    points = []
    for phi in np.arange(0, np.pi + step, step):  # polar angle
        for theta in np.arange(0, 2 * np.pi + step, step):  # azimuthal angle
            x = center[0] + radius * np.sin(phi) * np.cos(theta)
            y = center[1] + radius * np.sin(phi) * np.sin(theta)
            z = center[2] + radius * np.cos(phi)
            points.append([x, y, z])
    return np.array(points)
def createAxes(length,step):
    points = []
    for i in np.arange(0, length + step, step):
        points.append([i, 0, 0])  # X-axis
        points.append([0, i, 0])  # Y-axis
        points.append([0, 0, i])  # Z-axis
    return np.array(points)
    
#main
orbit=False
axesOn=True
boundaryCubeOn=False
objScale=5
drawMesh=False
focalLength=500
cullOn=True
#define points
surfacePoints=vertices*objScale
rotationMatrix90DegX=np.array([[1,0,0],[0, 0, -1],[0,1,0]]) #rotate 90 deg around x axis to convert from obj coord system to standard
surfacePoints=surfacePoints @ rotationMatrix90DegX.T
if boundaryCubeOn:
    cube=createCube(np.array([0,0,0]),100,1)
    surfacePoints=np.vstack((surfacePoints,cube))
if axesOn:
    axes=createAxes(50,1)
    surfacePoints=np.vstack((surfacePoints,axes))
cameraPoint=np.array([50, 50, 100]) + centerPoint
cameraPoint = cameraPoint.astype(float)
lookAt=centerPoint.astype(float)
worldUp=np.array([0,0,-1])
dragMoveSpeed=0.01
moveSpeed=2
dragging=False
zoomSpeed=0.1
meshFill=False
#init for orbits
last_drag_vec = np.array([0.0, 0.0, 0.0])   # world-space drag vector
angularVelocity = 0.0                      # radians per frame
axisOfRot = np.array([0.0, 0.0, 1.0])       # fallback axis
damping = 0.95                              # inertia damping per frame (0..1) (unused)
orbitRadius = np.linalg.norm(cameraPoint - lookAt)
shiftHeld=False
#pygame display
pygame.init()
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
print('Opening visualization window', flush=True)
while running:
    pressed = pygame.key.get_pressed()   #for holding key behavior
    xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
    if pressed[pygame.K_LSHIFT]: #shift toggle
        shiftHeld=True
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT:#shift toggle
                shiftHeld=False
        elif event.type == pygame.MOUSEBUTTONDOWN:#start drag
            if event.button == 1:  
                dragging = True 
                orbit=False   
        elif event.type == pygame.MOUSEBUTTONUP: #stop drag
            if event.button == 1:
                dragging=False  
                if angularVelocity <= 1e-6:
                    orbit = False
                else:
                    orbit = True
                    axisOfOrbit=axisOfRot
                    orbitVelocity=angularVelocity
        elif event.type == pygame.MOUSEMOTION: #mouse drag to rotate
            if dragging and not shiftHeld:
                #get movement and axes of camera
                dx,dy = event.rel #screen space drag
                xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
                dragWorld = -dx*xCam+(-dy)*yCam #y is inverted for pygame inverted axis
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
                worldUp = rotatePoint(worldUp,angularVelocity,axisOfRot)
            elif dragging and shiftHeld: #pan
                dx,dy = event.rel #screen space drag
                cameraPoint += -dx*xCam+(-dy)*yCam #y is inverted for pygame inverted axis
                lookAt += -dx*xCam+(-dy)*yCam
        elif event.type == pygame.MOUSEWHEEL: #zoom in/out
            if event.y == 1:
                cameraPoint = cameraPoint - (cameraPoint - lookAt)*zoomSpeed
            elif event.y == -1:
                cameraPoint = cameraPoint + (cameraPoint - lookAt)*zoomSpeed
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: #reset
                lookAt=centerPoint.astype(float)
            if event.key == pygame.K_BACKSPACE: #close
                running = False
            if event.key == pygame.K_m: #toggle mesh
                drawMesh = not drawMesh     
    if pressed[pygame.K_d]: 
        xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
        cameraPoint += xCam * moveSpeed
        lookAt += xCam * moveSpeed
    if pressed[pygame.K_a]: 
        xCam, yCam, zCam = getAxes(cameraPoint,lookAt,worldUp)
        cameraPoint -= xCam * moveSpeed
        lookAt -= xCam * moveSpeed
    screen.fill("black")
    if orbit:
        #compute rotation
        pass  
    camPoints = worldToCamera(surfacePoints,cameraPoint,lookAt,worldUp)
    
    if not drawMesh:  
        drawPoints(camPoints, focalLength)
    if drawMesh:
        for face in facesArray: #vertexes and the respective indices for each face
            #index into camPoints using vertex indices to find face vertices in cam perspective
            validIndices = face[:, 0][~np.isnan(face[:, 0])].astype(int) #filters out NaNs and converts to int
            faceCam = camPoints[validIndices] #faceCam is now a list of coordinates x, y, z in cam space
            # compute face normal in camera space
            v1 = faceCam[1] - faceCam[0]
            v2 = faceCam[2] - faceCam[0]
            faceNormal = np.cross(v1, v2)
            faceNormal = faceNormal / np.linalg.norm(faceNormal)
            #cull if facing away
            if cullOn and faceNormal[2] >= 0:
                continue
            if (np.any(faceCam[:, 2] <= 0)) | (len(validIndices)<=2):  #skip faces with vertices behind camera
                continue
            projected = [] #reset list once a new face is chosen
            for vertex in faceCam:
                xVertexCam, yVertexCam, zVertexCam = vertex
                xScreen = (xVertexCam / zVertexCam) * focalLength + 640 #perspective projection
                yScreen = (yVertexCam / zVertexCam) * focalLength + 360
                projected.append((int(xScreen), int(yScreen)))
            if len(projected) >= 2:
                try:
                    pygame.draw.polygon(screen, "grey", projected, 1)
                except Exception as e:
                    if debugErrors:
                        print(f"Error drawing polygon with points {projected}: {e}", flush=True)
    pygame.display.flip()
    clock.tick(60)  #FPS limit
    fps = int(clock.get_fps())
    print(f"FPS: {fps}", end='\r', flush=True)
pygame.quit()
print("Exiting", flush=True)
