import os
import tqdm
import trimesh

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Save largest connected component of meshes in a directory")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory containing input meshes")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save output meshes")
    return parser.parse_args()

def save_largest_component(input_mesh_path, output_mesh_path):
    mesh = trimesh.load(input_mesh_path, process=False)
    components = mesh.split(only_watertight=False)
    largest_component = max(components, key=lambda m: m.vertices.shape[0])
    
    if not largest_component.is_watertight:
        largest_component.remove_unreferenced_vertices()
        print(f"Warning: The largest component in {input_mesh_path} is not watertight.")
    
    largest_component.export(output_mesh_path)

if __name__ == "__main__":
    
    args = parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    mesh_files = sorted(os.listdir(input_dir))

    for mesh_file in tqdm.tqdm(mesh_files):
        if not mesh_file.endswith('.obj') and not mesh_file.endswith('.ply'):
            continue
        input_mesh_path = os.path.join(input_dir, mesh_file)
        output_mesh_path = os.path.join(output_dir, mesh_file)
        save_largest_component(input_mesh_path, output_mesh_path)