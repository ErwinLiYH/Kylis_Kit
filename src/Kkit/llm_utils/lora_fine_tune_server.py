import os
import argparse
import threading
import tempfile
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File, status
from pydantic import BaseModel
from typing import Dict, Optional
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    TrainerCallback
)
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, PeftModel
from trl import SFTConfig, SFTTrainer, DataCollatorForCompletionOnlyLM


# Initialize FastAPI application
app = FastAPI(title="LoRA Training Service")

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
    lora_target_modules: List[str] = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# Core training function
def train_model(config: TrainConfig, dataset_path: str, base_path: str):
    try:
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
        base_model = AutoModelForCausalLM.from_pretrained(
            config.model_name,
            device_map="auto",
            torch_dtype="auto"
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
                modules_to_save=config.lora_target_modules,
                task_type="CAUSAL_LM"
            )
            model = get_peft_model(base_model, lora_config)

        # Load and preprocess dataset
        training_state.update_state(message="Loading dataset...")
        dataset = load_dataset("json", data_files=dataset_path, split="train")

        def formatting_prompts_func(example):
            output_texts = tokenizer.chat_template(example["messages"])
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
            logging_steps=10,
            save_strategy="epoch",
            fp16=True,
        )

        trainer = SFTTrainer(
            model=model,
            data_collator=DataCollatorForCompletionOnlyLM(config.response_template, tokenizer=tokenizer),
            train_dataset=dataset,
            callbacks=[ProgressCallback()],
            args=trainer_args,
            formatting_func=formatting_prompts_func
        )

        trainer.train()

        # Save tokenizer separately
        tokenizer.save_pretrained(model_path)

        # Final state update
        training_state.update_state(
            status="completed",
            model_path=model_path
        )

    except Exception as e:
        training_state.update_state(
            status="error",
            message=str(e),
        )
    finally:
        # Cleanup temporary files
        if os.path.exists(dataset_path):
            try:
                os.remove(dataset_path)
            except Exception as e:
                print(f"Error cleaning up temp file: {str(e)}")

# API endpoints
@app.post(
    "/train",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new training job"
)
def start_training(
    config: TrainConfig,
    file: UploadFile = File(..., description="Training data (JSON format)")
):
    current_state = training_state.get_state()
    if current_state and current_state.get("status") == "training":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Training is already in progress"
        )

    # Save uploaded file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            content = file.file.read()
            tmp_file.write(content)
            dataset_path = tmp_file.name
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}"
        )

    # Start training thread
    training_state.update_state(
        status="training",
        config=config.model_dump(),
        dataset_path=dataset_path,
    )

    thread = threading.Thread(
        target=train_model,
        args=(config, dataset_path, app.state.base_path)
    )
    thread.start()

    return {"message": "Training job started successfully"}

@app.get("/status", summary="Get training status")
def get_status():
    state = training_state.get_state()
    if not state:
        return {"status": "idle"}
    
    response = {
        "status": state.get("status"),
        "message": state.get("message"),
        "current_step": state.get("current_step", 0),
        "total_steps": state.get("total_steps", 0),
        "current_epoch": state.get("current_epoch", 0),
        "total_epochs": state.get("total_epochs", 0)
    }
    
    if state.get("status") == "completed":
        response["model_path"] = state.get("model_path")
    elif state.get("status") == "error":
        response["error"] = state.get("message")
    
    return response

# Main entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000, 
                       help="Server listening port")
    parser.add_argument("--base_path", required=True, type=str,
                       help="Base directory for model outputs")
    args = parser.parse_args()

    # Validate base path
    if not os.path.exists(args.base_path):
        os.makedirs(args.base_path, exist_ok=True)
    if not os.path.isdir(args.base_path):
        raise ValueError(f"Base path {args.base_path} is not a directory")
    
    app.state.base_path = os.path.abspath(args.base_path)

    # Start server
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=args.port)
