import os
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def process_perf_txt(directory, contents):

    # Lists to store the extracted values
    times = []
    cpu_clk_unhalted = []
    inst_retired_any = []

    # Split the contents into lines
    lines = contents.splitlines()

    for line in lines:
        # Skip lines that are comments or headers
        if line.startswith('#') or 'time' in line:
            continue
        
        # Extract values using regular expressions
        match = re.match(r'\s*([\d.]+)\s+([\d,<>not counted]+)\s+CPU_CLK_UNHALTED.THREAD', line)
        if match:
            time = float(match.group(1))
            count_str = match.group(2)
            count = int(count_str.replace(',', '')) if 'not counted' not in count_str else 0
            times.append(round(time, 2))
            cpu_clk_unhalted.append(count)
        
        match = re.match(r'\s*([\d.]+)\s+([\d,<>not counted]+)\s+INST_RETIRED.ANY', line)
        if match:
            count_str = match.group(2)
            count = int(count_str.replace(',', '')) if 'not counted' not in count_str else 0
            inst_retired_any.append(count)

    plot_data(directory, times[:100], cpu_clk_unhalted[:100], inst_retired_any[:100])


def plot_data(directory, times, cpu_clk_unhalted, inst_retired_any):
    # Create a PDF file for plots
    pdf_filename = f"{directory}.pdf"
    with PdfPages(pdf_filename) as pdf:
        # Plot CPU_CLK_UNHALTED.THREAD and INST_RETIRED.ANY
        fig, ax1 = plt.subplots(figsize=(15, 7))  # Elongate the image along x-axis
        fig.subplots_adjust(top=0.85, bottom=0.15, left=0.1, right=0.9)  # Adjust margins
        color = 'tab:blue'
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('CPU_CLK_UNHALTED.THREAD', color=color)
        ax1.plot(times, cpu_clk_unhalted, color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = 'tab:red'
        ax2.set_ylabel('INST_RETIRED.ANY', color=color)
        ax2.plot(times, inst_retired_any, color=color)
        ax2.tick_params(axis='y', labelcolor=color)

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])  # Add space around the title
        plt.title(f"Time Series Data for {directory}", pad=20)  # Add padding to the title
        pdf.savefig(fig)
        plt.close(fig)

        # Calculate and plot cycles-per-instruction
        cpi = [clk / inst if inst != 0 else 0 for clk, inst in zip(cpu_clk_unhalted, inst_retired_any)]
        fig, ax1 = plt.subplots(figsize=(15, 7))  # Elongate the image along x-axis
        fig.subplots_adjust(top=0.85, bottom=0.15, left=0.1, right=0.9)  # Adjust margins
        color = 'tab:green'
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('CPI', color=color)
        ax1.plot(times, cpi, color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])  # Add space around the title
        plt.title(f"CPI Data for {directory}", pad=20)  # Add padding to the title
        pdf.savefig(fig)
        plt.close(fig)

        # Calculate and plot cumulative CPI
        cumulative_clk = [sum(cpu_clk_unhalted[:i+1]) for i in range(len(cpu_clk_unhalted))]
        cumulative_inst = [sum(inst_retired_any[:i+1]) for i in range(len(inst_retired_any))]
        cumulative_cpi = [clk / inst if inst != 0 else 0 for clk, inst in zip(cumulative_clk, cumulative_inst)]

        fig, ax1 = plt.subplots(figsize=(15, 7))  # Elongate the image along x-axis
        fig.subplots_adjust(top=0.85, bottom=0.15, left=0.1, right=0.9)  # Adjust margins
        color = 'tab:purple'
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Cumulative CPI', color=color)
        ax1.plot(times, cumulative_cpi, color=color)
        ax1.tick_params(axis='y', labelcolor=color)

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])  # Add space around the title
        plt.title(f"Cumulative CPI Data for {directory}", pad=20)  # Add padding to the title
        pdf.savefig(fig)
        plt.close(fig)



def find_and_process_perf_txt():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Iterate through all the items in the script directory
    for item in os.listdir(script_dir):
        item_path = os.path.join(script_dir, item)
        
        # Check if the item is a directory
        if os.path.isdir(item_path):
            # Check if the perf.txt file exists in the directory
            perf_txt_path = os.path.join(item_path, 'perf.txt')
            if os.path.isfile(perf_txt_path):
                # Read the contents of perf.txt and process it
                with open(perf_txt_path, 'r') as file:
                    contents = file.read()
                    process_perf_txt(item, contents)

if __name__ == "__main__":
    find_and_process_perf_txt()
