import os
from os import path as osp
import torch
import numpy as np
import trimesh
import tqdm
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Sample a subset of meshes from the dataset using farthest point sampling.')
    parser.add_argument('--data_dir', type=str, required=True, help='Directory containing the mesh files (.obj)')
    parser.add_argument('--source_mesh', type=str, required=True, help='Path to the canonical mesh file (.obj)')
    parser.add_argument('--all_data_file', type=str, required=True, help='Path to save/load the tensor of all vertices')
    parser.add_argument('--sampled_data_file', type=str, required=True, help='Path to save the sampled dataset')
    parser.add_argument('--num_samples', type=int, default=None, help='Number of samples to select (default: all above threshold)')
    return parser.parse_args()

def farthest_point_subset(all_shapes, max_samples=None, threshold=0.1):
    """
    Performs a farthest-point-like sampling of the meshes in all_shapes until
    the maximum distance among the remaining candidates falls below `threshold`.
    all_shapes: torch.Tensor of shape (N, V, 3)
    threshold: float distance cutoff for termination
    Returns a 1D torch.Tensor of selected (keep) indices.
    """
    N, V, d = all_shapes.shape
    all_shapes_flat = all_shapes.view(N, -1).cuda()
    
    keep_idx = [0]
    
    # Compute the Euclidean distances from all meshes to the initial mesh.
    dists = torch.norm(all_shapes_flat - all_shapes_flat[0], dim=1) # shape (N,)
    dists[0] = 0  # Already selected mesh
    
    # Iteratively add the mesh which is farthest from the current set.
    while True:
        if max_samples is not None and len(keep_idx) >= max_samples:
            break

        candidate_val, candidate_idx = torch.max(dists, dim=0)
        if candidate_val < threshold:
            break
        
        print(f"Selected {len(keep_idx)} samples, max dist = {candidate_val.item():.4f}")
        keep_idx.append(candidate_idx.item())
        candidate = all_shapes_flat[candidate_idx].unsqueeze(0)  # Shape (1, V*d)
        new_dists = torch.norm(all_shapes_flat - candidate, dim=1)
        dists = torch.minimum(dists, new_dists)
    
    return torch.tensor(keep_idx)

if __name__ == "__main__":
    args = parse_args()

    dataset_dir = args.data_dir
    canonical_mesh_file = args.source_mesh
    all_data_file = args.all_data_file
    sampled_data_file = args.sampled_data_file
    num_samples = args.num_samples

    canonical_mesh = trimesh.load(canonical_mesh_file, process=False)
    canonical_verts = canonical_mesh.vertices
    canonical_faces = canonical_mesh.faces

    num_verts = canonical_verts.shape[0]
    num_faces = canonical_faces.shape[0]
    
    if not os.path.exists(all_data_file):
        mesh_files = sorted([osp.join(dataset_dir, f) for f in os.listdir(dataset_dir) if f.endswith('.obj')])
        print(f"Found {len(mesh_files)} mesh files.")

        all_vertices = []
        mesh_indices = []
        for mesh_file in tqdm.tqdm(mesh_files):
            mesh = trimesh.load(mesh_file, process=False)
            if mesh.vertices.shape[0] != num_verts or mesh.faces.shape[0] != num_faces:
                print(f"Skipping {mesh_file}: unexpected number of vertices or faces.")
                print(f"Vertices: {mesh.vertices.shape[0]}, Faces: {mesh.faces.shape[0]}")
                continue

            all_vertices.append(mesh.vertices)
            mesh_indices.append(mesh_file)
        
        all_vertices_tensor = torch.tensor(np.stack(all_vertices, axis=0), dtype=torch.float32)


        torch.save(all_vertices_tensor, all_data_file)
    else:
        all_vertices_tensor = torch.load(all_data_file)
    print(f"All vertices tensor shape: {all_vertices_tensor.shape}")

    selected_indices = farthest_point_subset(all_vertices_tensor, max_samples=None, threshold=0.5)
    print(f"Selected {len(selected_indices)} diverse samples.")

    train_num_samples = num_samples if num_samples is not None else len(selected_indices)
    assert len(selected_indices) >= train_num_samples, "Not enough diverse samples selected."

    selected_vertices = all_vertices_tensor[selected_indices[:train_num_samples]]

    data_dict = {
        'src_verts': torch.tensor(canonical_verts, dtype=torch.float32),
        'tar_verts': selected_vertices,
        'faces': torch.tensor(canonical_faces, dtype=torch.long)
    }

    torch.save(data_dict, sampled_data_file)