from datasets import load_dataset
from Kkit.llm_utils.data_process import input_output_to_messages
from Kkit.llm_utils.lora_fine_tune_server import train_model, TrainConfig, training_state
import os
import torch


DATA_PATH = 'self_cognition.jsonl'
NAME = 'xxx'
AUTHOR = 'xxxx'
BASE_PATH = os.path.dirname(__file__)

data = load_dataset('json', data_files=os.path.join(BASE_PATH, DATA_PATH), split='train')
data = input_output_to_messages('query', 'response', data)

data = data.map(lambda x: {"messages": [{"role": m["role"], "content": m["content"].replace("{{NAME}}", NAME).replace("{{AUTHOR}}", AUTHOR)} for m in x['messages']]})

data_save_path = os.path.join(BASE_PATH, "self_cognition_processed.jsonl")
data.to_json(data_save_path, lines=True, force_ascii=False)

train_config = TrainConfig()
train_config.epochs = 10

print('Data processed, start training...')
train_model(train_config, data_save_path, BASE_PATH)
print(training_state.get_state())
