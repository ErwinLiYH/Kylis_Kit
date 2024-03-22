"""
This module is used to recursively traverse a file and extract the data according to the pattern loop.

It is allways used to extract the data from the code scalability testing result.

For example, the result file is:

```txt
number of threads: 1
execution time: 0.10s
number of threads: 2
execution time: 0.21s
number of threads: 3
execution time: 0.31s
```

The pattern loop is:

```
number of threads: $$
execution time: $$
```

Data extractor can be built as:
    
```python
#test.py
from Kkit.scaling_code import Data, Section, Line, extract_info_cli

d = Data(
    Section(
        Line("number of threads: $$", "N_threads"),
        Line("execution time: $$", "execution_time")
    )
)

extract_info_cli(d)
```

Then run the extractor:

```python
# use --help to see the help information
python test.py --help

# run the command
python test.py scalability_result.txt -o test.csv
```

The result will be saved in the test.csv file as a table:

```csv
N_threads,execution_time
1,0.10
2,0.21
3,0.31
```
"""

import re
import pandas as pd
import argparse
import warnings


if_warning = 0
"""@private"""
data_pattern = r" ?(\d+\.?\d*) ?"
"""@private"""

def match_string(pattern, string):
    """@private"""
    if re.match(pattern, string):
        return True
    else:
        return False

class Line:
    def __init__(self, pattern: str, *labels):
        """
        Initialize the Line object.

        Parameters:
        ------------
        pattern: str
            The pattern of the line. The pattern should be like "number of threads: $$", where "$$" is the data place.

        *labels: str
            The labels of the data, namely the column name of this data in table.
            For example, the pattern is "number of threads: $$", the label can be "number of threads".
            Can be multiple labels. Like "number of threads: $$, execution time: $$", the labels can be "number of threads" and "execution time".
            ```python
            Line("number of threads: $$, execution time: $$", "number of threads", "execution time")
            ```
        """
        self.full_pattern = "^"+pattern.replace("$$", data_pattern)+"$"
        """@private"""
        self.labels = labels
        """@private"""

    def analyse(self, string, line_number):
        """@private"""
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
    def __init__(self, *Lines):
        """
        Initialize the Section object.

        A Section object can contain multiple Line objects.

        Parameters:
        ------------
        *Lines: Line
            The Line objects in this section.
        """
        self.lines = Lines
    
class Data:
    def __init__(self, *Sections):
        """
        Initialize the Data object.

        A Data object can contain multiple Section objects.

        Parameters:
        ------------
        *Sections: Section
            The Section objects in this data.
        """
        self.sections = Sections
    def generate(self, file_path, encoding="utf-8"):
        """@private"""
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
                            result[j].append(k)
                        else:
                            result[j] = [k]
        return pd.DataFrame(result)
    
def extract_info_cli(data: Data):
    """
    Initialize the command line interface for the data extractor.

    Parameters:
    ------------
    data: Data
        The Data object to extract the data.

    Returns:
    ------------
    None
    """
    parser = argparse.ArgumentParser(description="Process some files.")

    # Add the arguments
    parser.add_argument("input_file", type=str, help="The name of the input file.")
    parser.add_argument("-o", "--output_file", type=str, help="The name of the output file.")
    parser.add_argument("-e", "--encoding", default="utf-8", type=str, help="The encoding to use.")

    # Parse the arguments
    args = parser.parse_args()

    data.generate(args.input_file, args.encoding).to_csv(args.output_file, index=False, encoding=args.encoding)

def extract_info(data: Data, file_path: str, encoding="utf-8"):
    """
    Extract the data from the file.

    Recommend to use the `extract_info_cli` function, becauseof the flexibility.

    Parameters:
    ------------
    data: Data
        The Data object to extract the data.

    file_path: str
        The path of the file.

    encoding: str
        The encoding of the file. Default is "utf-8".

    Returns:
    ------------
    pd.DataFrame
        The data extracted from the file.
    """
    return data.generate(file_path, encoding)

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