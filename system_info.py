import clr
import os
import psutil
import time
import pynvml
from struct import pack
from pySerialTransfer import pySerialTransfer as txfer


# Load LibreHardwareMonitorLib.dll
dll_path = os.path.join(os.getcwd(), "LibreHardwareMonitorLib.dll")
clr.AddReference(dll_path)

from LibreHardwareMonitor import Hardware

# Setup serial

#esp = serial.Serial(port='COM7', baudrate=115200, timeout=.1)

computer = Hardware.Computer()
computer.IsCpuEnabled = True
computer.Open()

cpu_hw = None
cpu_temp_sensor = None

# Find the CPU hardware block and a suitable temperature sensor
for hw in computer.Hardware:
    if hw.HardwareType == Hardware.HardwareType.Cpu:
        cpu_hw = hw
        hw.Update()

        first_temp = None

        for sensor in hw.Sensors:
            if sensor.SensorType == Hardware.SensorType.Temperature:
                # Remember the first temp sensor as fallback
                if first_temp is None:
                    first_temp = sensor
                # Prefer a "Package" sensor if available
                if "Package" in (sensor.Name or ""):
                    cpu_temp_sensor = sensor
                    break  # we’re happy

        # if no "Package" sensor was found, use the first temp sensor
        if cpu_temp_sensor is None:
            cpu_temp_sensor = first_temp

        break  # we’re done with CPU

def get_cpu_temp():
    global cpu_hw, cpu_temp_sensor
    if cpu_hw is None or cpu_temp_sensor is None:
        return None

    cpu_hw.Update()  # refresh sensor values
    value = cpu_temp_sensor.Value
    return float(value) if value is not None else None


def get_cpu_load():
    return psutil.cpu_percent(interval=1)


def get_ram_usage():
    mem = psutil.virtual_memory()
    return mem.percent


# ------- NVIDIA GPU via NVML -------
def init_nvml():
    try:
        pynvml.nvmlInit()
        return True
    except:
        return False


def get_gpu_stats():
    gpus = []
    count = pynvml.nvmlDeviceGetCount()
    for i in range(count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle).decode()

        util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

        gpus.append((name, util, temp))
    return gpus


# ------- MAIN LOOP -------
if __name__ == "__main__":
    link = txfer.SerialTransfer('COM7')
    link.open()
    #time.sleep(2)  # allow some time for the Arduino to reset

    gpu_ok = init_nvml()

    if gpu_ok:
        count = pynvml.nvmlDeviceGetCount()
        print("GPU count:", count)
    else:
        print("GPU monitoring disabled (NVML init failed).")

    while True:
        print("-" * 60)

        #print(f"CPU Load: {get_cpu_load():.1f}%")
        cpu_temp = get_cpu_temp()
        cpu_load = get_cpu_load()
        ram_load = get_ram_usage()
        #print(f"CPU Temp: {cpu_temp:.1f} °C" if cpu_temp else "CPU Temp: unavailable")

        #print(f"RAM Usage: {get_ram_usage():.1f}%")

        list_one = [int(cpu_load), int(cpu_temp) if cpu_temp is not None else 0, int(ram_load)]

        #esp.write(pack(int(cpu_temp).__str__() + "°C", 'utf-8'))
        

        if gpu_ok:
            for name, load, temp in get_gpu_stats():
                #print(f"GPU ({name}): {load}% load, {temp} °C")
                list_two = [int(load), int(temp)]
                list_one.extend(list_two)
        
        list_size = link.tx_obj(list_one)

        link.send(list_size)

        #time.sleep(0.5)
