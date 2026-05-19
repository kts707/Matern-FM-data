import panopti
import numpy as np
import trimesh # only for io

import argparse


parser = argparse.ArgumentParser(description='Interactive viewer for meshes')
parser.add_argument('--mesh1', type=str, required=True, help='Path to the first mesh file')
parser.add_argument('--mesh2', type=str, required=False, help='Path to the second mesh file')
parser.add_argument('--idx', type=int, required=False, default=0, help='Index of the vertex to highlight')
args = parser.parse_args()

viewer = panopti.connect(server_url="http://localhost:8080", viewer_id='client') 

mesh = trimesh.load(args.mesh1)

verts, faces = mesh.vertices, mesh.faces

index = args.idx

vertex_colors = np.zeros_like(verts)

# set the color of all vertices to be [0.11, 0.39, 0.89]
vertex_colors[:] = (np.array([0.11, 0.39, 0.89]) * 255).astype(np.uint8)

vertex_colors[index] = np.array([255, 0, 0])  # Red color for the specific vertex

viewer.add_mesh(
    vertices=verts,
    faces=faces,
    name="Mesh1",
    vertex_colors=vertex_colors
)

if args.mesh2:
    mesh2 = trimesh.load(args.mesh2)
    verts2, faces2 = mesh2.vertices, mesh2.faces

    viewer.add_mesh(
        vertices=verts2,
        faces=faces2,
        name="Mesh2",
        vertex_colors=vertex_colors
    )


viewer.hold() # prevent the script from terminating