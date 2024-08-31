/**
* Copyright (C) 2019-2021 Xilinx, Inc
*
* Licensed under the Apache License, Version 2.0 (the "License"). You may
* not use this file except in compliance with the License. A copy of the
* License is located at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
* WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
* License for the specific language governing permissions and limitations
* under the License.
*/

#include "cmdlineparser.h"
#include <iostream>
#include <cstring>

// XRT includes
#include "experimental/xrt_bo.h"
#include "experimental/xrt_device.h"
#include "experimental/xrt_kernel.h"

#include <chrono>

// #define DATA_SIZE EDIT_SIZE

auto get_ns() {
    return std::chrono::high_resolution_clock::now();
}


int main(int argc, char** argv) {
    std::vector<int> DATA_SIZES = { EDIT_DATA_SIZES };
    for (int DATA_SIZE : DATA_SIZES) {
        // Command Line Parser
        sda::utils::CmdLineParser parser;

        // Switches
        //**************//"<Full Arg>",  "<Short Arg>", "<Description>", "<Default>"
        parser.addSwitch("--xclbin_file", "-x", "input binary file string", "");
        parser.addSwitch("--device_id", "-d", "device index", "0");
        parser.parse(argc, argv);

        // Read settings
        std::string binaryFile = parser.value("xclbin_file");
        int device_index = stoi(parser.value("device_id"));

        if (argc < 3) {
            parser.printHelp();
            return EXIT_FAILURE;
        }

        std::cout << "Open the device" << device_index << std::endl;
        auto device = xrt::device(device_index);
        std::cout << "Load the xclbin " << binaryFile << std::endl;
        auto uuid = device.load_xclbin(binaryFile);

        size_t vector_size_bytes = sizeof(int) * DATA_SIZE;

        auto krnl = xrt::kernel(device, uuid, "vadd");

        std::cout << "Allocate Buffer in Global Memory\n";
        auto bo0 = xrt::bo(device, vector_size_bytes, krnl.group_id(0));
        auto bo1 = xrt::bo(device, vector_size_bytes, krnl.group_id(1));
        auto bo_out = xrt::bo(device, vector_size_bytes, krnl.group_id(2));

        // Map the contents of the buffer object into host memory
        auto bo0_map = bo0.map<int*>();
        auto bo1_map = bo1.map<int*>();
        auto bo_out_map = bo_out.map<int*>();
        std::fill(bo0_map, bo0_map + DATA_SIZE, 0);
        std::fill(bo1_map, bo1_map + DATA_SIZE, 0);
        std::fill(bo_out_map, bo_out_map + DATA_SIZE, 0);

        // Create the test data
        // int bufReference[DATA_SIZE];
        std::vector<int> bufReference(DATA_SIZE);
        for (int i = 0; i < DATA_SIZE; ++i) {
            bo0_map[i] = i;
            bo1_map[i] = i;
            bufReference[i] = bo0_map[i] + bo1_map[i];
        }

        // Synchronize buffer content with device side
        std::cout << "synchronize input buffer data to device global memory\n";

        auto start_time = get_ns();
        bo0.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        auto end_time = get_ns();
        auto buffer1_time = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        start_time = get_ns();
        bo1.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        end_time = get_ns();
        auto buffer2_time = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        start_time = get_ns();
        bo0.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        end_time = get_ns();
        auto buffer1_time2 = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        start_time = get_ns();
        bo1.sync(XCL_BO_SYNC_BO_TO_DEVICE);
        end_time = get_ns();
        auto buffer2_time2 = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        std::cout << "Execution of the kernel\n";
        auto run = krnl(bo0, bo1, bo_out, DATA_SIZE);
        run.wait();

        // Get the output;
        std::cout << "Get the output data from the device" << std::endl;
        start_time = get_ns();
        bo_out.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
        end_time = get_ns();
        auto buffer_out_time = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        std::cout << "Get the output data from the device" << std::endl;
        start_time = get_ns();
        bo_out.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
        end_time = get_ns();
        auto buffer_out_time2 = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        std::cout << "Get the output data from the device" << std::endl;
        start_time = get_ns();
        bo_out.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
        end_time = get_ns();
        auto buffer_out_time3 = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        std::cout << "Get the output data from the device" << std::endl;
        start_time = get_ns();
        bo_out.sync(XCL_BO_SYNC_BO_FROM_DEVICE);
        end_time = get_ns();
        auto buffer_out_time4 = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time).count();

        // Validate our results
        // if (std::memcmp(bo_out_map, bufReference, DATA_SIZE))
        //     throw std::runtime_error("Value read back does not match reference");
        for (int i = 0; i < DATA_SIZE; ++i) {
            if (bo_out_map[i] != bufReference[i]) {
                throw std::runtime_error("Value read back does not match reference at index " + std::to_string(i));
            }
        }

        std::cout << "TEST PASSED\n";

        std::cout << "CPU WRITE GMEM BUFFER1:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer1_time << " ns" << std::endl;

        std::cout << "CPU WRITE GMEM BUFFER2:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer2_time << " ns" << std::endl;

        std::cout << "CPU WRITE GMEM BUFFER1 2:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer1_time2 << " ns" << std::endl;

        std::cout << "CPU WRITE GMEM BUFFER2 2:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer2_time2<< " ns" << std::endl;

        std::cout << "CPU READ GMEM BUFFER OUT:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer_out_time << " ns" << std::endl;

        std::cout << "CPU READ GMEM BUFFER OUT 2:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer_out_time2 << " ns" << std::endl;

        std::cout << "CPU READ GMEM BUFFER OUT 3:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer_out_time3 << " ns" << std::endl;

        std::cout << "CPU READ GMEM BUFFER OUT 4:" << std::endl;
        std::cout << "SIZE: " << vector_size_bytes << " bytes" << std::endl;
        std::cout << "TIME: " << buffer_out_time4 << " ns" << std::endl;
    }
    return 0;
}
