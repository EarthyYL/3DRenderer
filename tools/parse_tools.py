import numpy as np
import time


def parseOBJFile(filePath: str, debugErrors: bool): #defunctional, kept for reference

    with open(filePath, 'r') as file: 
        print('File Opened Successfully', flush=True)
        startTime = time.perf_counter()
        facesList = []
        maxVertices = 0

        for line in file:
            try:
                if line.startswith('v '):  # vertex line
                    parts = line.strip().split()
                    vertex = np.array(
                        [float(parts[1]), float(parts[2]), float(parts[3])]
                    )
                    vertices = (
                        vertex
                        if 'vertices' not in locals()
                        else np.vstack((vertices, vertex))
                    )
                if line.startswith('vn '):  # vertex normal line
                    parts = line.strip().split()
                    normal = np.array(
                        [float(parts[1]), float(parts[2]), float(parts[3])]
                    )
                    normals = (
                        normal
                        if 'normals' not in locals()
                        else np.vstack((normals, normal))
                    )

                if line.startswith('f '):   #face line
                    parts = line.strip().split()[1:] #get indices
                    face = np.full((len(parts), 3), np.nan) #initalize list
                    for j, p in enumerate(parts):
                        vals = p.split('/')
                        # grab indices from face line and handle missing vals
                        face[j, 0] = (
                            int(vals[0]) - 1 if vals[0] else np.nan
                        )   
                        face[j, 1] = (
                            int(vals[1]) - 1
                            if len(vals) > 1 and vals[1]
                            else np.nan
                        ) 
                        face[j, 2] = (
                            int(vals[2]) - 1
                            if len(vals) > 2 and vals[2]
                            else np.nan
                        )
                    facesList.append(face)   # add indices to list of faces
                    maxVertices = max(
                        maxVertices, face.shape[0]
                    )   # track max vertices in face
            except Exception as e:
                if debugErrors:
                    print(
                        f'Error parsing line: {line.strip()} - {e}', flush=True
                    )
        # convert faces list to a 3D array and pad with NaNs to maintain dimensions
        facesArray = np.full((len(facesList), maxVertices, 3), np.nan)
        for i, face in enumerate(facesList):
            facesArray[i, : face.shape[0], :] = face   # fill in face data
        # remember, we convert from 1-based to 0-based indexing when reading
        # 1 dimension is faces, 2 dimension is each vertex in face, 3 dimension is index of v/vt/vn
        centerPoint = np.array(
            [
                np.mean(vertices[:, 0]),
                np.mean(vertices[:, 1]),
                np.mean(vertices[:, 2]),
            ]
        )  
        # feedback
        endTime = time.perf_counter()
        print(
            f"{'Processing time'}: {endTime - startTime:.4f} seconds",
            flush=True,
        )
        print('File Closed Successfully', flush=True)
    return vertices.astype(np.float32), normals.astype(np.float32), facesArray, centerPoint.astype(np.float32)
    #array of vertex coords, normal vectors, indices to both, and a central point, respectively
def parseOBJFileTriangulator(filePath: str, debugErrors: bool):
    with open(filePath, 'r') as file: 
        print('File Opened Successfully', flush=True)
        startTime = time.perf_counter()
        facesList = []
        maxVertices = 0

        for line in file:
            try:
                if line.startswith('v '):  # vertex line
                    parts = line.strip().split()
                    vertex = np.array(
                        [float(parts[1]), float(parts[2]), float(parts[3])]
                    )
                    vertices = (
                        vertex
                        if 'vertices' not in locals()
                        else np.vstack((vertices, vertex))
                    )
                if line.startswith('vn '):  # vertex normal line
                    parts = line.strip().split()
                    normal = np.array(
                        [float(parts[1]), float(parts[2]), float(parts[3])]
                    )
                    normals = (
                        normal
                        if 'normals' not in locals()
                        else np.vstack((normals, normal))
                    )
                if line.startswith('f '):   #face line
                    parts = line.strip().split()[1:] #get indices from line 'f v0/vt0/vn0 v1/vt1/vn1 ...'
                    face = np.full((len(parts), 3), np.nan) #initalize/reset face array
                    for j, p in enumerate(parts): #fills face data
                        vals = p.split('/')
                        # grab indices from face line and handle missing vals
                        face[j, 0] = (
                            int(vals[0]) - 1 if vals[0] else -1
                        )   
                        face[j, 1] = (
                            int(vals[1]) - 1
                            if len(vals) > 1 and vals[1]
                            else -1
                        ) 
                        face[j, 2] = (
                            int(vals[2]) - 1
                            if len(vals) > 2 and vals[2]
                            else -1
                        )
                    # triangulation block
                    num_vertices = face.shape[0]
                    if num_vertices < 3:
                    # invalid face, skip
                        if debugErrors:
                            print(f"Skipping invalid face with {num_vertices} vertices", flush=True)
                        continue
                    elif num_vertices == 3:
                        # triangle, add directly
                        facesList.append(face)
                    else:
                        for j in range(1, num_vertices - 1):
                            triangle = np.vstack((face[0], face[j], face[j + 1]))
                            facesList.append(triangle)
            except Exception as e:
                if debugErrors:
                    print(
                        f'Error parsing line: {line.strip()} - {e}', flush=True
                    )
        # convert faces list to a 3D array and pad with NaNs just in case
        maxVertices = 3  # after triangulation, max vertices per face is 3
        facesArray = np.full((len(facesList), maxVertices, 3), np.nan)
        for i, face in enumerate(facesList):
            facesArray[i, : face.shape[0], :] = face   # fill in face data
        # remember, we convert from 1-based to 0-based indexing when reading
        # facesArray shape: (num_triangles, 3, 3)
        # each layer is [[v_index, vt_index, vn_index][v_index, vt_index, vn_index][v_index, vt_index, vn_index]
        centerPoint = np.array(
            [
                np.mean(vertices[:, 0]),
                np.mean(vertices[:, 1]),
                np.mean(vertices[:, 2]),
            ]
        )  
        # feedback
        endTime = time.perf_counter()
        print(
            f"{'Processing time'}: {endTime - startTime:.4f} seconds",
            flush=True,
        )
        print('File Closed Successfully', flush=True)
        print(f"Mesh created with {facesArray.shape[0]} triangles", flush=True)
    return vertices.astype(np.float32), normals.astype(np.float32), facesArray.astype(np.int32), centerPoint.astype(np.float32)
