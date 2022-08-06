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