import subprocess
import json
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from contextlib import asynccontextmanager
import threading
import argparse


server_lock = threading.Lock()
llama_server = None

class ServerConfig(BaseModel):
    model_name: str
    configs: Dict[str, Any]
    server_path: str = "./llama-server"

class SwitchRequest(BaseModel):
    new_model_name: str
    new_configs: Dict[str, Any]

class LlamaServer:
    def __init__(self, model_name: str, configs: Dict[str, Any], server_path: str):
        self.server_path = server_path
        self.model_name = model_name
        self.configs = configs.copy()
        self.process = None

    def _convert_configs_to_args(self) -> list:
        args = []
        for key, value in self.configs.items():
            if key.startswith("-"):
                arg_name = key
            else:
                arg_name = f"--{key.replace('_', '-')}"
            
            if isinstance(value, bool):
                if value:
                    args.append(arg_name)
            else:
                args.extend([arg_name, str(value)])
        return args

    def start(self):
        if self.process and self.process.poll() is None:
            raise RuntimeError("Server is already running")

        cmd = [self.server_path]
        cmd.extend(["--model", self.model_name])
        cmd.extend(self._convert_configs_to_args())

        try:
            self.process = subprocess.Popen(cmd)
            time.sleep(1)
            if self.process.poll() is not None:
                raise RuntimeError(f"Server failed to start. Exit code: {self.process.returncode}")
        except Exception as e:
            self.process = None
            raise RuntimeError(f"Error starting server: {str(e)}")

    def stop(self):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None

    def switch(self, new_model_name: str, new_configs: Dict[str, Any]):
        self.stop()
        self.model_name = new_model_name
        self.configs = new_configs.copy()
        self.start()

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server...")
    yield
    print("Stopping server...")
    global llama_server
    if llama_server and llama_server.is_running():
        llama_server.stop()

app = FastAPI(lifespan=lifespan)

@app.post("/wrapper_start")
def start_server(config: ServerConfig):
    global llama_server
    with server_lock:
        if llama_server and llama_server.is_running():
            raise HTTPException(status_code=400, detail="Server is already running")
        
        try:
            llama_server = LlamaServer(
                model_name=config.model_name,
                configs=config.configs,
                server_path=config.server_path
            )
            llama_server.start()
            return {
                "status": "success",
                "message": f"Server started with model: {config.model_name}",
                "model": config.model_name,
                "config": config.configs
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/wrapper_switch")
def switch_model(request: SwitchRequest):
    global llama_server
    with server_lock:
        if not llama_server or not llama_server.is_running():
            raise HTTPException(status_code=400, detail="Server is not running")
        
        try:
            llama_server.switch(
                new_model_name=request.new_model_name,
                new_configs=request.new_configs
            )
            return {
                "status": "success",
                "message": f"Switched to model: {request.new_model_name}",
                "new_model": request.new_model_name,
                "new_config": request.new_configs
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/wrapper_stop")
def stop_server():
    global llama_server
    with server_lock:
        if not llama_server or not llama_server.is_running():
            raise HTTPException(status_code=400, detail="Server is not running")
        
        try:
            llama_server.stop()
            return {"status": "success", "message": "Server stopped"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/wrapper_status")
def get_status():
    global llama_server
    status = {
        "is_running": False,
        "current_model": None,
        "current_config": None
    }
    
    if llama_server and llama_server.is_running():
        status.update({
            "is_running": True,
            "current_model": llama_server.model_name,
            "current_config": llama_server.configs
        })
    
    return status

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server listening host")
    parser.add_argument("--port", type=int, default=8001, help="Server listening port")
    args = parser.parse_args()
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()