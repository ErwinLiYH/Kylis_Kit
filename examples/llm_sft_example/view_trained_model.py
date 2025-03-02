from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_MODEL = "you/base/model"
LORA_PATH = "your/lora/path"

model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(LORA_PATH)

model = PeftModel.from_pretrained(model, LORA_PATH)

prompt = "who are you?"
messages = [
    {"role": "user", "content": prompt}
]

text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=512,
    eos_token_id=151645  # <|im_end|>
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

print(len(generated_ids[0]))

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(response)