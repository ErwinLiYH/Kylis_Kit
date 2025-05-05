import os
import argparse
import asyncio
import json
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field
from typing import Optional
import shutil
from typing import Dict, Any
from datetime import datetime
from ruamel.yaml import YAML
from contextlib import asynccontextmanager
from fastapi import Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App started!")
    yield
    print("App shutting down...")

app = FastAPI(lifespan=lifespan)
yaml = YAML(typ='rt')  # Round-trip YAML parser
yaml.preserve_quotes = True

app.state.subprocess_registry = {}

# Request models
class CommandRequest(BaseModel):
    command: str
    process_id: str

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]
    file_path: str
    modified_file_path: Optional[str] = Field(
        default=None,
        description="New file path to save modified config (optional)"
    )

class FileUploadResponse(BaseModel):
    filename: str
    saved_path: str
    file_size: int

# Utility functions
def validate_safe_path(base: Path, target: str) -> Path:
    """Prevent path traversal attacks"""
    resolved = (base / target).resolve()
    if not resolved.is_relative_to(base):
        raise HTTPException(status_code=403, detail="Path traversal attempt detected")
    return resolved

def deep_update(source: Dict, overrides: Dict) -> Dict:
    """Deep merge dictionaries"""
    for key, value in overrides.items():
        if isinstance(value, dict):
            source[key] = deep_update(source.get(key, {}), value)
        else:
            source[key] = value
    return source

def load_config(file_path: Path) -> Dict:
    """Load configuration based on file type"""
    suffix = file_path.suffix.lower()
    try:
        with open(file_path, 'r') as f:
            if suffix in ['.yaml', '.yml']:
                return yaml.load(f)
            elif suffix == '.json':
                return json.load(f)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading config: {str(e)}")

def save_config(config: Dict, file_path: Path):
    """Save configuration based on file type"""
    suffix = file_path.suffix.lower()
    try:
        with open(file_path, 'w') as f:
            if suffix in ['.yaml', '.yml']:
                yaml.dump(config, f)
            elif suffix == '.json':
                json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving config: {str(e)}")

def secure_filename(filename: str) -> Path:
    """Clean file path and name from illegal characters while preserving folder structure"""
    filename = filename.strip().replace(' ', '_')
    path = Path(filename)

    allowed_chars = set(".-_()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

    if path.parts[0] == '/':
        raise HTTPException(status_code=400, detail=f"Invalid filename {filename}, must be relative path")

    def clean_component(s):
        return ''.join(c for c in s if c in allowed_chars)

    cleaned_parts = [clean_component(part) for part in path.parts]  # Clean each parent folder
    for p in cleaned_parts:
        if p == '':
            raise HTTPException(status_code=400, detail=f"Invalid filename, {filename}")

    return Path(*cleaned_parts)

async def cleanup_process_registry():
    to_delete = []

    for pid, info in app.state.subprocess_registry.items():
        if info["status"] == "exited":
            to_delete.append(pid)

    for pid in to_delete:
        del app.state.subprocess_registry[pid]
        print(f"[CLEANUP] Removed exited process: {pid}")

# API endpoints
@app.get("/status")
async def get_status():
    return {
        "status": "running",
        "llama_factory_path": str(app.state.llama_factory_path),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/cleanup")
async def manual_cleanup():
    cleaned_pids = await cleanup_process_registry()
    return {
        "message": "Cleanup completed",
        "cleaned_processes": cleaned_pids,
        "count": len(cleaned_pids)
    }

@app.get("/processes")
async def list_processes():
    return {
        "processes": {
            pid: {
                "pid": info["pid"],
                "command": info["command"],
                "status": info["status"],
                "start_time": info["start_time"],
                "returncode": info.get("returncode")
            }
            for pid, info in app.state.subprocess_registry.items()
        }
    }

@app.get("/config/{file_path:path}")
async def get_config(file_path: str):
    config_path = validate_safe_path(app.state.llama_factory_path, file_path)
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail="Configuration file not found")
    return load_config(config_path)

@app.post("/update_yaml")
async def update_yaml(request: ConfigUpdateRequest):
    config_path = validate_safe_path(app.state.llama_factory_path, request.file_path)
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail="Configuration file not found")
    if config_path.suffix.lower() not in ['.yaml', '.yml']:
        raise HTTPException(status_code=400, detail="Not a YAML file")
    
    dest_path = config_path
    if request.modified_file_path:
        dest_path = validate_safe_path(
            app.state.llama_factory_path, 
            request.modified_file_path
        )
    
    try:
        config = load_config(config_path)
        updated_config = deep_update(config, request.config)
        save_config(updated_config, dest_path)
        return {"status": "success", "message": "YAML config updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update_json")
