#!/bin/bash

# run simulations for all config files in the specified directory
CANONICAL_CONFIG=$1
RAW_OUT_DIR=$2
OUT_FILE=$3

SIM_CMD="./PolyFEM_bin -j $CANONICAL_CONFIG -o $RAW_OUT_DIR"
echo "Running simulation for $CANONICAL_CONFIG -> $RAW_OUT_DIR"

eval $SIM_CMD

python save_canonical_mesh.py --input_dir $RAW_OUT_DIR --output_file $OUT_FILE

rm -rf $RAW_OUT_DIR