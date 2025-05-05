import os
import json
import sys
import portalocker
from typing import Tuple, Optional, Dict, List

try:
    from mpi4py import MPI
    # detect whether in MPI environment
    if MPI.COMM_WORLD.Get_size() > 1:
        using_mpi = True
    else:
        using_mpi = False
except ImportError:
    using_mpi = False

class PortController:
    def __init__(self, name: str, path: str = "~/.portcl", ports: List[int]=None, max_process: List[int]=None):
        self.base_path = os.path.expanduser(path)
        self.name = name
        self.config_path = os.path.join(self.base_path, f"{name}.json")
        self.ports = ports
        os.makedirs(self.base_path, exist_ok=True)
        
        if not os.path.exists(self.config_path):
            self._init_config()

    def _init_config(self):
        need_confirm = False
        if self.ports is not None and self.max_process is not None:
            if len(self.ports) != len(self.max_process):
                raise ValueError("Length of ports and max_process must be the same")
            ports_info = [{"port": p, "process_ids": [], "max_process": m} for p, m in zip(self.ports, self.max_process)]
        else:
            need_confirm = True
            ports_info = [
                {"port": 9000, "process_ids": [], "max_process": 10},
                {"port": 9001, "process_ids": [], "max_process": 5},
                {"port": 9002, "process_ids": [], "max_process": 8}
            ]
        
        template = {
            "host": "localhost",
            "ports": ports_info
        }
        
        with open(self.config_path, 'w') as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            json.dump(template, f, indent=2)

        print(f"init config file for {self.name} in {self.config_path}")
        if need_confirm:
            print("Please confirm the ports and max_process in the config file.")
            print("You can edit the config file directly if needed.")
            input("Press Enter to continue...")

    def _is_process_alive(self, pid: int) -> bool:
        try:
            if sys.platform == 'win32':
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle == 0:
                    return False
                kernel32.CloseHandle(handle)
                return True
            else:
                os.kill(pid, 0)
                return True
        except:
            return False

    def read_config(self, return_file: bool = False) -> Tuple[dict, Optional[portalocker.Lock]]:
        try:
            f = open(self.config_path, 'r+')
            portalocker.lock(f, portalocker.LOCK_EX)
            
            config = json.load(f)
            self._validate_config(config)
            
            for port_info in config["ports"]:
                port_info["process_ids"] = [pid for pid in port_info["process_ids"] if self._is_process_alive(pid)]
            
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()
            
            if return_file:
                return config, f
            else:
                portalocker.unlock(f)
                f.close()
                return config, None
                
        except (portalocker.LockException, json.JSONDecodeError) as e:
            raise RuntimeError(f"配置文件操作失败: {str(e)}")

    def _validate_config(self, config: dict):
        if not isinstance(config.get("host"), str):
            raise ValueError("Invalid host field")
            
        ports = config.get("ports", [])
        if not isinstance(ports, list):
            raise ValueError("Invalid ports format")
            
        for p in ports:
            if not all(k in p for k in ["port", "process_ids", "max_process"]):
                raise ValueError("Missing required port fields")

    def allocate_port(self, n:int=1, verbose: bool = True) -> list:
        config, f = self.read_config(return_file=True)

        def alloc_one(config: dict) -> int:
            candidates = sorted(
                [p for p in config["ports"] if len(p["process_ids"]) < p["max_process"]],
                key=lambda x: (len(x["process_ids"]), x["port"])
            )
            if not candidates:
                raise RuntimeError("All ports are full")
            selected = candidates[0]
            selected["process_ids"].append(os.getpid())
            return selected["port"]
        
        def alloc_n(config: dict, n: int) -> List[int]:
            ports = []
            for _ in range(n):
                ports.append(alloc_one(config))
            return ports
        
        try:
            res = alloc_n(config, n)
            
            f.seek(0)
            json.dump(config, f, indent=2)
            f.truncate()
            
            if verbose:
                self._print_status(config)
                
            return res
            
        finally:
            portalocker.unlock(f)
            f.close()

    def _print_status(self, config: dict):
        print("\nPort Status:")
        print(f"{'Port':<8} {'Used':<5} {'Max':<5} {'Status':<10}")
        for p in config["ports"]:
            used = len(p["process_ids"])
            status = "Full" if used >= p["max_process"] else "Available"
            print(f"{p['port']:<8} {used:<5} {p['max_process']:<5} {status:<10}")

    def allocate_port_mpi_all_rank_same(self, n: int = 1) -> List[int]:
        """allocate n ports in main rank, and all ranks get the same ports"""
        if using_mpi:
            comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
            size = comm.Get_size()
            
            if rank == 0:
                ports = self.allocate_port(n)
                all_ports = comm.bcast(ports, root=0)
            else:
                all_ports = comm.bcast(None, root=0)
            return all_ports
        else:
            return self.allocate_port(n)
