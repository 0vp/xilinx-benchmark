# This script parses the timeline_kernels.csv file to get the start and end time of each kernel event.

import sys

import sys

csv_dir = sys.argv[2]
timeline_kernels = open('./' + csv_dir + '/timeline_kernels.csv').read().split('\n')

timeline = {
    'load_input_U0': {
        'found': False,
        'start': 0,
        'end': 0
    },
    'load_input_1_U0': {
        'found': False,
        'start': 0,
        'end': 0
    },
    'store_result_U0': {
        'found': False,
        'start': 0,
        'end': 0
    }
}

def find_end_time(kernel_event, line, i):
    global timeline_kernels, timeline

    if timeline[kernel_event]['found'] == False:
        # get start time
        timeline[kernel_event]['found'] = True
        timeline[kernel_event]['start'] = float(line.split(',')[7])
        return
    
    # if next kernel event is not the same as the current one, save the end time
    if kernel_event not in timeline_kernels[i + 1]:
        # get end time
        timeline[kernel_event]['end'] = float(line.split(',')[8])

if __name__ == '__main__':
    print('Parsing Timeline Kernels...')

    data_size = 4 * int(sys.argv[1]) # 4 bytes per int * size of vector
    project_name = sys.argv[2]
    access_type = "HOST" if 'host' in project_name else "GMEM"
    time_unit = ''

    for i, line in enumerate(timeline_kernels):
        # get the time unit
        if "Start Time (" in line:
            time_unit = line.split(',')[7].replace('Start Time (', '').replace(')', '').replace(' ', '')

        # replace the kernel names to be consistent with all projects
        if 'host' in project_name:
            line = line.replace('rp_krnl_vadd_Pipeline_readA_fu', 'load_input_U0')
            line = line.replace('rp_krnl_vadd_Pipeline_readB_fu', 'load_input_1_U0')
            line = line.replace('grp_krnl_vadd_Pipeline_writeC', 'store_result_U0')

        # find the start and end time of each kernel event
        if "load_input_U0" in line:
            find_end_time('load_input_U0', line, i)
        elif "load_input_1_U0" in line:
            find_end_time('load_input_1_U0', line, i)
        elif "store_result_U0" in line:
            find_end_time('store_result_U0', line, i)

    # print the timeline
    print(f"FPGA READ {access_type} 1")
    print(f"SIZE: {data_size} bytes")
    print(f"TIME: {timeline['load_input_U0']['end'] - timeline['load_input_U0']['start']} {time_unit}")

    print(f"FPGA READ {access_type} 2")
    print(f"SIZE: {data_size} bytes")
    print(f"TIME: {timeline['load_input_1_U0']['end'] - timeline['load_input_1_U0']['start']} {time_unit}")

    print(f"FPGA WRITE {access_type}")
    print(f"SIZE: {data_size} bytes")
    print(f"TIME: {timeline['store_result_U0']['end'] - timeline['store_result_U0']['start']} {time_unit}")