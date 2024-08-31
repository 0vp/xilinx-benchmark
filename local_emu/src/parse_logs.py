
import os

log_types = ["ocl_cpu_to_gmem", "ocl_cpu_to_gmem_rw", "xrt_cpu_to_gmem", "xrt_cpu_to_gmem_rw", "ocl_fpga_to_gmem", "xrt_fpga_to_gmem"]
log_types_data = {log_type: {"files": [], "READ": {}, "WRITE": {}} for log_type in log_types}

# get list of all files in the directory
def get_files(directory):
    files = os.listdir(directory)

    # get full path of files
    files = list(map(lambda x: os.path.join(directory, x), files))

    return files

# parse logs to get information
def parse_log(log_type, log):
    lines = open(log, 'r').readlines()
    for i, line in enumerate(lines):
        is_read_line = " READ " in line
        is_write_line = " WRITE " in line
        
        # check if the line is a read or write line // line that contains data
        if not (is_read_line or is_write_line):
            continue
        
        # get the data size and time taken
        data_size = int(lines[i+1].replace("SIZE: ", "").replace(" bytes\n", ""))
        time = lines[i+2].replace("TIME: ", "")
        action_type = "READ" if is_read_line else "WRITE"

        # convert the time to ms
        if "ms" in time:
            time = float(time.replace(" ms\n", ""))
        elif "ns" in time:
            time = time.replace(" ns\n", "")
            time = float(time) / 1000000
        
        # add time to the list for the data size, otherwise create a new list and entry for the data size
        try:
            log_types_data[log_type][action_type][data_size].append(time)
        except KeyError:
            log_types_data[log_type][action_type][data_size] = [time]

        # print(log_type, action_type, data_size, time)

def median(lst):
    lst = sorted(lst)  # Sort the list first
    n = len(lst)
    if n % 2 == 0:
        return (lst[n // 2] + lst[(n - 1) // 2]) / 2
    else:
        return lst[n // 2]

if __name__ == '__main__':
    logs = get_files('../logs')
    
    # create logs_data
    if not os.path.exists('../logs_data'):
        os.makedirs('../logs_data')

    # get logs for each log type
    for execution_mode in ["hw", "emu"]:
        log_types_data = {log_type: {"files": [], "READ": {}, "WRITE": {}} for log_type in log_types}
        has_files = False

        for log in logs:
            file_log_type = os.path.basename(log).split('_2024')[0]
            
            found_log_type = file_log_type.replace(execution_mode + '_', "")
            if found_log_type in log_types:
                log_types_data[found_log_type]["files"].append(log)
                has_files = True
        
        if not has_files:
            continue

        # parse logs
        for log_type in log_types_data:
            for log in log_types_data[log_type]["files"]:
                parse_log(log_type, log)

        # save log data
        for log_type in log_types_data:
            for action in ["READ", "WRITE"]:
                with open(f'../logs_data/{execution_mode}_{log_type}_{action}.csv', 'w') as f:
                    f.write("SIZE (bytes),TIME (ms)\n")
                    
                    # sort the data sizes
                    data_sizes = list(log_types_data[log_type][action].keys())
                    data_sizes.sort()
                    
                    # write the data to the file
                    for data_size in data_sizes:
                        time = median(log_types_data[log_type][action][data_size])
                        f.write(f"{data_size},{time}\n")