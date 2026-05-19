import os

import argparse
import trimesh
import potpourri3d as pp3d
import numpy as np

def parse_args():
    parser = argparse.ArgumentParser(
        description="Align 3D mesh using Weighted PCA on XZ coordinates."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing input 3D mesh files (.obj, .stl, .ply).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save aligned 3D mesh files.",
    )
    parser.add_argument(
        "--base_mesh",
        type=str,
        required=True,
        help="Path to the base mesh file for reference alignment.",
    )
    parser.add_argument(
        "--idx",
        type=int,
        required=False,
        default=0,
        help="Index of the head vertex for orientation correction.",
    )
    parser.add_argument(
        "--axis",
        type=str,
        required=False,
        default='x',
        help="Main axis to align with the largest variance (default: 'x').",
    )
    parser.add_argument(
        "--rotation",
        action='store_true',
        help="Whether to apply rotation to align the main axis.",
    )
    return parser.parse_args()

def align_mesh_xz_centered(mesh, head_vertex_index=None, weights=None, apply_rotation=True, main_axis='x'):
    """
    Centers the mesh at the origin and rotates it such that the 
    Weighted PCA axes of the X and Z coordinates align with global X and Z.
    
    Args:
        mesh: The trimesh object.
        weights: (Optional) A numpy array of shape (N,) containing mass/area 
                 weights for each vertex.
    """
    vertices = mesh.vertices
    
    # 1. Select X and Z coordinates
    points_xz = vertices[:, [0, 2]]
    
    # 2. Handle Weights (Default to 1.0 if None)
    if weights is None:
        weights = np.ones(len(points_xz))
    
    # 3. Compute Weighted Mean (Center of Mass)
    # shape: (2,)
    weighted_mean = np.average(points_xz, axis=0, weights=weights)
    
    # 4. Center the data at the Origin
    # We apply this to the full 3D vertices immediately
    mesh.vertices -= np.array([weighted_mean[0], 0, weighted_mean[1]])
    
    # Re-extract the centered XZ for PCA calculation
    centered_xz = mesh.vertices[:, [0, 2]]
    
    # 5. Compute Weighted Covariance Matrix
    # Cov = (X - mean).T * W * (X - mean)
    # We use a diagonal weight matrix approach efficiently:
    weights_matrix = np.diag(weights)
    
    # Calculation: (2xN) @ (NxN) @ (Nx2) = (2x2)
    # Note: We use the raw weights here (not normalized) to match standard Cov definitions,
    # though scaling doesn't change eigenvectors.
    cov_matrix = (centered_xz.T @ weights_matrix @ centered_xz) / np.sum(weights)
    
    # 6. Compute Eigenvalues and Eigenvectors
    eig_vals, eig_vecs = np.linalg.eigh(cov_matrix)
    
    # Sort descending (Largest variance maps to X axis)
    if main_axis == 'x':
        sort_indices = np.argsort(eig_vals)[::-1]
    elif main_axis == 'z':
        sort_indices = np.argsort(eig_vals)  # Smallest variance maps to X axis
    else:
        raise ValueError(f"Invalid main_axis: {main_axis}. Must be 'x' or 'z'.")
    principal_components = eig_vecs[:, sort_indices]
    
    if apply_rotation:
        # 7. Construct Rotation Matrix (2D -> 3D)
        # Transpose to get the rotation FROM data TO global axes
        rotation_2d = principal_components.T

        transform_matrix = np.eye(4)
        transform_matrix[0, 0] = rotation_2d[0, 0]
        transform_matrix[0, 2] = rotation_2d[0, 1]
        transform_matrix[2, 0] = rotation_2d[1, 0]
        transform_matrix[2, 2] = rotation_2d[1, 1]
        
        # 8. Apply Rotation
        mesh.apply_transform(transform_matrix)

        # check if most of the vertices are on the left or right of the head vertex
        if head_vertex_index is not None:
            if main_axis == 'x':
                head_x = mesh.vertices[head_vertex_index, 0]
                left_count = np.sum(mesh.vertices[:, 0] > head_x)

                if left_count < 0.8 * len(mesh.vertices):
                    # print('rotate')
                    # rotate 180 degrees around Y axis
                    rotation_180 = np.eye(4)
                    rotation_180[0, 0] = -1
                    rotation_180[2, 2] = -1
                    mesh.apply_transform(rotation_180)
            elif main_axis == 'z':
                head_z = mesh.vertices[head_vertex_index, 2]
                
                # Count vertices "behind" the head along the Z axis
                back_count = np.sum(mesh.vertices[:, 2] < head_z)

                # If the majority of the mesh is NOT behind the head vertex, flip it.
                if back_count < 0.8 * len(mesh.vertices):
                    # Rotate 180 degrees around Y axis (Flips X and Z)
                    rotation_180 = np.eye(4)
                    rotation_180[0, 0] = -1
                    rotation_180[2, 2] = -1
                    mesh.apply_transform(rotation_180)
            else:
                raise ValueError(f"Invalid main_axis: {main_axis}. Must be 'x' or 'z'.")
    return mesh

def main():

    args = parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_mesh = trimesh.load(args.base_mesh, process=False)
    verts_np, faces_np = base_mesh.vertices, base_mesh.faces
    massvec_np = pp3d.vertex_areas(verts_np, faces_np)

    head_vertex_index = args.idx
    main_axis = args.axis
    apply_rotation = args.rotation

    mesh_files_list = sorted(os.listdir(input_dir))

    for filename in mesh_files_list:
        if filename.lower().endswith(('.obj', '.stl', '.ply')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            print(f"Processing: {filename}")
            
            mesh = trimesh.load(input_path, process=False)
            try:
                mesh = align_mesh_xz_centered(mesh, head_vertex_index=head_vertex_index, weights=massvec_np, apply_rotation=apply_rotation, main_axis=main_axis)
                mesh.export(output_path)
            except Exception as e:
                print(f"Failed to process {filename}: {e}")

if __name__ == "__main__":
    main()