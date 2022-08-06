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
    
def store_result(path, name, Aobject=None):
    if Aobject == None:
        try:
            print("find \"%s\" in global variable"%name)
            Aobject = globals()["name"]
            print("store \"%s\" to %s"%(name, os.path.join(path, name)))
        except:
            print("variable \"%s\" does not exist!"%name)
    with open(os.path.join(path, name), "wb") as f:
        pickle.dump(Aobject, f)