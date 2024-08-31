import pandas as pd
import numpy as np
from plotnine import ggplot, aes, geom_point, geom_line, labs, theme_minimal, scale_x_log10, theme, element_blank, element_line, geom_vline, scale_color_manual, scale_shape_manual, element_text

log_types = ["ocl_cpu_to_gmem", "ocl_cpu_to_gmem_rw", "xrt_cpu_to_gmem", "xrt_cpu_to_gmem_rw", "ocl_fpga_to_gmem"]
actions = ["READ", "WRITE"]

data_hw = None
data_emu = None

# custom size label function
def size_format(bytes):
    if bytes < 1024:
        return f"{bytes}B"
    elif bytes < 1024**2:
        return f"{bytes//1024}KB"
    elif bytes < 1024**3:
        return f"{bytes//(1024**2)}MB"
    else:
        return f"{bytes//(1024**3)}GB"

if __name__ == '__main__':
    # fetch data
    for log_type in log_types:
        for action in actions:
            for execution_mode in ["hw", "emu"]:
                # read the log file
                file = f'../logs_data/{execution_mode}_{log_type}_{action}.csv'
                try:
                    data = pd.read_csv(file)
                except FileNotFoundError:
                    continue

                # get the columns and format into arrays
                transfer_sizes_bytes = list(data['SIZE (bytes)'])
                transfer_sizes_mb = np.array([size / 1024 / 1024 for size in transfer_sizes_bytes])
                median_times_ms = np.array(data['TIME (ms)'])

                # convert from bytes and ms-> GB and s
                transfer_sizes_gb = transfer_sizes_mb / 1024  # in GB
                median_times_s = median_times_ms * 0.001  # in s

                # Calculate speeds in GB/s
                speeds_gbps = transfer_sizes_gb / median_times_s

                x_axis_title = "Transfer Size (B)"
                y_axis_title = "Transfer Speed (GB/s)"
                
                if execution_mode == "hw":
                    data_hw = pd.DataFrame({
                        x_axis_title: transfer_sizes_bytes[:],
                        y_axis_title: speeds_gbps[:]
                    })
                elif execution_mode == "emu":
                    data_emu = pd.DataFrame({
                        x_axis_title: transfer_sizes_bytes[:],
                        y_axis_title: speeds_gbps[:]
                    })

                    # print fastest speeds and their corresponding sizes
                    max_speed = max(speeds_gbps)
                    max_speed_index = speeds_gbps.tolist().index(max_speed)

                    print(f"Fastest speed for {log_type} {action} is {round(max_speed, 3)} GB/s @ {size_format(transfer_sizes_bytes[max_speed_index])} bytes")

            data = pd.concat([data_hw, data_emu], keys=["hw", "emu"], names=["Execution Mode"]).reset_index()

            # Define custom breaks and labels
            custom_breaks = [64 * (2**i) for i in range(0, 26, 2)]  # this will generate [64, 256, 1024, 4096, ..., 2GB]
            custom_labels = [size_format(b) for b in custom_breaks]

            # Plot using plotnine (ggplot)
            plot = (
                ggplot(data, aes(x='Transfer Size (B)', y='Transfer Speed (GB/s)', color='Execution Mode', shape='Execution Mode', group='Execution Mode')) +
                geom_vline(xintercept=custom_breaks, color='lightgray', size=0.5, alpha=0.5) +
                geom_point(size=3) +
                geom_line(size=1) +
                scale_color_manual(values={"hw": "blue", "emu": "red"}) +
                scale_shape_manual(values={"hw": "o", "emu": "^"}) +
                scale_x_log10(breaks=custom_breaks, labels=custom_labels) +
                labs(title=f'Benchmark {action} Speeds vs Data Sizes ({log_type})',
                    x='Transfer Size (B)',
                    y='Transfer Speed (GB/s)') +
                theme_minimal(base_family="Times New Roman") + 
                theme(
                    text=element_text(family="Times New Roman"),
                    axis_text=element_text(family="Times New Roman"),
                    axis_title=element_text(family="Times New Roman"),
                    legend_text=element_text(family="Times New Roman"),
                    legend_title=element_text(family="Times New Roman"),
                    plot_title=element_text(family="Times New Roman", face="bold"),
                    panel_grid_major_x=element_blank(),
                    panel_grid_minor_x=element_blank(),
                    axis_line=element_line(colour="black", size=0.5),
                )
            )

            # Save the plot
            plot.save(f'../logs_data/{log_type}_{action}.png', width=10, height=6, dpi=300)
