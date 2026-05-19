import os

import meshio

import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Normalize meshes in the input dir."
    )
    parser.add_argument(
        "--mesh_dir",
        type=str,
        required=True,
        help="Directory containing input mesh files."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save normalized mesh files."
    )
    return parser.parse_args()

def main():

    args = parse_args()

    mesh_dir = args.mesh_dir
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    # for each .msh tet mesh, normalize to unit cube cntered at origin
    for filename in os.listdir(mesh_dir):
        if not filename.endswith(".msh"):
            continue

        mesh_path = os.path.join(mesh_dir, filename)
        mesh = meshio.read(mesh_path)

        points = mesh.points
        cells = mesh.get_cells_type("tetra")

        # scale the longest side to unit length and center at origin
        min_coords = points.min(axis=0)
        max_coords = points.max(axis=0)
        center = (min_coords + max_coords) / 2.0
        scale = (max_coords - min_coords).max()
        normalized_points = (points - center) / scale

        print(f"Normalized mesh {filename}: center {center}, scale {scale}")

        # save the mesh with normalized points
        normalized_mesh = meshio.Mesh(
            points=normalized_points,
            cells={"tetra": cells}
        )

        output_path = os.path.join(output_dir, filename)
        meshio.write(
            output_path,
            normalized_mesh,
            file_format="gmsh22",
            binary=False
        )
        print(f"Normalized mesh saved to {output_path}")


if __name__ == "__main__":
    main()