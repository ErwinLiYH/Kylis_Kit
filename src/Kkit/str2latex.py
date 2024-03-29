"""
This module is used to transfer between LaTex bmatrix and numpy array.

Example:

```python
from Kkit import str2latex

bmatrix = r'''
\\begin{bmatrix}
1 & 2 & 3 \\\\
4 & 5 & 6
\end{bmatrix}
'''

array = str2latex.bmatrix2numpy(bmatrix)

print(array)
# [[1 2 3]
#  [4 5 6]]

bmatrix = str2latex.numpy2bmatrix(array)

print(bmatrix)

# \begin{bmatrix}
# 1&2&3\\
# 4&5&6
# \end{bmatrix}
```
"""

# Transfer between string and object
# Author:walkureHHH
# Last modify:2020/10/14
import numpy

class latex_str_error(Exception):
    pass

def bmatrix2numpy(latex_str)->numpy.array:
    """
    Transfer a latex bmatrix to a numpy array

    Parameters
    ----------
    latex_str : str
        The latex string

    Returns
    -------
    numpy.array
        The numpy array
    """
    latex_str = latex_str.strip()
    if latex_str.startswith('\\begin{bmatrix}') and latex_str.endswith('\\end{bmatrix}'):
        latex_str = latex_str.replace('\\begin{bmatrix}','').replace('\\end{bmatrix}','')
        rows = latex_str.split('\\\\')
        lis = [i.split('&') for i in rows]
        return numpy.array(lis)
    else:
        raise latex_str_error("this is not a bmatrix,please check it again")

def numpy2bmatrix(array)->str:
    """
    Transfer a numpy array to a latex bmatrix

    Parameters
    ----------
    array : numpy.array
        The numpy array

    Returns
    -------
    str
        The latex string
    """
    s = '\\begin{bmatrix}\n'
    shape = numpy.shape(array)
    str_list = array.tolist()
    for i in range(0,shape[0]):
        for j in range(0,shape[1]):
            if j < shape[1]-1:
                s += (str(str_list[i][j])+'&')
            else:
                s += str(str_list[i][j])
        if i < shape[0]-1:
            s += '\\\\\n'
        else:
            s += '\n\\end{bmatrix}'
    return s

# def str2list(list_str,mod_str = ',')->list:
#     list_str = list_str.strip().replace('\n',mod_str)
#     return list_str.split(mod_str)

# def list2str(list_,mod_str=',')->str:
#     result = ''
#     for i in range(0,len(list_)):
#         if i < len(list_)-1:
#             result += (str(list_[i])+mod_str)
#         else:
#             result += str(list_[i])
#     return "[%s]"%result

# if __name__ == "__main__":
#     lista = [1,2,3,4,5,6]
#     print(lista)
#     print(list2str(lista))
