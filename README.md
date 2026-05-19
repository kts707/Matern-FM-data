# Matern-FM data generation scripts

## What's in this repo?

This codebase contains the data generation scripts for the **datasets of random elastic equilibrium states**, used in [Matérn Noise for Triangulation-Agnostic Flow Matching on Meshes](https://matern-fm.github.io/), by Tianshu Kuai, Arman Maesumi, Daniel Ritchie, and Noam Aigerman, published in ACM Transactions on Graphics (Proceedings of SIGGRAPH 2026).

If you are looking for scripts to create the SMPL dataset (yoga poses) used in our paper, refer to the instructions [here](https://github.com/ArmanMaesumi/poissonnet/tree/master/smplx_data).

## Our preprocessed datasets
Our preprocessed datasets can be downloaded from [here](https://udemontreal-my.sharepoint.com/:f:/g/personal/tianshu_kuai_umontreal_ca/IgDTIysjX7jBQa3RzqXL1TsBAePI1R2l0EUxTkIKThh3CKE?e=bCMkX2). See our [repo](https://github.com/kts707/matern-fm#Datasets) and [paper](link) for more details. 

## Installation

Install [PolyFEM](https://github.com/polyfem/polyfem). Note that the object needs to be a tetrahedral mesh. If your mesh is not tetrahedral (e.g., a triangle mesh), we recommend setting up [fTetWild](https://github.com/wildmeshing/fTetWild) to convert it to a tetrahedral mesh. Put their executables (`PolyFEM_bin` and `FloatTetwild_bin`) in this directory. 

Install python dependencies:
```
# torch (other versions also work)
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu121

# other dependencies
pip install trimesh meshio potpourri3d panopti
```


## Prepare a tetrahedral mesh for simulation

Run `fTetWild` to convert your mesh to a tetrahedral mesh (`.msh` file) and put it under the `data` folder. Then normalize it to be within a unit cube by running:
```
python normalize_tet_meshes.py --mesh_dir <msh_mesh_dir> --output_dir <output_msh_mesh_dir>
```

We provide two example data folders (each contains a normalized tetrahedral mesh): `data/stanford_bunny` and `data/fish`. The instructions in the following sections are based on the Stanford Bunny. Feel free to swap it with your own mesh. 

## Run physical simulations

### Generate configs for simulations

We will run 40k simulations of dropping the object with random initial orientations and angular velocities. Start by generating the configs for all 40k simulations:
```
# python generate_sim_configs.py \
    --mesh <path_to_msh> \
    --num 40000 \
    --outdir <path_to_saving_dir> \
    --seed 0

# stanford bunny example
python generate_sim_configs.py \
    --mesh data/stanford_bunny/stanford_bunny.msh \
    --num 40000 \
    --outdir configs/stanford_bunny \
    --seed 0
```

### Run simulations and collect the random elastic object's equilibrium states
```
# bash run_batch_simulations.sh <config_dir> <raw_output_dir> <final_output_dir>

# stanford bunny example
bash run_batch_simulations.sh \
    configs/stanford_bunny \
    results/stanford_bunny_raw_results \
    results/stanford_bunny
```

### Ensure that each deformed mesh contains only a single connected component
```
# python save_largest_component.py \
    --input_dir <final_output_dir> \
    --output_dir <final_output_dir_single_component>

# stanford bunny example
python save_largest_component.py \
    --input_dir results/stanford_bunny \
    --output_dir results/stanford_bunny_single_component
```

### Generate a canonical mesh as the source mesh
Generate a config for saving the canonical mesh:
```
# python generate_canonical_config.py --mesh <path_to_msh> --outdir <path_to_saving_dir>

# stanford bunny example
python generate_canonical_config.py \
    --mesh data/stanford_bunny/stanford_bunny.msh \
    --outdir configs/stanford_bunny_canonical
```


Run a dummy simulation and save the raw canonical mesh:
```
# bash save_canonical_mesh.sh <config_dir> <raw_output_dir> <final_output_dir>

# stanford bunny example
bash save_canonical_mesh.sh \
    configs/stanford_bunny_canonical/canonical_config.json \
    results/stanford_bunny_canonical_raw_results \
    results/stanford_bunny_canonical_mesh/canonical.obj
```


Ensure that the canonical mesh contains a single connected component:
```
# python save_largest_component.py \
    --input_dir <final_output_dir> \
    --output_dir <final_output_dir_single_component>

# stanford bunny example
python save_largest_component.py \
    --input_dir results/stanford_bunny_canonical_mesh \
    --output_dir results/stanford_bunny_canonical_mesh_single_component
```


## (Optional) Removing global rotations around the y-axis via PCA


### Use an interactive viewer to extract the reference vertex for alignment

Use [panopti](https://github.com/ArmanMaesumi/panopti) to visualize the mesh in an interactive viewer. Its inspection tool enables clicking on the mesh to see the vertex indices of a face. Find the index of the vertex at one end of the mesh (e.g., the leftmost vertex on Stanford Bunny's nose), then run the alignment script using the chosen vertex index and the axis to be aligned with the largest principal component. See [panopti's documentation](https://armanmaesumi.github.io/panopti/getting_started/) for how to run and use the viewer. 

```
# start the server
python -m panopti.run_server --host localhost --port 8080

# once the server is running
# python interactive_viewer.py \
    --mesh1 <canonical_mesh> \
    --mesh2 <deformed_mesh> \
    --idx 2627

# stanford bunny example
python interactive_viewer.py \
    --mesh1 results/stanford_bunny_canonical_mesh_single_component/canonical.obj \
    --mesh2 results/stanford_bunny_single_component/0000000.obj \
    --idx 1553
```

### Run the following script to align the meshes based on the index chosen in the previous step
```
# python pca_align.py \
    --base_mesh <canonical_mesh> \
    --input_dir <input_dir> \
    --output_dir <output_dir> \
    --idx 2627 \
    --axis z \
    --rotation

# stanford bunny example
python pca_align.py \
    --base_mesh results/stanford_bunny_canonical_mesh_single_component/canonical.obj \
    --input_dir results/stanford_bunny_single_component \
    --output_dir results/stanford_bunny_single_component_aligned \
    --idx 1553 \
    --axis x \
    --rotation
```


## Sample diverse deformations via farthest point sampling
```
# sample 20k diverse deformations
# save the sampled data as .pt file

# python sample_dataset.py \
    --source_mesh <canonical_mesh> \
    --data_dir <data_dir> \
    --all_data_file <all_data_file> \
    --sampled_data_file <sampled_data_file> \
    --num_samples 20000

# the data file has the following structure:
# data_dict = {'src_verts': source vertices in (V, 3)
#              'tar_verts': deformed vertices in (N, V, 3)
#              'faces': faces in (F, 3)
# }

# stanford bunny example
python sample_dataset.py \
    --source_mesh results/stanford_bunny_canonical_mesh_single_component/canonical.obj \
    --data_dir results/stanford_bunny_single_component_aligned \
    --all_data_file results/stanford_bunny_single_component_aligned.pt \
    --sampled_data_file results/stanford_bunny_single_component_aligned_diverse_20k.pt \
    --num_samples 20000
```

## Citation
If you find our work or datasets useful in your research, please consider citing it:
```bibtex
@article{kuai2026matern,
author = {Kuai, Tianshu and Maesumi, Arman and Ritchie, Daniel and Aigerman, Noam},
title = {Matérn Noise for Triangulation-Agnostic Flow Matching on Meshes},
year = {2026},
booktitle = {ACM Transactions on Graphics (Proceedings of SIGGRAPH 2026)},
publisher = {Association for Computing Machinery}
}
```

## Acknowledgement
The physical simulation is based on [PolyFEM](https://github.com/polyfem/polyfem), and the tetrahedral meshing is based on [fTetWild](https://github.com/wildmeshing/fTetWild). We use [panopti](https://github.com/ArmanMaesumi/panopti) for interactive mesh visualization. A big thanks to their work and efforts in releasing the code.

## License

This project is under the MIT license. 
