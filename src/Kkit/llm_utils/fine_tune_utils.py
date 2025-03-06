from pydantic import BaseModel
from typing import Dict, Optional
import torch
from typing import List, Union
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainerCallback
)
import threading
import os
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, PeftModel
from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM


# Global training state tracker
class TrainingState:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_task: Optional[Dict] = None

    def update_state(self, **kwargs):
        with self.lock:
            if self.current_task is None:
                self.current_task = {}
            self.current_task.update(kwargs)

    def get_state(self):
        with self.lock:
            return self.current_task.copy() if self.current_task else None

training_state = TrainingState()

# Training progress callback
class ProgressCallback(TrainerCallback):
    def on_train_begin(self, args, state, control, **kwargs):
        training_state.update_state(
            total_epochs=state.num_train_epochs,
            total_steps=state.max_steps
        )

    def on_epoch_end(self, args, state, control, **kwargs):
        training_state.update_state(
            current_epoch=int(state.epoch),
            current_step=state.global_step
        )

    def on_step_end(self, args, state, control, **kwargs):
        training_state.update_state(
            current_step=state.global_step,
            total_steps=state.max_steps
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        if torch.cuda.is_available():
            logs["gpu_alloc_mem"] = torch.cuda.memory_allocated() / 1024**2
            logs["gpu_reserved_mem"] = torch.cuda.memory_reserved() / 1024**2
        else:
            logs["gpu_alloc_mem"] = 0
            logs["gpu_reserved_mem"] = 0

TRAIN_ROUND = 0

# Training configuration model
class TrainConfig(BaseModel):
    model_name: str = "Qwen/Qwen2.5-0.5B"
    lora_path: Optional[str] = None      # Path to existing LoRA model, train from scratch if None, train from existing model if not None
    lora_rank: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 3e-4
    max_length: Optional[int] = None
    model_save_path: Optional[str] = None
    response_template: Optional[str] = "<|im_start|>assistant\n"   # Template for response generation
    lora_target_modules: Union[List[str], str] = "all-linear"
    lora_modules_to_save: Optional[List[str]] = None #["lm_head", "embed_token"]
    tokenizer_padding_side: Optional[str] = "left"
    attn_implementation: str = "flash_attention_2"
    model_load_torch_dtype: str = "auto"
    train_arg_bf16: bool = True
    train_arg_fp16: bool = False
    train_round: int = TRAIN_ROUND

class MergeConfig(BaseModel):
    model_name: str
    lora_path: str
    model_output: str

# Core training function
def train_model(config: TrainConfig, dataset_path: str, base_path: str):
    # try:
    training_state.update_state(
        status="training",
        message="Initializing model..."
    )

    # Handle model save path
    if config.model_save_path:
        if os.path.isabs(config.model_save_path):
            model_path = config.model_save_path
        else:
            model_path = os.path.join(base_path, config.model_save_path)
    else:
        model_path = os.path.join(base_path, "lora_finetuned")
    
    # Ensure directory exists with write permission
    os.makedirs(model_path, exist_ok=True)
    if not os.access(model_path, os.W_OK):
        raise RuntimeError(f"No write permission for {model_path}")

    # Load model
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    if config.tokenizer_padding_side is not None:
        tokenizer.padding_side = config.tokenizer_padding_side
    base_model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        device_map="auto",
        torch_dtype=config.model_load_torch_dtype,
        attn_implementation=config.attn_implementation
    )

    if config.lora_path:
        # load LoRA model
        model = PeftModel.from_pretrained(
            base_model,
            config.lora_path,
            device_map="auto"
        )
    else:
        # Configure new LoRA
        lora_config = LoraConfig(
            r=config.lora_rank,
            lora_alpha=config.lora_alpha,
            target_modules=config.lora_target_modules,
            lora_dropout=config.lora_dropout,
            bias="none",
            modules_to_save=config.lora_modules_to_save,
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(base_model, lora_config)

    # Load and preprocess dataset
    training_state.update_state(message="Loading dataset...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def formatting_prompts_func(example):
        output_texts_ids = tokenizer.apply_chat_template(example["messages"])
        output_texts = tokenizer.decode(output_texts_ids)
        return output_texts
    
    # Example dataset format:
    # {"messages": [{"role": "user", "content": "What color is the sky?"},
    #       {"role": "assistant", "content": "It is blue."}]}

    trainer_args = SFTConfig(
        output_dir=model_path,
        per_device_train_batch_size=config.batch_size,
        max_seq_length=config.max_length if config.max_length else tokenizer.model_max_length,
        learning_rate=config.learning_rate,
        num_train_epochs=config.epochs,
        logging_dir=os.path.join(base_path, "logs"),
        report_to="wandb",
        run_name=f"{config.model_name}-{config.train_round}",
        logging_steps=10,
        save_strategy="epoch",
        bf16=config.train_arg_bf16,
        fp16=config.train_arg_fp16
    )

    trainer = SFTTrainer(
        model=model,
        data_collator=DataCollatorForCompletionOnlyLM(config.response_template, tokenizer=tokenizer),
        train_dataset=dataset,
        callbacks=[ProgressCallback],
        args=trainer_args,
        formatting_func=formatting_prompts_func
    )

    training_state.update_state(message="Training...")
    trainer.train()

    # Final state update
    training_state.update_state(
        status="completed",
        model_path=model_path
    )

def merge_model(
    model_name: str,
    lora_path: str,
    model_output: str,
    save_tokenizer: bool = True,
    save_config: bool = True,
    safe_serialization: bool = True,
    max_shard_size: str = "4GB",
    torch_dtype: str = "auto",
    push_to_hub: bool = False,
):
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch_dtype,
        trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    lora_model = PeftModel.from_pretrained(base_model, lora_path)
    
    merged_model = lora_model.merge_and_unload()

    merged_model.save_pretrained(
        model_output,
        safe_serialization=safe_serialization,
        max_shard_size=max_shard_size
    )

    if save_tokenizer:
        tokenizer.save_pretrained(
            model_output,
            legacy_format=True,
            safe_serialization=True
        )

    if save_config:
        merged_model.config.save_pretrained(model_output)

    if push_to_hub:
        merged_model.push_to_hub(model_output)
        tokenizer.push_to_hub(model_output)

    return merged_model, tokenizer
