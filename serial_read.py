import serial
import time
from typing import List
from time import sleep
from pathlib import Path
from serial.tools import list_ports
from tqdm import tqdm

def find_ports() -> List[str]:

    print("disconnect the device.")
    print("please type 'y' to continue.")

    while True:
        if input() == 'y':
            break

    disconnected_ports = set([port.device for port in list_ports.comports()])

    print(disconnected_ports)
    print("now connect the device.")
    print("please type 'y' to continue.")

    while True:
        if input() == 'y':
            break

    timeout = 10  # seconds
    possible_ports = set()

    with tqdm(total=timeout, desc="Wait for new port", unit="s") as pbar:
        start_time = time.time()
        while time.time() - start_time < timeout and len(possible_ports) < 2:
            current_ports = set([port.device for port in list_ports.comports()])
            possible_ports = current_ports.symmetric_difference(disconnected_ports)
            sleep(0.1) # check every 100ms
            pbar.update(0.1)

    if not possible_ports:
        raise Exception("No new ports found within timeout.") from None
    
    if len(possible_ports) < 2:
        raise Exception("Some ports is missing.") from None
    
    return sorted(list(possible_ports))

def connect_ports(cfg_port: str, data_port: str) -> List[serial.Serial]:
    
    try:
        cfg_ser = serial.Serial(
            port=cfg_port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        print("config port connected.")
    except serial.SerialException as e:
        print("config port connection failed.")
        raise e
    
    try:
        data_ser = serial.Serial(
            port=data_port,
            baudrate=921600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )

        print("data port connected.")
    except serial.SerialException as e:
        print("data port connection failed.")
        raise e
    
    return [cfg_ser, data_ser]

def read_config(cfg_filepath: Path) -> List[str]:

    with open(cfg_filepath, "r") as f:
        cfg_file = f.readlines()
    
    return cfg_file

def send_config(cfg_ser: serial.Serial, cfg_file: List[str], max_retries: int = 3) -> None:

    status = list()

    replies = ["Done", "Ignored: Sensor is already stopped"]

    for line in cfg_file:

        line = line.replace('\r','').strip()

        if line.startswith("%"):
            continue

        retries = 0
        while retries <= max_retries:
            cfg_ser.write(line.encode("utf-8"))
            status_lines = []
            # read return value of the device
            for _ in range(2):
                response = cfg_ser.readline()
                decoded_response = response.decode('utf-8').strip()
                status_lines.append(decoded_response)

            if any(reply in status_lines for reply in replies):
                print(f"Command '{line}' successful after {retries+1} retries. Replies: {status_lines}")
                break  # Go to the next line in cfg_file
            else:
                print(f"Command '{line}' failed, retrying ({retries+1}/{max_retries}). Replies: {status_lines}")
                retries += 1
        else: # else block of while loop, executed if loop finishes without break
            raise Exception(f"Command '{line}' failed after {max_retries} retries. Replies: {status_lines}")


def read_data(data_ser: serial.Serial) -> bytes:
    pass

if __name__ == "__main__":

    path = Path("/Users/adib/Desktop/kuliah/TA/Program/UART Reader/generic_config.cfg")
    
    cfg_port, data_port = find_ports()
    cfg_ser, data_ser = connect_ports(cfg_port, data_port)

    print("done")

    cfg_file = read_config(path)

    send_config(cfg_ser, cfg_file, 20)

    cfg_ser.close()
    data_ser.close()
    
    # data_ser = serial.Serial(data_port, 921600)
