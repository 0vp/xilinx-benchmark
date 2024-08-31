#!/bin/sh

# copies shir-benchmark/src/* to .backup with only the relevant files needed to to run on hw.

declare -a PROJECTS=("xrt_cpu_to_gmem" "ocl_cpu_to_gmem" "ocl_cpu_to_gmem_rw" "xrt_cpu_to_gmem_rw" "ocl_fpga_to_gmem" "ocl_fpga_to_host")

BACKUP_FOLDER="../.backup/src"

async_copy_remove() {
    local PROJECT=$1

    # creates the folder and copies the compiled project files over
    mkdir -p $BACKUP_FOLDER/$PROJECT
    cp -r ./$PROJECT $BACKUP_FOLDER

    # remove unnecessary files that are not needed for execution
    rm -rf $BACKUP_FOLDER/$PROJECT/_x*
    rm -rf $BACKUP_FOLDER/$PROJECT/.ipcache
    rm -rf $BACKUP_FOLDER/$PROJECT/.Xil
    rm -rf $BACKUP_FOLDER/$PROJECT/package.hw
    rm -rf $BACKUP_FOLDER/$PROJECT/src
    rm $BACKUP_FOLDER/$PROJECT/*.log
    rm $BACKUP_FOLDER/$PROJECT/*.rst
    rm $BACKUP_FOLDER/$PROJECT/*.json
    rm $BACKUP_FOLDER/$PROJECT/*.mk
    # rm $BACKUP_FOLDER/$PROJECT/*.ini # needed for ocl_fpga
    rm $BACKUP_FOLDER/$PROJECT/Makefile

    rm $BACKUP_FOLDER/$PROJECT/build_dir.hw.xilinx_aws-vu9p-f1_shell-v04261818_201920_3/*link*
    rm $BACKUP_FOLDER/$PROJECT/build_dir.hw.xilinx_aws-vu9p-f1_shell-v04261818_201920_3/*package*

}

# remove current backup
rm -rf $BACKUP_FOLDER

# create backup folder
mkdir -p $BACKUP_FOLDER

# copy files over
pids=()
for i in $(seq 0 3); do
    PROJECT=${PROJECTS[$i]}

    async_copy_remove "$PROJECT" &
    pids+=($!)
done

# wait for all processes to complete
for pid in "${pids[@]}"; do
    wait $pid
done