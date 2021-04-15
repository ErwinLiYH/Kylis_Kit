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

if __name__=="__main__":
    a = ["a","b","c","d"]
    b = [1,2,3,4]
    c = [3,4,7,5]
    dic = merge_list_to_dic(a,b)
    print(sort_dic_by_value(dic,True))
    print(sort_multi_list(a,b,c,by=2,my_reverse=True))