async def update_json(request: ConfigUpdateRequest):
    config_path = validate_safe_path(app.state.llama_factory_path, request.file_path)
    if not config_path.is_file():
        raise HTTPException(status_code=404, detail="Configuration file not found")
    if config_path.suffix.lower() != '.json':
        raise HTTPException(status_code=400, detail="Not a JSON file")
    
    dest_path = config_path
    if request.modified_file_path:
        dest_path = validate_safe_path(
            app.state.llama_factory_path, 
            request.modified_file_path
        )
    
    try:
        config = load_config(config_path)
        updated_config = deep_update(config, request.config)
        save_config(updated_config, dest_path)
        return {"status": "success", "message": "JSON config updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload_data", response_model=FileUploadResponse)
async def upload_data(file: UploadFile = File(...)):
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        raise HTTPException(400, detail="Invalid filename")
    
    save_path = app.state.llama_factory_path / safe_filename
    save_dir = save_path.parent

    if not save_dir.exists():
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(500, detail=f"Failed to create directory: {str(e)}")
    
    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {
            "filename": safe_filename,
            "saved_path": str(save_path.relative_to(app.state.llama_factory_path)),
            "file_size": save_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(500, detail=f"File upload failed: {str(e)}")
    finally:
        await file.close()

@app.post("/run_command")
async def run_command(api_request: Request, request: CommandRequest):
    try:
        process = await asyncio.create_subprocess_shell(
            request.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=app.state.llama_factory_path,
        )

        process_id = request.process_id
        if process_id in app.state.subprocess_registry:
            process_id += str(uuid.uuid4())
        app.state.subprocess_registry[process_id] = {
            "pid": process.pid,
            "command": request.command,
            "status": "running",
            "process": process,
            "start_time": datetime.now().isoformat()
        }

        async def stream_output():
            try:
                stdout = process.stdout
                stderr = process.stderr

                while True:
                    if await api_request.is_disconnected():
                        print(f"Client disconnected. Terminating subprocess {process.pid}")
                        process.terminate()
                        break
                    stdout_task = asyncio.create_task(stdout.readline())
                    stderr_task = asyncio.create_task(stderr.readline())

                    done, pending = await asyncio.wait(
                        [stdout_task, stderr_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    for task in done:
                        try:
                            line_bytes = task.result()
                            if not line_bytes:
                                continue  # EOF on one stream

                            line = line_bytes.decode(errors='replace').rstrip()

                            if task == stdout_task:
                                yield f"STDOUT: {line}\n"
                            elif task == stderr_task:
                                yield f"STDERR: {line}\n"

                        except Exception as e:
                            yield f"[ERROR reading stream: {str(e)}]\n"

                    # Cancel and discard pending task to avoid hanging
                    for task in pending:
                        task.cancel()
                        try:
                            await task  # Await cancelled task to silence warnings
                        except:
                            pass

                    # Check process termination and both streams closed
                    if process.stdout.at_eof() and process.stderr.at_eof():
                        break

                await process.wait()
                yield f"\n[Process exited with code: {process.returncode}]\n\n"

            except Exception as e:
                try:
                    process.terminate()
                    await process.wait()
                except:
                    pass
                yield f"\n[Error: {str(e)}]\nkill sub-process\n\n"

            finally:
                app.state.subprocess_registry[process_id]["status"] = "exited"
                app.state.subprocess_registry[process_id]["returncode"] = process.returncode


        return StreamingResponse(stream_output(), media_type="text/plain", headers={"X-Process-ID": process_id})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--llama_factory_path", type=str, required=True,
                       help="Path to LLaMA-Factory source code")
    parser.add_argument("--port", type=int, default=9000,
                       help="Server port number")
    args = parser.parse_args()
    
    factory_path = Path(args.llama_factory_path).resolve()
    if not factory_path.exists():
        raise RuntimeError(f"LLaMA-Factory path does not exist: {factory_path}")
    
    app.state.llama_factory_path = factory_path
    uvicorn.run(app, host="0.0.0.0", port=args.port)

if __name__ == "__main__":
    main()