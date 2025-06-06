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
from typing import List
from fastapi.logger import logger
from logging import StreamHandler, Formatter
import logging


server_lock = threading.Lock()
llama_server = None

class ServerConfig(BaseModel):
    model_name: str
    configs: Dict[str, Any]
    server_path: List[str] = ["./llama-server"]

class SwitchRequest(BaseModel):
    new_model_name: str
    new_configs: Dict[str, Any]

class LlamaServer:
    def __init__(self, model_name: str, configs: Dict[str, Any], server_path: List[str]):
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
            elif value == '':
                args.extend([arg_name])
            else:
                args.extend([arg_name, str(value)])
        return args

    def start(self, log_file: str = "llama_server.log"):
        if self.process and self.process.poll() is None:
            raise RuntimeError("Server is already running")
        cmd = (self.server_path).copy()
        if app.state.llama_cpp_or_vllm == "llama_cpp":
            cmd.extend(["--model", self.model_name])
        elif app.state.llama_cpp_or_vllm == "vllm":
            cmd.extend([self.model_name])
        cmd.extend(self._convert_configs_to_args())
        print(cmd)

        try:
            with open(log_file, "w") as log_f:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=log_f,
                    stderr=log_f,
                    text=True,
                )
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
        self.start(app.state.log_file)

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Run in {app.state.llama_cpp_or_vllm} mode...")
    yield
    logger.info("Stopping server...")
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
            llama_server.start(app.state.log_file)
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
    parser.add_argument("--log_file", type=str, default="./server.log", help="Log file path")
    parser.add_argument("--llama_cpp_or_vllm", "-lv", default="vllm", help="using `vllm` or `llama_cpp` as backend")
    args = parser.parse_args()
    args.llama_cpp_or_vllm in ["vllm", "llama_cpp"]
    app.state.log_file = args.log_file
    app.state.llama_cpp_or_vllm = args.llama_cpp_or_vllm
    handler = StreamHandler()
    formater = Formatter("%(levelname)s:     %(message)s")
    handler.setFormatter(formater)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()