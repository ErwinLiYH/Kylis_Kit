"""
# Kylis kit

Some personal tools for python programming.

## Modules

- `llm_utils`: Provide a LLM fine-tuning API and some utilities (in server).
- `mder`: Maltilthreading m3u8 download module. Support download m3u8 file and convert it to mp4. Support resume download.
- `scaling_code`: Extract information from recurring patterns in text files, allways used in scaling test.
- `timeout`: Run a command with timeout and retry times.
- `color`:
    1. Convert color between RGB , HSV and hex.
    2. Convert string to color by extracting dominant color from images related to the string.
- `encryption`: Encrypt and decrypt files.
- `str2latex`: Convert string to latex format.
- `fundict`: 
    1. Nonedict: A dictionary that returns None when the key is not found.
    2. AbbrDict: A dictionary that can use key abbreviation to get value.
- `utils`: Some useful functions.

More information can be found at the help of each sub-module.

## Install and import

```bash
pip install git+https://github.com/erwinliyh/kylis_kit@main
```

```python
import Kkit
# or
from Kkit import <module>
```

Some modules need extra packages, you can install them by:

```bash
pip install git+https://github.com/erwinliyh/kylis_kit@main[module_name]
```

All modules that need extra requirements:

1. `color` : ["haishoku", "colorsys", "numpy", "requests"]
2. `encryption` : ["cryptography"]
3. `scaling` : ["pandas"]
4. `str2latex` : ["numpy"]
5. `llm` : ["fastapi", "torch", "torchvision", "torchaudio", "uvicorn", "wanb",
            "transformers", "datasets", "peft", "python-multipart", "trl[all]"]

Other modules are pure python code with just build-in packages.
"""
from .utils import *