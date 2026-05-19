#!/bin/bash

# run simulations for all config files in the specifized directory
CFG_DIR=$1
RAW_OUT_DIR=$2
ALL_RESULTS_DIR=$3


for CFG_FILE in "$CFG_DIR"/*; do
  if [ -f "$CFG_FILE" ]; then
    CFG_FILENAME=$(basename -- "$CFG_FILE")
    EXP_NAME="${CFG_FILENAME%.*}"
    OUT_DIR="$RAW_OUT_DIR/$EXP_NAME"

    SIM_CMD="./PolyFEM_bin -j $CFG_FILE -o $OUT_DIR"
    echo "Running simulation for $CFG_FILE -> $OUT_DIR"

    eval $SIM_CMD

    python process_raw_outputs.py --input_dir $OUT_DIR --final_result_dir $ALL_RESULTS_DIR --raw_results_dir $RAW_OUT_DIR
  fi

done