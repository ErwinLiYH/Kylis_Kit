import time
import pickle
import os
from logging import Logger

def print_list(Alist, num_of_columns=None, separator_in_line=" , ", separator_between_line="\n", prefix="", verbose=True):
    length = len(Alist)
    if num_of_columns == None:
        num_of_columns = length
    print(prefix, end="")
    for i in range(length):
        if i%num_of_columns != (num_of_columns-1):
            if i == (length-1):
                print(Alist[i], end = separator_between_line)
            else:
                print(Alist[i], end = separator_in_line)
        else:
            print(Alist[i], end = separator_between_line)
    if verbose:
        print("\nlength: %d"%length)

def conclude_list(Alist):
    result = {}
    for i in Alist:
        if i in result:
            result[i] += 1
        else:
            result[i] = 1
    return result

def conclude_list2(a_list):
    no_duplicate = []
    for i in a_list:
        if i not in no_duplicate:
            no_duplicate.append(i)
    count_list = []
    for i in no_duplicate:
        count_list.append(a_list.count(i))
    return no_duplicate, count_list

def time_string():
    return time.strftime("%Y-%m-%d-%H%M%S", time.localtime())

def load(path_name, encoding="b", lines=False, removeCL=True):
    if encoding=="b":
        with open(path_name, "rb") as f:
            return pickle.load(f)
    else:
        with open(path_name, "r", encoding=encoding) as f:
            if lines:
                content = f.readlines()
                if removeCL:
                    content = [i.rstrip("\n") for i in content]
            else:
                content = f.read()
            return content
    
def store(path_name, Aobject=None, encoding="b"):
    if path_name==None:
        return
    path = os.path.dirname(path_name)
    if path!="" and path!="./" and os.path.exists(path)==False:
        os.makedirs(path)
    if encoding=="b":
        with open(path_name, "wb") as f:
            pickle.dump(Aobject, f)
    else:
        with open(path_name, "w", encoding=encoding) as f:
            f.write(Aobject)

def sort_dic_by_value(dic,my_reverse=False):
    return {k: v for k, v in sorted (dic.items(), key=lambda item: item[1], reverse=my_reverse)}

def sort_multi_list(*multi_list,by = 1,my_reverse=False):
    li = zip(*multi_list)
    length = len(multi_list)
    if length == 1:
        raise Exception("please input multiple lists, not just 1")
    else:
        if by in range(0,length):
            x = sorted(li, key=lambda i:i[by],reverse=my_reverse)
            return x
        else:
            raise Exception("the value of 'by' can only be 0 or 1")
           
def find_key_by_value(value, dic):
    for k,v in dic.items():
        if v == value:
            return k

def merge_list_to_dic(list1,list2):
    li = zip(list1,list2)
    return {k:v for (k,v) in li}

def list_in_list(list1, list2, X=None):
    boolean_list = []
    for i in list1:
        boolean_list.append(i in list2)
    if X==None:
        return boolean_list
    elif X=="all":
        return False not in boolean_list
    elif X=="any":
        return True in boolean_list
    
def klistdir(path, with_prefix=True):
    if with_prefix:
        return [os.path.join(path, i) for i in os.listdir(path)]
    else:
        return os.listdir(path)
    
class PathJoin:
    def __init___(self, base_path):
        self.base_path = base_path
    def path(self, path):
        return os.path.join(self.base_path ,path)

def kstrip(string, key):
    s = string
    if len(s)<len(key):
        return s
    if s[0:len(key)] == key:
        s = s[len(key):]
    if s[-len(key):] == key:
        s = s[0:-len(key)]
    return s

def retry(retry_times=3, verbose=False, record=False):
    """
    Retry decorator: retry the function for retry_times times if exception occurs

    Parameters:
    --------------
    retry_times: int
        the number of times to retry the function

    verbose: bool
        whether to print the retry information

    record: bool or Logger
        whether to record the retry information, if True, raise the exception, if Logger, record the exception in log, if False, do nothing.

    Example:
    ```python
    @retry(retry_times=3)
    def test():
        print("test")
        raise Exception("test")
    ```
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(retry_times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if verbose:
                        print(f"function {func.__name__} failed, retrying {i+1}/{retry_times}")
                    if i == retry_times-1:
                        if isinstance(record, Logger):
                            record.exception(f"function {func.__name__} failed after {retry_times} retries")
                        elif record:
                            raise e
        return wrapper
    return decorator

if __name__=="__main__":
    kstrip("asd-asd","asd")