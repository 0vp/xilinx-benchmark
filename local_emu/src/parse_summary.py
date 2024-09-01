"""
How this works.

In native_trace.csv, you will get something like this.

MAPPING
13,READ
9,WRITE
5,xrt::bo::bo
...
EVENTS
123,0,42568.319332,2,API_CALL,13
124,123,42568.595988,2,API_CALL,13
...

The first column on events represents the event ID, and the second is the ID of the previous event that it is endind (0 if it is a start of a event). THe third column is then the time that it starts/ends.

Then, the last column represents the actual API call, which the number gets referenced in MAPPING.

Now, the way to detect the data transfers is by finding the timestamp + data size in summary.csv and trying to map it to the events in native_trace.csv.
"""

import sys

PROJECT = sys.argv[1]

mode = None
READ_ID = -1
WRITE_ID = -1

trace_data = [
    # {
    #     "start_id": n
    #     "end_id": n
    #     "start_time": n ms
    #     "rounded_start_time": n ms  
    #     "end_time": n ms
    #     "action": READ/WRITE
    #     "data_size": n bytes
    # },
]

summary = open('./' + PROJECT + "/summary.csv").read().splitlines()
native_trace = open('./' + PROJECT + "/native_trace.csv").read().splitlines()

for i, line in enumerate(native_trace):
    if line == "MAPPING":
        mode = "MAPPING"
        continue
    elif line == "EVENTS":
        mode = "EVENTS"
        continue
    elif line == "":
        mode = None
        continue

    # skip if mode is None, after it can be changed.
    if mode == None:
        continue

    # get the READ and WRITE ID
    if mode == "MAPPING":
        if ",READ" in line:
            READ_ID = line.replace(",READ", "")
        elif ",WRITE" in line:
            WRITE_ID = line.replace(",WRITE", "")
    # get all the READ and WRITE events
    elif mode == "EVENTS":
        row = line.split(",")

        # see if it is a READ/WRITE event.
        # last column is referenced to MAPPING
        if (row[-1] == READ_ID):
            ACTION = "READ"
        elif (row[-1] == WRITE_ID):
            ACTION = "WRITE"
        else:
            # isnt a needed action.
            continue

        # if start of a event
        if (row[1] == "0"):
            # in summary.csv, the time is rounded to 1 decimal place and 0 if it is a .0.
            rounded_end_time = round(float(row[2]), 1)
            if (rounded_end_time.is_integer()):
                rounded_end_time = str(int(rounded_end_time))

            trace_data.append({
                "start_id": row[0],
                "end_id": -1,
                "start_time": row[2],
                "rounded_start_time": str(rounded_end_time),
                "end_time": -1,
                "action": ACTION,
                "data_size": -1
            })
        else:
            start_id = row[1]
            end_id = row[0]
            end_time = row[2]

            # find the start id from the ones that were already found.
            found = False
            for trace in trace_data:
                if start_id == trace["start_id"]:
                    trace["end_id"] = end_id
                    trace["end_time"] = end_time
                    found = True
                
                if found:
                    break

# now we try to found the data size
for i, line in enumerate(summary):
    # determine if it is a section of summary that we are interested in.
    if "TITLE:Top Memory Reads" in line:
        mode = "READ"
        continue
    elif "TITLE:Top Memory Writes" in line:
        mode = "WRITE"
        continue
    elif line == "":
        mode = None
        continue

    # skip if mode is None, after it can be changed.
    if mode == None:
        continue

    # if entry row / line with needed data:
    if "ENTRY:" in line:
        line = line.replace("ENTRY:", "")
        time_size = line.split(",")[:2]
        start_time = time_size[0]
        data_size = time_size[1]

        # find the right transfer event and save the size
        found = False
        for trace in trace_data:
            if (start_time == trace["rounded_start_time"] or start_time == str(int(float(trace["rounded_start_time"])))) and mode == trace["action"]:
                # convert to bytes
                trace["data_size"] = int(float(data_size) * 1000)
                found = True

            if found:
                break

for trace in trace_data:
    if trace["data_size"] != -1:
        print("CPU " + trace["action"] + " GMEM BUFFER:")
        print("SIZE: " + str(trace["data_size"]) + " bytes")
        print("TIME: " + str(float(trace["end_time"]) - float(trace["start_time"])) + " ms")