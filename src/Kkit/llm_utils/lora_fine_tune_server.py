import os
import argparse
import threading
import tempfile
import wandb
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, status, Depends, Form
from Kkit.llm_utils.fine_tune_utils import (
    train_model,
    TrainConfig,
    MergeConfig,
    training_state,
    merge_model,
)


# Initialize FastAPI application
app = FastAPI(title="LoRA Training Service")

def train_model_server(config: TrainConfig, dataset_path: str, base_path: str):
    try:
        train_model(config, dataset_path, base_path)
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

def parse_config(config: str = Form(...)) -> TrainConfig:
    try:
        return TrainConfig(**json.loads(config))
    except Exception as e:
        raise HTTPException(422, detail=str(e))

# API endpoints
@app.post(
    "/train",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new training job"
)
def start_training(
    config: TrainConfig = Depends(parse_config),
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

    print(config)

    thread = threading.Thread(
        target=train_model_server,
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

@app.post("/merge", summary="合并LoRA适配器到基础模型")
def merge(config: MergeConfig):
    try:
        merge_model(
            model_name=config.model_name,
            lora_path=config.lora_path,
            model_output=config.model_output
        )
        
        return {
            "status": "success",
            "message": "merging finished",
            "output_path": config.model_output
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": f"merging failed: {str(e)}"
            }
        )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server listening host")
    parser.add_argument("--port", type=int, default=8000, help="Server listening port")
    parser.add_argument("--base_path", required=True, type=str, help="Base directory for model outputs")
    args = parser.parse_args()

    # Validate base path
    if not os.path.exists(args.base_path):
        os.makedirs(args.base_path, exist_ok=True)
    if not os.path.isdir(args.base_path):
        raise ValueError(f"Base path {args.base_path} is not a directory")

    app.state.base_path = os.path.abspath(args.base_path)

    # Start server
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

# Main entry point
if __name__ == "__main__":
    main()