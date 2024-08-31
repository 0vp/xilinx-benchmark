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

// #define DATA_SIZE EDIT_SIZE

extern "C" {
void krnl_vadd(int* a, int* b, int* out, const int n_elements) {
    int DATA_SIZE = n_elements;
    // should be DATA_SIZE, but HLS does not support dynamic array size.
    int arrayA[2147483648];
    int arrayB[2147483648];

    for (int i = 0; i < n_elements; i += DATA_SIZE) {
        int size = DATA_SIZE;
        // boundary check
        if (i + size > n_elements) size = n_elements - i;

    // Burst reading A
    readA:
        for (int j = 0; j < size; j++) arrayA[j] = a[i + j];

    // Burse reading B
    readB:
        for (int j = 0; j < size; j++) arrayB[j] = b[i + j];

    // Burst reading B and calculating C and Burst writing
    // to  Global memory
    writeC:
        for (int j = 0; j < size; j++) out[i + j] = arrayA[j] + arrayB[i + j];
    }
}
}