"""
This module provide a simple and intuitive interface to control instance in child process.

The Remote Object in child process can be created by `RemoteObjectProxy`.

**In sequential mode**(paralle_execution=False), The instance's attributes and instance's function can be accessed and called like normal object in parent process. The Exception will be raised in parent process if the instance in child process raise Exception. The instance in child process is totally like a normal object in parent process, but it is actually running in a child process.

    1. The instance's attributes can be accessed like normal object.
    2. The instance's function can be called like normal object.
    3. The Exception will be raised in parent process if the instance in child process raise Exception.

**In parallel mode**(paralle_execution=True), The instance's attributes can be accessed like normal object in parent process. The instance's function can be called like normal object in parent process, but the return value is a `multiprocessing.Pipe` object, you need call recv() to get the return value. The Exception will be returned to parent process instead of raised in parent process.

    1. The instance's attributes can be accessed like normal object.
    2. The instance's function can be called like normal object, but the return value is a `multiprocessing.Pipe` object.
    3. The Exception will be returned to parent process instead of raised in parent process.

The `ParallelResultFetcher` is used to fetch the return value of parallel execution.

## Example

```python
from Kkit.child_process import RemoteObjectProxy, ParallelResultFetcher
import time

class TestObj:
    def __init__(self, time):
        self.time = time

    def sleep(self, add_time):
        time.sleep(self.time+add_time)
        return f"sleep {self.time+add_time} seconds"

def obj_creator(time):
    return TestObj(time)

# Sequential execution

test_obj = RemoteObjectProxy(obj_creator, paralle_execution=False, time=5)
print(test_obj.time)   # access attribute like normal object
print(test_obj.sleep(2))  # call method like normal object

# Parallel execution

num_processes = 10
test_objs_parallel = [RemoteObjectProxy(obj_creator, time=i) for i in range(num_processes)]
result_fetcher = ParallelResultFetcher(num_processes)

start_time = time.time()
for i in range(num_processes):
    result_fetcher[i] = test_objs_parallel[i].sleep(2)
res = result_fetcher.wait_all_results()
print(res)
print(time.time()-start_time)  # should be around 11 seconds(last object sleep the longest time, 9+2 seconds)
```
"""

import copy
import multiprocessing


class EmptyResult:
    """
    EmptyResult is a placeholder for empty result in `ParallelResultFetcher.results` list.
    """
    def __init__(self):
        pass

    def __str__(self):
        return "Empty Result"
    
    def __repr__(self):
        return "Empty Result"

class ParallelResultFetcher:
    """
    ParallelResultFetcher is used to fetch the return value of parallel execution
    """
    def __init__(self, num_of_processes:int):
        """
        This class is used to fetch the return value of parallel execution.

        Parameters
        ----------
        num_of_processes : int
            number of processes to fetch result.
        """
        self.num_of_processes = num_of_processes
        self.results = [EmptyResult()] * num_of_processes

    def __setitem__(self, index, value):
        if 0 <= index < self.num_of_processes:
            self.results[index] = value
        else:
            raise IndexError(f"Index {index} out of range (0~{self.num_of_processes-1})")

    def __getitem__(self, index):
        if 0 <= index < self.num_of_processes:
            return self.results[index]
        else:
            raise IndexError(f"Index {index} out of range (0~{self.num_of_processes-1})")

    def __len__(self):
        return len(self.results)

    def wait_all_results(self):
        """
        Wait for all results and return the results. After calling this function, the `ParallelResultFetcher.results` will be reset to `EmptyResult`.
        """
        for i in range(self.num_of_processes):
            self.results[i] = self.results[i].recv()

        res = copy.deepcopy(self.results)
        self.results = [None] * self.num_of_processes
        return res

class RemoteObjectProxy:
    """
    RemoteObjectProxy is a proxy class for remote object.
    """
    class IsCallable:
        def __init__(self):
            pass

    def __init__(self, remote_obj_creator, paralle_execution=True, *args, **kwargs):
        """
        This class is a proxy class for remote object.

        Parameters
        ----------
        remote_obj_creator : function
            A function to create the remote object, this function should return the object to be controlled in child process.

        paralle_execution : bool, optional
            Whether to run the function in parallel. Default is True.

        *args
            The arguments for `remote_obj_creator`.
            
        **kwargs
            The keyword arguments for `remote_obj_creator
        """
        self.paralle_execution = paralle_execution
        self.parent_conn, child_conn = multiprocessing.Pipe()

        self.args = args
        self.kwargs = kwargs

        self.process = multiprocessing.Process(
            target=self._run_remote_object,
            args=(remote_obj_creator, child_conn),
            daemon=True
        )
        self.process.start()
        self.parent_conn.recv()  # wait for the remote object to be created

    def _run_remote_object(self, remote_obj_creator, conn):
        remote_obj = remote_obj_creator(*self.args, **self.kwargs)
        conn.send("ready")
        while True:
            try:
                cmd = conn.recv()
                if cmd == "close":
                    break

                func_name, not_test, args, kwargs = cmd
                try:
                    attr = getattr(remote_obj, func_name)
                    if not callable(attr):
                        result = getattr(remote_obj, func_name)
                        conn.send(result)
                    else:
                        if not_test:
                            result = getattr(remote_obj, func_name)(*args, **kwargs)
                            conn.send(result)
                        else:
                            is_callable = self.IsCallable()
                            conn.send(is_callable)
                except Exception as e:
                    conn.send(e)
            except (EOFError, ConnectionResetError):
                break

    def __getattr__(self, name):
        def dynamic_call(*args, **kwargs):
            self.parent_conn.send((name, True, args, kwargs))
            
            result = self.parent_conn.recv()
            if isinstance(result, Exception):
                raise result
            return result
        
        def dynamic_call_parallel(*args, **kwargs):
            self.parent_conn.send((name, True, args, kwargs))
            return self.parent_conn

        self.parent_conn.send((name, False, (), {}))
        res = self.parent_conn.recv()
        if isinstance(res, Exception):
            if self.paralle_execution:
                return res
            else:
                raise res
        if isinstance(res, self.IsCallable):
            if self.paralle_execution:
                return dynamic_call_parallel
            else:
                return dynamic_call
        else:
            return res

    def close(self):
        if self.process.is_alive():
            self.parent_conn.send("close")
            self.process.join()
        self.parent_conn.close()