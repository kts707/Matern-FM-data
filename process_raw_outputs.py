import os
import numpy as np

import meshio
import argparse
import shutil

def parse_args():
    parser = argparse.ArgumentParser(
        description="Process raw VTU outputs to extract output meshes."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Directory containing input VTU files."
    )
    parser.add_argument(
        "--final_result_dir",
        type=str,
        required=True,
        help="Directory to save final OBJ files."
    )
    parser.add_argument(
        "--raw_results_dir",
        type=str,
        required=True,
        help="Directory to save raw results."
    )
    return parser.parse_args()

def compute_stitching_map(points, cells, decimals=7):
    """
    Computes the stitching map once using a template mesh.
    """
    # 1. Round to handle tolerance
    rounded_points = np.round(points, decimals=decimals)
    
    # 2. Get unique indices and the inverse map
    # return_index=True gives us the indices of the *first* occurrence of each unique point
    _, unique_indices, inverse_map = np.unique(
        rounded_points, 
        axis=0, 
        return_index=True, 
        return_inverse=True
    )
    
    # 3. Sort the unique indices array itself to get the correct, stable order
    # The indices array (unique_indices) holds the original position of the unique points.
    # We use argsort to find the order that sorts 'unique_indices' by its values.
    # This gives us a map from the *lexicographical* order (the default np.unique output) 
    # back to the *original occurrence* order.
    original_order_sort_indices = np.argsort(unique_indices)

    # 4. Apply this ordering to the inverse map
    # We only need to adjust the inverse map (the stitching topology)
    # to reference the points in the new, stable order.
    # The 'stitched_cells' (your topology) must now reference the indices of the
    # unique points in the desired stable order.
    # Inverse map references the lexicographically sorted array (unique_points_sorted).
    # original_order_sort_indices[inverse_map] maps the original inverse indices
    # to the new, stable indices.
    reordered_inverse_map = np.argsort(original_order_sort_indices)[inverse_map]
    
    # 5. Pre-compute the stitched cells using the reordered map
    stitched_cells = reordered_inverse_map[cells]
    
    # 6. The recover_indices must also be in the stable order
    # We take the unique indices (first occurrence) and order them based on step 3.
    recover_indices = unique_indices[original_order_sort_indices]
    
    return recover_indices, stitched_cells
    # return unique_indices, stitched_cells

def extract_boundary_triangles(tets):
    """
    Extracts the boundary surface (skin) of a tetrahedral mesh.
    
    Winding Order Note:
    Assuming positive volume tetrahedra (0-1-2 is CCW base, 3 is peak),
    the standard outward faces are:
    - Base: (0, 2, 1)
    - Side: (0, 1, 3)
    - Side: (1, 2, 3)
    - Side: (2, 0, 3)
    """
    cols = [[0, 2, 1], [0, 1, 3], [1, 2, 3], [2, 0, 3]]
    all_faces = tets[:, cols].reshape(-1, 3)
    
    # Sort indices to find duplicates regardless of winding (e.g. 1-2-3 vs 3-2-1)
    sorted_faces = np.sort(all_faces, axis=1)
    
    _, unique_indices, counts = np.unique(sorted_faces, axis=0, return_index=True, return_counts=True)
    
    # Select faces that appear exactly once (the boundary)
    # We select from 'all_faces' to preserve the correct outward winding order
    boundary_faces = all_faces[unique_indices[counts == 1]]
    
    return boundary_faces

def main():
    args = parse_args()
    input_dir = args.input_dir

    # gather all the .vtu files in sorted idx order "step_idx.vtu"
    vtu_files = sorted([f for f in os.listdir(input_dir) if f.endswith(".vtu")], 
                       key=lambda x: int(x.split("_")[-1].split(".vtu")[0]))
    
    if len(vtu_files) <= 80:
        # delete the input_dir
        shutil.rmtree(input_dir)
        raise ValueError("Simulation failed: not enough VTU files.")

    # load the first .vtu file
    mesh_first_frame = meshio.read(os.path.join(input_dir, vtu_files[0]))

    body_ids = mesh_first_frame.point_data['body_ids']
    mask = (body_ids == 1)
    sel_idx = np.nonzero(mask)[0]
    print("Selected point indices for body id 1:", sel_idx)

    unstitched_points = mesh_first_frame.points[sel_idx]
    unstitched_cells = mesh_first_frame.get_cells_type("tetra")

    # compute stitching map
    recover_indices, stitched_cells = compute_stitching_map(unstitched_points, unstitched_cells)

    # compute the boundary triangles
    boundary_triangles = extract_boundary_triangles(stitched_cells)
    tri_cells_list = [("triangle", boundary_triangles.astype(int))]

    mesh = meshio.read(os.path.join(input_dir, vtu_files[-1]))

    sol = mesh.point_data['solution'][sel_idx]

    unstitched_points_displaced = unstitched_points + sol

    recovered_points_displaced = unstitched_points_displaced[recover_indices]
    
    # copy the last frame .obj file to the final_result_dir
    if not os.path.exists(args.final_result_dir):
        os.makedirs(args.final_result_dir, exist_ok=True)
    
    zips_saving_dir = args.raw_results_dir
    if not os.path.exists(zips_saving_dir):
        os.makedirs(zips_saving_dir, exist_ok=True)

    exp_name = os.path.basename(os.path.normpath(input_dir))

    final_obj_path = os.path.join(args.final_result_dir, f"{exp_name}.obj")

    meshio.write_points_cells(
        final_obj_path,
        recovered_points_displaced,
        tri_cells_list
    )

    # zip the input_dir and output_dir into a .zip file such that when unzipped they produce folders named "{exp_name}_raw_outputs" and "{exp_name}_processed_outputs"
    shutil.make_archive(os.path.join(zips_saving_dir, f"{exp_name}_raw_outputs"), 'zip', input_dir)

    # delete the input_dir and output_dir
    shutil.rmtree(input_dir)




if __name__ == "__main__":
    main()