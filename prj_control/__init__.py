import time
import pickle
import os

# def mkprj(name="flavour_wheel_test", structure=
# ["logs","results/pic_results","results/linkage_results","results/web_results","results/word_results","models/glove"]):
#     # os.mkdir(name)
#     for i in structure:
#         os.makedirs(os.path.join(name ,i))

def time_string():
    return time.strftime("%Y-%m-%d-%H%M%S", time.localtime())

def load_result(path_name):
    with open(path_name, "rb") as f:
        return pickle.load(f)
    
def store_result(path_name, Aobject):
    with open(path_name, "wb") as f:
        pickle.dump(Aobject, f)

def print_list(Alist, num_of_columns, separator_in_line=" , ", separator_between_line="\n"):
    length = len(Alist)
    for i in range(length):
        if i%num_of_columns != (num_of_columns-1):
            if i == (length-1):
                print(Alist[i], end = separator_between_line)
            else:
                print(Alist[i], end = separator_in_line)
        else:
            print(Alist[i], end = separator_between_line)
    print("\nlength: %d"%length)