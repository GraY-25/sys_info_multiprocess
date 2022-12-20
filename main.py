import time
import psutil
import platform
from datetime import datetime
import cpuinfo
import socket
import uuid
import re
import multiprocessing


class SysInfoCollectorBase:
    last_times = dict()  # store last time of run for each decorated by "_speed_test_decorator" method

    def __init__(self):
        self._run_parallel()
        # self._run_one_by_one()

    def _get_size(self, bytes_count, suffix="B"):
        """
        Get KB MB GB etc. from Bytes
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes_count < factor:
                return f"{bytes_count:.2f}{unit}{suffix}"
            bytes_count /= factor

    def _return_all_methods(self):
        """
        Return all methods from class, except starting with "_"
        """
        public_method_names = [getattr(self, method) for method in dir(self) if callable(getattr(self, method)) if not method.startswith('_')]
        return public_method_names

    def _print_results(self, results_list):
        for result in results_list:
            for k, v in result.items():
                print(k, v)

    def _runner(self, f):
        return f()

    def _speed_test_decorator(func):
        def inner(*args, **kwargs):
            time0 = time.time()
            func(*args, **kwargs)
            time_of_run = time.time() - time0
            cls_name = str(args[0])[str(args[0]).find(".") + 1:str(args[0]).find(" ")]
            SysInfoCollectorBase.last_times[cls_name] = time_of_run
            print(f"\n{cls_name} exec time: {time_of_run}")
        return inner

    @_speed_test_decorator
    def _run_parallel(self):
        public_method_names = self._return_all_methods()
        with multiprocessing.Pool() as pool:
            result = pool.map(self._runner, public_method_names)
        self._print_results(result)


class SysInfoCollector1(SysInfoCollectorBase):

    def __init__(self):
        super()._run_parallel()

    def get_system_information(self):
        """
        Get primary system info
        """
        result = dict()
        result["=" * 40 + " System Information " + "=" * 40] = ""
        uname = platform.uname()
        result["System: "] = uname.system
        result["Node Name: "] = uname.node
        result["Release: "] = uname.release
        result["Version: "] = uname.version
        result["Machine: "] = uname.machine
        result["Processor: "] = uname.processor
        result["Processor: "] = cpuinfo.get_cpu_info()['brand_raw']
        result["Ip-Address: "] = socket.gethostbyname(socket.gethostname())
        result["Mac-Address: "] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        return result

    def get_boot_time(self):
        """
        Get OS boot time
        """
        result = dict()
        result["=" * 40 + " Boot Time " + "=" * 40] = ""
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        result[f"Boot Time: {bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"] = ""
        return result


class SysInfoCollector2(SysInfoCollectorBase):

    def __init__(self):
        super()._run_parallel()

    def get_cpu_information(self):
        """
        Get CPU information
        """
        result = dict()
        result["=" * 40 + " CPU Info " + "=" * 40] = ""
        result["Physical cores: "] = psutil.cpu_count(logical=False)
        result["Total cores: "] = psutil.cpu_count(logical=True)
        cpufreq = psutil.cpu_freq()
        result["Max Frequency: "] = f"{cpufreq.max:.2f}Mhz"
        result["Min Frequency: "] = f"{cpufreq.min:.2f}Mhz"
        result["Current Frequency: "] = f"{cpufreq.current:.2f}Mhz"
        result["CPU Usage Per Core: "] = ""
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            result[f"Core {i}: "] = f"{percentage}%"
        result["Total CPU Usage: "] = f"{psutil.cpu_percent()}%"
        return result

    def get_memory_information(self):
        """
        Get memory information
        """
        result = dict()
        result["=" * 40 + " Memory Information " + "=" * 40] = ""
        svmem = psutil.virtual_memory()
        result["Total: "] = f"{self._get_size(svmem.total)}"
        result["Available: "] = f"{self._get_size(svmem.available)}"
        result["Used: "] = f"{self._get_size(svmem.used)}"
        result["Percentage: "] = f"{svmem.percent}%"
        result["=" * 20 + " SWAP " + "=" * 20] = ""
        swap = psutil.swap_memory()
        result["Total: "] = f"{self._get_size(swap.total)}"
        result["Free: "] = f"{self._get_size(swap.free)}"
        result["Used: "] = f"{self._get_size(swap.used)}"
        result["Percentage: "] = f"{swap.percent}%"
        return result

    def get_disk_information(self):
        """
        Get disk information
        """
        result = dict()
        result["=" * 40 + " Disk Information " + "=" * 40] = ""
        result["Partitions and Usage:"] = ""
        partitions = psutil.disk_partitions()
        for partition in partitions:
            result["=== Device: "] = f"{partition.device} ==="
            result["  Mountpoint: "] = f"{partition.mountpoint}"
            result["  File system type: "] = f"{partition.fstype}"
            try:
                partition_usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                # TODO: for "Drive not ready" state
                continue
            result[f"  Total Size: "] = f"{self._get_size(partition_usage.total)}"
            result[f"  Used: "] = f"{self._get_size(partition_usage.used)}"
            result[f"  Free: "] = f"{self._get_size(partition_usage.free)}"
            result[f"  Percentage: "] = f"{partition_usage.percent}%"
        disk_io = psutil.disk_io_counters()
        result[f"Total read: "] = f"{self._get_size(disk_io.read_bytes)}"
        result[f"Total write: "] = f"{self._get_size(disk_io.write_bytes)}"
        return result

    def get_network_information(self):
        """
        Get network information
        """
        result = dict()
        result["=" * 40 + " Network Information " + "=" * 40] = ""
        if_addrs = psutil.net_if_addrs()
        for interface_name, interface_addresses in if_addrs.items():
            for address in interface_addresses:
                result[f"=== Interface: "] = f"{interface_name} ==="
                if str(address.family) == 'AddressFamily.AF_INET':
                    result[f"  IP Address: "] = f"{address.address}"
                    result[f"  Netmask: "] = f"{address.netmask}"
                    result[f"  Broadcast IP: "] = f"{address.broadcast}"
                elif str(address.family) == 'AddressFamily.AF_PACKET':
                    result[f"  MAC Address: "] = f"{address.address}"
                    result[f"  Netmask: "] = f"{address.netmask}"
                    result[f"  Broadcast MAC: "] = f"{address.broadcast}"
        net_io = psutil.net_io_counters()
        result[f"Total Bytes Sent: "] = f"{self._get_size(net_io.bytes_sent)}"
        result[f"Total Bytes Received: "] = f"{self._get_size(net_io.bytes_recv)}"
        return result


class SysInfoCollector_1_and_2(SysInfoCollector1, SysInfoCollector2):
    def __init__(self):
        super()._run_parallel()


class SysInfoCollector_one_by_one(SysInfoCollector1, SysInfoCollector2):

    def __init__(self):
        self._run_parallel()

    @SysInfoCollectorBase._speed_test_decorator
    def _run_parallel(self):  # Override for performance test "parallel vs one-by-one" execution.
        public_method_names = self._return_all_methods()
        result = map(self._runner, public_method_names)
        # Equivalent to:
        # self.get_system_information()
        # self.get_boot_time()
        # self.get_cpu_information()
        # self.get_memory_information()
        # self.get_disk_information()
        # self.get_network_information()
        self._print_results(result)


if __name__ == '__main__':
    collector1 = SysInfoCollector1()
    collector2 = SysInfoCollector2()
    collector_1_and_2 = SysInfoCollector_1_and_2()
    collector_one_by_one = SysInfoCollector_one_by_one()

    print(f"\n{'=' * 60}")
    for cls, last_time in SysInfoCollectorBase.last_times.items():
        print(f"Class {cls} executed in {last_time} sec.")

