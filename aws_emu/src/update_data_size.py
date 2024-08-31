# copy the template into `run` and update the data size

# python3 copy_template.py <template_name> <data_size>

import sys

powers_of_two = [ 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288, 1048576, 2097152, 4194304, 8388608, 16777216, 33554432, 67108864, 134217728, 268435456, 536870912, 1073741824, 2147483648, 4294967296, 8589934592, 17179869184, 34359738368, 68719476736 ]
data_sizes = [16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]

def update_template(template, project_name):
    print('Updating the data size range for template <' + template + '/' + project_name + '>')
    
    # replace `std::vector<int> DATA_SIZES = { EDIT_DATA_SIZES };` with `std::vector<int> DATA_SIZES = { data_size };`
    filename = template + '/src/host.cpp'
    file = open(filename).read()

    # if fpga project, add a '0' entry at the end of the data list
    # this is done as they need to iterate half a loop more
    if 'fpga' in project_name:
        # need to add a '0' entry at the end of the data list
        data_sizes.append(0)
        data_sizes_str = ', '.join([str(x) for x in data_sizes])
    else:
        data_sizes_str = ', '.join([str(x) for x in data_sizes])

    file = file.replace('DATA_SIZES = { EDIT_DATA_SIZES };', 'DATA_SIZES = { ' + data_sizes_str + ' };')

    with open(filename, 'w') as f:
        f.write(file)

update_template(sys.argv[1], sys.argv[2])