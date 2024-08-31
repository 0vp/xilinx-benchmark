# Setup & Execution For OpenCL and XRT Data Transfers Benchmarks on Xilinx FPGA

## Introduction
This test suite is used for benchmarking the bandwidth and latency of data transfers between the cpu and global memory. It focuses on benchmarking the transfer speeds of various APIs (XRT API and OpenCL/OCL) between the host and the FPGA board.

Below, you will find setup and execution instructions to reproduce my results.

Here's the content converted to markdown format:

# Setup

## Local Install

### Operating System

The emulations were run on both CentOS 7.9.2009 and CentOS 8.4.2105. Their respective disk images (.iso) files can be found in the CentOS vault provided by Internet Initiative Japan. A link to the vault can be found here:

[https://ftp.iij.ad.jp/pub/linux/centos-vault/](https://ftp.iij.ad.jp/pub/linux/centos-vault/)

If you plan to install it locally, you will need to save the disk image and then flash it onto a bootable USB with at least 16 GB of storage. To flash it, I recommend using the software [https://rufus.ie/](https://rufus.ie/).

Next, reboot your computer and load into BIOS. Here, you will be able to select to boot from the USB that you flashed. Do so and then follow the setup instructions on the screen to install CentOS. Here is a useful tutorial to help visualize the steps [https://www.youtube.com/watch?v=4viTo4gulQk](https://www.youtube.com/watch?v=4viTo4gulQk).

### Software and Tools

If you plan to run the tests locally, before the tests can be run, the environment needs to be set up. For the following tools, you want to keep the software version consistent. For my emulation and hardware tests, the version of Xilinx tools used was `2021.2`.

Below includes the needed software:

1. Vivado and Vitis, for simpler installation, install the Linux Self-Extracting web installer or the Single-File installer, and then follow the instructions from the installer.

   Vivado:
   [https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools.html](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vivado-design-tools.html)

   Vitis:
   [https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vitis.html](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/vitis.html)

   The default installation of these files is in the `/opt/Xilinx/` folder. If they are not placed there automatically, you will need to copy them over manually.

2. Xilinx Runtime (XRT) and Platform Packages

   For the target platform for emulation, `Alveo U200` was used. However, any of the supported platforms found here [https://xilinx.github.io/Vitis_Accel_Examples/2021.2/html/shells.html](https://xilinx.github.io/Vitis_Accel_Examples/2021.2/html/shells.html) can be used.

   Xilinx Runtime (XRT) & Deployment Target Platform:
   [https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/alveo.html](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/alveo.html)

   The above will provide you with 2 *.rpm files. Ensure that you have admin access and then run the command
   `sudo yum install *.rpm` for each .rpm file.

   The default installation of XRT is in the `/opt/xilinx/` folder, and the target platform can be found under
   `/opt/xilinx/platforms/`. If they are not placed there automatically, you will need to copy them over manually.

3. Ensure that Python >= 2.7.5 is installed by running `python --version`.

   You will also need Python 3.6+ in order to run scripts used to parse python logs and to graph the data.

   For CentOS 7, Python 2.7.5 is installed by default, however, that is not the case for CentOS 8. The latest Python version for CentOS 8 is Python 3.9.6, to install it, run
   `sudo yum install python39`

## AWS Server

If you plan to run the tests on an AWS EC2 F1 Instance, you will need:

1. Setup AWS & AWS Permissions

   Assuming that you already have an AWS account, you will need to:
   1. Setup AWS IAM Permissions for Creating FPGA Images
      Navigate to `IAM` > `Policies` > `Create policy`

      Select Service `EC2`, check the permissions `CreateFpgaImage` and `DescribeFpgaImages`, and for `Resources`, select `All`, then click `Next`. Name the policy and then create it.

      Next, go to `Users` or `User groups`, then add the permissions to your user or group that you belong to.

   2. Setup S3 Bucket for Compiled Target `*.awsxclbin`
      First, install the `AWS CLI`. then,

      Set your credentials (found in your console.aws.amazon.com page), region (us-east-1) and output (json)
      ```
      aws configure
      ```

      Create an S3 bucket (choose a unique bucket name)
      ```
      aws s3 mb s3://<bucket-name> --region us-east-1
      ```

      Create a temporary file used to create folders in the S3 bucket.
      ```
      touch temp.txt
      ```

      Choose a Design Checkpoint (dcp) folder name.
      ```
      aws s3 cp temp.txt s3://<bucket-name>/<dcp-folder-name>/
      ```

      Choose a logs folder name.
      ```
      aws s3 cp temp.txt s3://<bucket-name>/<logs-folder-name>/
      ```

2. FPGA Developer AMI
   [https://aws.amazon.com/marketplace/pp/prodview-gimv3gqbpe57k](https://aws.amazon.com/marketplace/pp/prodview-gimv3gqbpe57k)
   Subscribe to this software and continue to configuration.

   From here, choose software version `1.12.2 (Jan 31, 2023)` in order to use the 2021.2 version of the tools. Make sure that the region is set to `US East (N. Virginia)` as that is the closest location that supports EC2 F1 instances.

   Next, continue to launch. In the `Choose Action` box, select `Launch through EC2`. If you are planning to run emulations, choose the `z1d.2xlarge`, if planning to run on hardware/fpga, choose the `f1.2xlarge` instance.

   In the `Configure storage` block, click `Advanced`, expand Volume 2 and change 
   `Delete on termination` to `Yes`. You can now click `Launch instance`.

   From here, assuming AWS permissions are set up correctly, you will need to set up an `Elastic IP` for this EC2 instance. First, click `Allocate Elastic IP address`, and then click `Allocate`. Next, click `Actions` and then select the newly created instance and its private IP address.

   Next, you want to edit your `Security Group's` > `Inbound rules` by creating a new rule for `SSH, My IP`, then `Save rules` to whitelist your IP to be allowed to access the instance.

   Now, to connect to the EC2 instance through SSH, perform the command
   ```
   ssh -i "<path>/<to>/<private>/<key>" centos@<public ip address>
   ```

3. Setup EC2 Instance
   1. Patch Outdated CentOS Mirror List
      ```
      sudo sed -i s/mirror.centos.org/vault.centos.org/g /etc/yum.repos.d/*.repo
      sudo sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/*.repo
      sudo sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/*.repo
      ```

      NOTE: you will need to copy the commands from [https://serverfault.com/a/1161847](https://serverfault.com/a/1161847) due to the way latex formats the caret.

      Once updated, refresh the cache.
      ```
      yum clean all ; yum makecache
      ```

   2. Setup Vitis
      ```
      git clone https://github.com/aws/aws-fpga.git $AWS_FPGA_REPO_DIR
      cd $AWS_FPGA_REPO_DIR
      source vitis_setup.sh
      ```

   3. Setup XRT
      Replace release tag with your version found in the table here, the value is correct for version `2021.2`: [https://github.com/aws/aws-fpga/blob/master/Vitis/docs/XRT_installation_instructions.md](https://github.com/aws/aws-fpga/blob/master/Vitis/docs/XRT_installation_instructions.md)
      ```
      XRT_RELEASE_TAG=202120.2.12.427

      cd aws-fpga
      source vitis_setup.sh
      cd $VITIS_DIR/Runtime
      export XRT_PATH="${VITIS_DIR}/Runtime/${XRT_RELEASE_TAG}"
      git clone http://www.github.com/Xilinx/XRT.git -b ${XRT_RELEASE_TAG} ${XRT_PATH}

      cd ${XRT_PATH}
      sudo ./src/runtime_src/tools/scripts/xrtdeps.sh

      cd build
      scl enable devtoolset-9 bash
      ./build.sh

      cd Release
      sudo yum reinstall xrt_*-aws.rpm -y
      ```

      If the above fails, you may need to clear the cache again and run the above commands again.
      ```
      yum clean all ; yum makecache
      ```
NOTE: you will need to source the following 2 scripts before you run compile or run anything.
```
source /home/centos/src/project_data/aws-fpga/vitis_setup.sh
source /home/centos/src/project_data/aws-fpga/vitis_runtime_setup.sh
```

The value for the PLATFORM is `$AWS_PLATFORM`

Now that the environment is set up, refer to `EXECUTION` for steps to run the tests.

Here's the content converted to Markdown format:

# Execution

Before you can run the execution, you will need to clone the repository, in which you will find 3 folders `local_emu`, `aws_emu`, and `aws_hw`. Note that emulation will take a long time for larger data sizes.

If your python version is not standard, you will need to `EXPORT python=path/to/python` in order for the bash scripts to run python scripts.

The way these tests are set up is that in the `./src/template`, there are 6 designs, each to test one of the data transfer actions from the above list. Each design performs the same vector add function. 2 identical functions of variable size will be added and the result is returned and then verified. The size of the data transferred / vectors are incremented by powers of 2, starting from the smallest possible value to the largest possible value.

There are 3 parameters/variables that are needed:

1. Vector A: The first vector to be added.
2. Vector B: The second vector to be added.
3. Size: The size of the vectors and variable data size to let the FPGA know the size of the vectors for vector addition.

In a typical test run (`./src/run_compile.sh`), each design folder will be copied to `./src/$PROJECT` where it will be compiled for the target platform and ran. The compilation stage is done asynchronously for optimisation and the execution is ran individually to record maximum performance. As the designs are compiled and ran, information regarding the run will be printed out, and everything will be logged in the logs found in `./logs`, one for each design (6 logs per test run, minus the ones that are not supported or ran).

From here, in order to gather information (size of data transfer and elapsed time) from the test runs, run the script `./src/parse_logs.py` which will create .csv files in `./logs_data` with the needed information. To graph the .csv files, run `./src/graph_data.py`, which will graph the transfer size on the x-axis and elapsed time on the y-axis in log10 timescale.

## Local Emulation

1. Navigate to the `local_emu` folder.
   ```
   cd local_emu
   ```
2. Change the PLATFORM variable in `src/run_compile.sh` to the target platform found in `/opt/xilinx/platforms/` (the folder name of the platform). Save and exit.
3. Change the data_sizes variable in `src/update_data_size.py` data size values you want. Each value represents the number of elements to in the vector to transfer. For example, `data_sizes = [16, 32]` will transfer 16 integers and in the next run transfer 32 integers in the next test run. Note that to calculate the total bytes sent, multiply the number of integers by 4. Save and exit.
4. Go into the `src` folder and run `run_compile.sh`.
   ```
   cd src; sh run_compile.sh
   ```

## AWS EC2 Z1D Emulation

1. Navigate to the `aws_emu` folder.
   ```
   cd aws_emu
   ```
2. Change the data_sizes variable in `src/update_data_size.py` data size values you want. Each value represents the number of elements to in the vector to transfer. For example, `data_sizes = [16, 32]` will transfer 16 integers and in the next run transfer 32 integers in the next test run. Note that to calculate the total bytes sent, multiply the number of integers by 4. Save and exit.
3. Go into the `src` folder and run `run_compile.sh`.
   ```
   cd src; sh run_compile.sh
   ```

## AWS EC2 F1 Hardware

1. Start on a `z1d.2xlarge` instance, and navigate to the `aws_hw` folder.
   ```
   cd aws_hw
   ```
2. Change the data_sizes variable in `src/update_data_size.py` data size values you want. Each value represents the number of elements to in the vector to transfer. For example, `data_sizes = [16, 32]` will transfer 16 integers and in the next run transfer 32 integers in the next test run. Note that to calculate the total bytes sent, multiply the number of integers by 4. Save and exit.
3. Go into the `src` folder and run `run_compile.sh`. This step may take up to 3 hours.
   ```
   cd src; sh run_compile.sh
   ```
4. Create a backup of the newly compiled binary files. This will create a backup folder `.backup` in the `aws_hw` folder.
   ```
   sh backup.sh
   ```
5. Open `create_afi.sh` and edit the `S3_BUCKET_NAME`, `S3_DCP`, and `S3_LOGS` according to what you named the bucket and folders.
   Note that for this step, you must have setup AWS & Permissions according to `SETUP`).
6. Run `create_afi.sh`
   ```
   sh create_afi.sh
   ```
7. Save the folders in the `.backup/src` containing the `*.awsxclbin` files locally. An easy method to set this up without further setup is by following this tutorial for SFTP:
   [https://www.youtube.com/watch?v=o-dH2C_Nz-E](https://www.youtube.com/watch?v=o-dH2C_Nz-E)
8. Wait until the Amazon FPGA Image (API) is available.
   You can check the status of it by finding the AFI id `*_afi_id.txt` file in the `.backup/src/<PROJECT>` folder and then running:
   ```
   aws ec2 describe-fpga-images --fpga-image-ids <AFI ID>
   ```
   The status JSON should show
   ```json
   ...
   "State": {
       "Code": "available"
   },
   ...
   ```
   when the AFI is ready.
9. Once ready, create a AWS EC2 F1 instance, setup Vitis and XRT as shown in `SETUP` and in the same manner as the `z1d` instance was setup.
10. Now in the same manner as before, copy the project files from the backup folder back into the `src` directory of the newly cloned project.
    Thus, when you navigate to `aws_hw/src`, you will find `ocl_cpu_to_gmem, ocl_cpu_to_gmem_rw, ...`.
11. Now, execute the test on hardware by running `run_hw.sh`
    ```
    sh run_hw.sh
    ```

## Parsing Log Files & Graphing Results

You will notice that after every test, the `./logs` folder will become populated with log files for each project/design. These log files contain execution information of the type of data transfer, the size, and the time it took to complete. Below are the steps to parse them into a CSV format and graph them.

Note that running `parse_logs.py` and `graph_data.py` require Python 3.6+.

1. Install the needed python library.
   ```
   pip install plotnine
   ```
2. Navigate the the `src` folder.
   ```
   cd ./src
   ```
3. Create the `logs_data` folder.
   ```
   mkdir logs_data
   ```
4. Parse the logs and generate CSV files in `log_data`.
   ```
   python parse_logs.py
   ```
5. Edit Graph titles and output file names to your liking.
   Edit lines:
   ```python
   labs(title=f'Benchmark {action} Speeds vs Data Sizes ({log_type})',
               x='Transfer Size (GB) (log scale)',
               y='Transfer Speed (GB/s)') +        
   ```
   and
   ```python
   plot.save(f'../logs_data/{log_type}_{action}_log.png', width=10, height=6, dpi=300)
   ```
6. Graph the CSV files into PNGs in `log_data`.
   ```
   python graph_data.py
   ```
