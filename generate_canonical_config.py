import os
import json
import argparse

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
        "tend": 0.1,
        "dt": 0.025
    }
}


def make_config(template, mesh=None):
    conf = json.loads(json.dumps(template))  # deep copy
    if mesh is not None:
        conf["geometry"][0]["mesh"] = mesh
    return conf


def main():
    parser = argparse.ArgumentParser(description="Generate random JSON configs with random rotations.")
    parser.add_argument("--mesh", type=str, default=None, help="Path to mesh to use.")
    parser.add_argument("--outdir", type=str, default="canonical", help="Output directory for generated JSON file.")
    args = parser.parse_args()

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)

    conf = make_config(TEMPLATE, mesh=args.mesh)

    outpath = os.path.join(args.outdir, "canonical_config.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(conf, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()
