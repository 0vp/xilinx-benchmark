source /home/centos/src/project_data/aws-fpga/vitis_setup.sh
source /home/centos/src/project_data/aws-fpga/vitis_runtime_setup.sh

declare -a PROJECTS=("xrt_cpu_to_gmem" "ocl_cpu_to_gmem" "ocl_cpu_to_gmem_rw" "xrt_cpu_to_gmem_rw" "ocl_fpga_to_gmem" "ocl_fpga_to_host")
declare -a EXECUTABLES=("hello_world_xrt -x" "hello_world" "hello_world" "hello_world_xrt -x" "hello_world" "host_memory_simple.exe")
declare -a XCLBINS=("vadd.awsxclbin" "vadd.awsxclbin" "vadd.awsxclbin" "vadd.awsxclbin" "vadd.awsxclbin" "krnl_vadd.awsxclbin")

SCRIPT_START_TIME=$(date +"%F_%T")

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

for i in $(seq 0 3); do
    PROJECT=${PROJECTS[$i]}
    EXECUTABLE=${EXECUTABLES[$i]}
    XCLBIN=${XCLBINS[$i]}

    mkdir -p ../logs
    LOG_FILE="../logs/hw_"$PROJECT"_$SCRIPT_START_TIME.log"

    # redirect all output to log file
    exec > $LOG_FILE 2>&1

    # print the log header
    header

    # copy over the executable into compile_target
    mkdir -p compile_target
    MESSAGE="Copying over the template project..."; log_message
    cp -r ./$PROJECT/* ./compile_target

    MESSAGE="Going into compile_target..."; log_message
    cd compile_target

    MESSAGE="Making executable executable..."; log_message
    chmod +x "${EXECUTABLE% -x}"

    MESSAGE="Running executable..."; log_message
    ./$EXECUTABLE $XCLBIN

    MESSAGE="Returning to src/..."; log_message
    cd ..

    MESSAGE="Removing compile_target..."; log_message
    rm -rf compile_target
done