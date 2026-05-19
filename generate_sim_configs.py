import os
import json
import argparse
import random

TEMPLATE = {
    "common": "../ipc-defaults.json",
    "geometry": [{
        "mesh": "data/cube.msh",
        "transformation": {
            "translation": [0, 1.5, 0],
            "rotation": [0, 0, 0]
        },
        "volume_selection": 1
    }, {
        "mesh": "data/plane.obj",
        "is_obstacle": True
    }],
    "initial_conditions": {
        "velocity": [{
            "id": 1,
            "value": ["0", "0", "0"]
        }]
    },
    "contact": {
        "friction_coefficient": 2.0
    },
    "materials": {
        "type": "NeoHookean",
        "E": 1e4,
        "nu": 0.4,
        "rho": 1000
    },
    "time": {
        "tend": 3,
        "dt": 0.025
    }
}


def random_rotation(rng):
    """Return [rx, ry, rz] Euler angles sampled uniformly in [0,360) degrees
    if in_radians=True. Order is x, then y, then z.
    """
    return [rng.random() * 360.0 - 180.0,
            rng.random() * 360.0 - 180.0,
            rng.random() * 360.0 - 180.0]

def random_angular_velocity(rng):
    # return angular velocity vector [wx, wy, wz] in multiplier of pi
    # the length of the vector is sampled uniformly in [1.0, 3.0]

    length = rng.uniform(1.0, 3.0)
    wx = rng.uniform(-1.0, 1.0)
    wy = rng.uniform(-1.0, 1.0)
    wz = rng.uniform(-1.0, 1.0)
    norm = (wx**2 + wy**2 + wz**2)**0.5
    
    return [length * wx / norm,
            length * wy / norm,
            length * wz / norm]

def compute_angular_velocity_str(angular_velocity):
    """Given angular_velocity = [wx, wy, wz] in multiplier of pi, return string for velocity field."""
    wx, wy, wz = angular_velocity
    
    # cross product between angular velocity vector and position vector (x,y,z)
    return [f"{wy} * pi * z - {wz} * pi * (y - 1.5)",
            f"{wz} * pi * x - {wx} * pi * z",
            f"{wx} * pi * (y - 1.5) - {wy} * pi * x"]

def make_config(template, mesh=None, E=None, tend=None, dt=None, rotation=None, angular_velocity=None):
    conf = json.loads(json.dumps(template))  # deep copy
    if mesh is not None:
        conf["geometry"][0]["mesh"] = mesh
    if E is not None:
        conf["materials"]["E"] = E
    if tend is not None:
        conf["time"]["tend"] = tend
    if dt is not None:
        conf["time"]["dt"] = dt
    if rotation is not None:
        conf["geometry"][0]["transformation"]["rotation"] = rotation
    if angular_velocity is not None:
        angular_velocity_str = compute_angular_velocity_str(angular_velocity)
        conf["initial_conditions"]["velocity"][0]["value"] = angular_velocity_str
    return conf


def main():
    parser = argparse.ArgumentParser(description="Generate random JSON configs with random rotations.")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of files to generate.")
    parser.add_argument("--mesh", type=str, default=None, help="Path to mesh to use.")
    parser.add_argument("--E", type=float, default=None, help="Young's modulus E to set in materials.")
    parser.add_argument("--tend", type=float, default=None, help="tend value in time section.")
    parser.add_argument("--dt", type=float, default=None, help="dt value in time section.")
    parser.add_argument("--outdir", type=str, default="configs", help="Output directory for generated JSON files.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed (for reproducibility).")
    parser.add_argument("--translation", type=float, nargs=3, metavar=('TX','TY','TZ'),
                        default=None, help="Optional translation override (three floats).")
    parser.add_argument("--disable_angular_velocity", action="store_true", help="Enable random angular velocity")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    os.makedirs(args.outdir, exist_ok=True)

    for i in range(args.num):
        rot = random_rotation(rng)
        if not args.disable_angular_velocity:
            angular_velocity = random_angular_velocity(rng)
        else:
            angular_velocity = None
        conf = make_config(TEMPLATE, mesh=args.mesh, E=args.E, tend=args.tend, dt=args.dt, rotation=rot, angular_velocity=angular_velocity)
        if args.translation is not None:
            conf["geometry"][0]["transformation"]["translation"] = list(args.translation)

        filename = f"{i:07d}.json"
        outpath = os.path.join(args.outdir, filename)
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(conf, f, indent=4, ensure_ascii=False)
        print(f"Wrote {outpath} (rotation = {rot} degrees) (Angular velocity = {angular_velocity} * pi)")

    print(f"Done. {args.num} files written to '{args.outdir}'.")


if __name__ == "__main__":
    main()
