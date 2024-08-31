#!/bin/bash

# This script is used to compile the examples and run them only in hardware emulation mode.

source /home/centos/src/project_data/aws-fpga/vitis_setup.sh
source /home/centos/src/project_data/aws-fpga/vitis_runtime_setup.sh

PLATFORM=$AWS_PLATFORM
PLATFORM_NAME=$(echo "${AWS_PLATFORM##*/}" | sed 's/\.xpfm$//')
EMULATION_MODE="hw"
SCRIPT_START_TIME=$(date +"%F_%T")
MESSAGE=""

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
    echo "$DATETIME INFO: $MESSAGE"
}

log_error() {
    DATETIME=$(date +"%F %T")
    echo "$DATETIME ERROR: $MESSAGE"
}

# Function to be run asynchronously for each project
async_project() {
    local PROJECT=$1
    local EXECUTABLE=$2
    local XCLBIN=$3
    local SCRIPT_TIME=$4

    # make compile directory & set log file
    mkdir $PROJECT
    mkdir -p ../logs
    LOG_FILE="../logs/compile_"$PROJECT"_"$SCRIPT_TIME".log"

    # redirect all output to log file
    exec > $LOG_FILE 2>&1

    # print the log header
    header

    # copy over the template project and update the data size
    MESSAGE="Copying over the template project..."; log_message
    cp -r ./template/$PROJECT/* ./$PROJECT

    # update the data size
    MESSAGE="Running update_data_size.py..."; log_message
    python ./update_data_size.py ./$PROJECT $PROJECT

    # compile the example
    MESSAGE="Compiling the example..."; log_message
    cd ./$PROJECT
    # make cleanall
    make all PLATFORM=$PLATFORM TARGET=$EMULATION_MODE
}

echo "Compilation started."

pids=()
for i in $(seq 0 3); do
    PROJECT=${PROJECTS[$i]}
    EXECUTABLE=${EXECUTABLES[$i]}
    XCLBIN=${XCLBINS[$i]}

    # Run the function in the background
    async_project "$PROJECT" "$EXECUTABLE" "$XCLBIN" "$SCRIPT_START_TIME" &
    
    # Store the PID of the background process
    pids+=($!)
done

# wait for all processes to complete
for pid in "${pids[@]}"; do
    wait $pid
done

# running examples cannot be async
if [ "$EMULATION_MODE" = "hw_emu" ]; then
    for i in $(seq 0 3); do
        PROJECT=${PROJECTS[$i]}
        EXECUTABLE=${EXECUTABLES[$i]}
        XCLBIN=${XCLBINS[$i]}

        # Run each example
        LOG_FILE="../logs/compile_"$PROJECT"_"$SCRIPT_START_TIME".log"

        # redirect all output to log file
        exec >> $LOG_FILE 2>&1

        # navigate to directory
        cd $PROJECT

        # run the example
        MESSAGE="Setting up the emulation environment..."; log_message
        emconfigutil --platform $PLATFORM
        export XCL_EMULATION_MODE=$EMULATION_MODE

        MESSAGE="Running the example..."; log_message
        ./$EXECUTABLE ./build_dir.$EMULATION_MODE.$PLATFORM_NAME/vadd.xclbin

        # go back to src dir
        cd ../
    done
fi

exec 1>&- 2>&-
exec 1>/dev/tty 2>&1
echo "Compilation completed."