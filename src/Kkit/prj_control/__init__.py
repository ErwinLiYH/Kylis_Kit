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