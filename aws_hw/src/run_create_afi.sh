#!/bin/sh

# This script is used to create the AFI for the examples in the projects array.

source /home/centos/src/project_data/aws-fpga/vitis_setup.sh
source /home/centos/src/project_data/aws-fpga/vitis_runtime_setup.sh

PLATFORM=$AWS_PLATFORM
PLATFORM_NAME=$(echo "${AWS_PLATFORM##*/}" | sed 's/\.xpfm$//')
SCRIPT_START_TIME=$(date +"%Y%m%d_%H%M%S")
BACKUP_FOLDER="../.backup/src"

S3_BUCKET_NAME="shir-fpga-awsxclbin"    # name of your s3 bucket
S3_DCP="dcp"                            # name of the dcp folder
S3_LOGS="logs"                          # name of the logs folder

declare -a PROJECTS=("xrt_cpu_to_gmem" "ocl_cpu_to_gmem" "ocl_cpu_to_gmem_rw" "xrt_cpu_to_gmem_rw" "ocl_fpga_to_gmem" "ocl_fpga_to_host")
declare -a EXECUTABLES=("hello_world_xrt -x" "hello_world" "hello_world" "hello_world_xrt -x" "hello_world" "host_memory_simple.exe")
declare -a XCLBINS=("vadd.xclbin" "vadd.xclbin" "vadd.xclbin" "vadd.xclbin" "vadd.xclbin" "krnl_vadd.xclbin")

header() {
    echo "DATETIME: $(date +"%F %T")"
    echo "GIT COMMIT: $(git rev-parse HEAD)"
    echo "XILINX VITIS VERSION: $(v++ --version)"
}

log_message() {
    DATETIME=$(date +"%F %T")
    MESSAGE=$1
    echo "$DATETIME INFO: $MESSAGE"
}

log_error() {
    DATETIME=$(date +"%F %T")
    MESSAGE=$1
    echo "$DATETIME ERROR: $MESSAGE"
}

async_create() {
    PROJECT=$1
    EXECUTABLE=$2
    XCLBIN=$3

    cd $BACKUP_FOLDER/$PROJECT/

    # create logs folder & file
    mkdir -p ../../../logs
    LOG_FILE="../../../logs/afi_"$PROJECT"_"$SCRIPT_START_TIME".log"

    # redirect all output to log file
    exec > $LOG_FILE 2>&1

    # print the log header
    header

    # get project dir relative to run_create_afi.sh
    PROJECT_DIR=./build_dir.hw.$PLATFORM_NAME     
    XCLBIN=$PROJECT_DIR/$XCLBIN

    # create AFI
    log_message "Creating Vitis AFI..."
    $VITIS_DIR/tools/create_vitis_afi.sh -xclbin=$XCLBIN \
        -o=vadd \
        -s3_bucket=$S3_BUCKET_NAME -s3_dcp_key=$S3_DCP -s3_logs_key=$S3_LOGS
}

pids=()
for i in $(seq 0 3); do
    PROJECT=${PROJECTS[$i]}
    EXECUTABLE=${EXECUTABLES[$i]}
    XCLBIN=${XCLBINS[$i]}

    # async create AFI
    log_message "Executing for project: $PROJECT..."
    async_create "$PROJECT" "$EXECUTABLE" "$XCLBIN" &

    pids+=($!)
done

# wait for all processes to complete
for pid in "${pids[@]}"; do
    wait $pid
done