import re
import pandas as pd
import argparse
import warnings


if_warning = 0
data_pattern = r" ?(\d+\.?\d*) ?"

def match_string(pattern, string):
    if re.match(pattern, string):
        return True
    else:
        return False

class Line:
    def __init__(self, pattern: str, *labels):
        self.full_pattern = "^"+pattern.replace("$$", data_pattern)+"$"
        self. labels = labels

    def analyse(self, string, line_number):
        if self.labels==tuple():
            return {}
        if match_string(self.full_pattern, string) == False:
            if if_warning == 0:
                return {}
            else:
                warnings.warn("The line(%s) can't match the patter(%s), skip line %d"%(string, self.full_pattern, line_number))
                return {}

        data = re.findall(data_pattern, string)
        if all(map(lambda x: "." in x, data)):
            data = [float(i) for i in data]
        else:
            data = [int(i) for i in data]
        if len(data)!=len(self.labels):
            raise Exception("The number of data(%d) is differenct from lables(%d), line %d"%(len(data), len(self.labels), line_number))
        return {l:d for l,d in zip(self.labels, data)}

class Section:
    def __init__(self, *Lines, times):
        self.lines = Lines
        self.times = times
    
class Data:
    def __init__(self, *Sections):
        self.sections = Sections
    def generate(self, file_path, encoding="utf-8"):
        with open(file_path, "r", encoding=encoding) as f:
            lines = [i.rstrip("\n") for i in f.readlines() if i.rstrip("\n")!=""]
        result = {}
        for s in self.sections:
            index = 0
            for i, line in enumerate(lines):
                temp = s.lines[index%len(s.lines)].analyse(line, i)
                if temp!={}:
                    index+=1
                    for j,k in temp.items():
                        if j in result:
                            result[j].extend([k]*s.times)
                        else:
                            result[j] = [k]*s.times
        return pd.DataFrame(result)
    
def extract_info_cli(data):
    parser = argparse.ArgumentParser(description="Process some files.")

    # Add the arguments
    parser.add_argument("input_file", type=str, help="The name of the input file.")
    parser.add_argument("-o", "--output_file", type=str, help="The name of the output file.")
    parser.add_argument("-e", "--encoding", default="utf-8", type=str, help="The encoding to use.")

    # Parse the arguments
    args = parser.parse_args()

    data.generate(args.input_file, args.encoding).to_csv(args.output_file, index=False, encoding=args.encoding)

def extract_info(data, file_path, encoding="utf-8"):
    data.generate(file_path, encoding)

if __name__=="__main__":
    d = Data(
        Section(
            Line("MKL number of threads: $$", "N_threads"),
            Line("cmkl_permut total time: $$", "cfunc_time"),
            Line("cmkl_permut permutation time: $$", "permut_time")
        ),
        Section(
            Line("Function permutation_mkl took $$ seconds to run.", "python_func_time")
        )
    )
    d.generate("./new_txt.txt").to_csv("test.csv", index=False)