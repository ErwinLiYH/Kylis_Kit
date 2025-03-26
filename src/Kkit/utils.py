import time
import pickle
import os
from logging import Logger
from functools import reduce
import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler


def print_list(Alist, num_of_columns=None, separator_in_line=" , ", separator_between_line="\n", prefix="", show_length=False, align=True):
    """
    Print a list in a pretty table format.
    
    You can specify the number of columns, the separator between elements in a line, the separator between lines, the prefix of the table, whether to show the length of the list, and whether to align the elements in the list. The str() of each element should be in one line for pretty.

    Parameters
    ----------
    Alist : list
        the list to be printed

    num_of_columns : int or None, default None
        the number of columns to be printed in one line. If None, the number of columns will be the length of the list

    separator_in_line : str, default " , "
        the separator between elements in a line

    separator_between_line : str, default "\\n"
        the separator between lines

    prefix : str, default ""
        the prefix of the table

    show_length : bool, default False
        whether to show the length of the list

    align : bool, default True
        whether to align the elements in the list

    Examples
    --------
    >>> a = [1,12,123,1234,12345,"123456",1234567,12345678,"123456789"]
    >>> print_list(a, num_of_columns=5, prefix="The example list is:")
    The example list is:        1 ,        12 ,       123 ,      1234 ,     12345
                           123456 ,   1234567 ,  12345678 , 123456789
    """
    align_length = 0
    if align:
        for i in Alist:
            if len(str(i))>align_length:
                align_length = len(str(i))
    length_perfix = len(prefix)+align_length
    length = len(Alist)
    if num_of_columns == None:
        num_of_columns = length
    print(prefix, end="")
    for i in range(length):
        line_index = i%num_of_columns
        if i == 0 or line_index != 0:
            alignL = align_length
        else:
            alignL = length_perfix
        if line_index == (num_of_columns-1) or i == (length-1):
            separator = separator_between_line
        else:
            separator = separator_in_line
        print(f"{Alist[i]:>{alignL}}", end=separator)
    if show_length:
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
    """
    load the object from the file, binary or text.

    Parameters
    ----------
    path_name : str
        The path of the file

    encoding : str, default "b"
        The encoding of the file, "b" for binary, text encoding ("utf-8", "gbk", etc.) for text

    lines : bool, default False
        Whether to read the file as lines. If True, return a list of lines. If False, return the whole content.

    removeCL : bool, default True
        Whether to remove the line break character at the end of each line. Only valid when lines is True.
    """
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
    """
    store the object to the file, binary or text.

    Parameters
    ----------
    path_name : str
        The path of the file

    Aobject : Any, default None
        The object to be stored, if None, do nothing. Should be serializable if encoding is "b".

    encoding : str, default "b"
        The encoding of the file, "b" for binary, text encoding ("utf-8", "gbk", etc.) for text
    """
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
    def __init__(self, base_path):
        self.base_path = base_path
    def __call__(self, path):
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

def retry(retry_times=3, raise_exception=False, record_retry=False):
    """
    Retry decorator: retry the function for retry_times times if exception occurs

    Parameters
    ----------
    retry_times : int
        the number of times to retry the function

    raise_exception : bool or logging.Logger
        whether to raise the exception after retry_times retries, or the logger to record the exception. If False, the exception will not be raised, If True, the exception will be raised. If a logger is provided, the exception will be recorded in the logger.
        
    record_retry : bool or logging.Logger
        whether to record the retry information, or the logger to record the retry information. If False, the retry information will not be recorded, If True, the retry information will be printed. If a logger is provided, the retry information will be recorded in the logger.

    Examples
    --------
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
                    if isinstance(record_retry, Logger):
                        record_retry.exception(f"function {func.__name__} failed, retrying {i+1}/{retry_times}")
                    elif record_retry:
                        print(f"function {func.__name__} failed, retrying {i+1}/{retry_times}")
                    if i == retry_times-1:
                        if isinstance(raise_exception, Logger):
                            raise_exception.exception(f"function {func.__name__} failed after {retry_times} retries")
                        elif raise_exception:
                            raise e
        return wrapper
    return decorator

def Pipeline(*funcs):
    """
    Combine multiple functions into a pipeline function.
    Execute the functions in order from left to right.
    """
    def pipeline_two(f, g):
        return lambda x: g(f(x))
    return reduce(pipeline_two, funcs, lambda x: x)

def init_logger(
    logger_name: str,
    log_file: Optional[str] = None,
    max_mb: Optional[int] = None
) -> logging.Logger:
    """
    Quickly initialize a logger with file or stdout output.
    
    Parameters
    ----------

        logger_name: Name of the logger

        log_file: Path to log file. If None, outputs to stdout

        max_mb: Maximum log file size in MB. None means no size limit.
                Only applies when log_file is specified.
    
    Returns
    -------
        Configured logging.Logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)  # Default level: INFO

    # Clear existing handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Configure formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure handler based on parameters
    if log_file:
        if max_mb is not None:
            # Use rotating files with size limit
            handler = RotatingFileHandler(
                log_file,
                maxBytes=max_mb * 1024 * 1024,
                backupCount=3  # Keep 3 backup copies
            )
        else:
            # Use regular file handler without size limit
            handler = logging.FileHandler(log_file)
    else:
        # Output to stdout if no file specified
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

if __name__=="__main__":
    kstrip("asd-asd","asd")