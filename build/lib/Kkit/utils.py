import time
import pickle
import os

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

def time_string():
    return time.strftime("%Y-%m-%d-%H%M%S", time.localtime())

def load_result(path_name):
    with open(path_name, "rb") as f:
        return pickle.load(f)
    
def store_result(path_name, Aobject=None):
    path = os.path.dirname(path_name)
    file_name = os.path.basename(path_name)
    if type(Aobject) == type(None):
        if Aobject == None:
            print("find %s in globals"%file_name)
            try:
                Aobject=globals()[file_name]
                print("found and store %s in globals"%file_name)
            except:
                print("variable %s does not exist"%file_name)
    else:
        pass
    if path!="" and path!="./" and os.path.exists(path)==False:
        os.makedirs(path)
    with open(path_name, "wb") as f:
        pickle.dump(Aobject, f)

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

def merge_list_to_dic(list1,list2):
    li = zip(list1,list2)
    return {k:v for (k,v) in li}