import numpy as np
def writeFacesArrayToFile(facesArray, fileName):
    with open(fileName, "w") as f:
        f.write(f"# Original shape: {facesArray.shape}\n") #write shape
        for i, slice_2d in enumerate(facesArray):
            f.write(f"# Slice {i}\n")
            np.savetxt(f, slice_2d, delimiter=",", fmt="%.2f")
            f.write("\n") # Add a newline between slices
