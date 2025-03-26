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
print(time.time()-start_time)  # should be around 11 seconds(last object sleep 9+2 seconds)