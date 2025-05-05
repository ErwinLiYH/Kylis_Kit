import requests
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import closing

class LLamaFactoryClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()  # Reuse TCP connections

    # ====================
    # API for System Status
    # ====================
    def get_server_status(self) -> Dict:
        """Get server status (GET /status)"""
        url = f"{self.base_url}/status"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def manual_cleanup(self) -> Dict:
        """Manually clean up processes (POST /cleanup)"""
        url = f"{self.base_url}/cleanup"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()

    def list_processes(self) -> Dict:
        """List all processes (GET /processes)"""
        url = f"{self.base_url}/processes"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    # ====================
    # Configuration Management APIs
    # ====================
    def get_config(self, file_path: str) -> Dict:
        """Get configuration file (GET /config/{file_path})"""
        url = f"{self.base_url}/config/{file_path.lstrip('/')}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def update_yaml_config(
        self,
        file_path: str,
        config: Dict,
        modified_file_path: Optional[str] = None
    ) -> Dict:
        """Update YAML configuration (POST /update_yaml)"""
        url = f"{self.base_url}/update_yaml"
        payload = {
            "file_path": file_path,
            "config": config,
            "modified_file_path": modified_file_path
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def update_json_config(
        self,
        file_path: str,
        config: Dict,
        modified_file_path: Optional[str] = None
    ) -> Dict:
        """Update JSON configuration (POST /update_json)"""
        url = f"{self.base_url}/update_json"
        payload = {
            "file_path": file_path,
            "config": config,
            "modified_file_path": modified_file_path
        }
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    # ====================
    # File Operation APIs
    # ====================
    def upload_data_file(
        self,
        file_path: Path,
        timeout: int = 30
    ) -> Dict:
        """Upload data file (POST /upload_data)"""
        url = f"{self.base_url}/upload_data"
        
        if not file_path.is_file():
            return {"error": "File not found"}
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f)}
            response = self.session.post(
                url,
                files=files,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

    # ====================
    # Command Execution APIs
    # ====================
    def run_command(
        self,
        command: str,
        output_file: Optional[str] = None,
        print_output: bool = True,
        process_id: Optional[str] = None
    ) -> Dict:
        """
        Execute a command and get streaming output (POST /run_command)
        Returns a generator containing process_id and real-time output
        """
        url = f"{self.base_url}/run_command"
        payload = {
            "command": command,
            "process_id": process_id or f"client_{id(self)}"
        }
        with closing(self.session.post(url, json=payload, stream=True)) as resp:
            resp.raise_for_status()
            
            # Get process_id
            process_id = resp.headers.get('X-Process-ID')
            if not process_id:
                raise ValueError("No process ID returned from server.")
            
            # Handle streaming output
            output_buffer = []
            file_handle = open(output_file, 'a') if output_file else None
            
            try:
                for chunk in resp.iter_content(chunk_size=4):
                    if chunk:  # Filter keep-alive empty chunks
                        decoded = chunk.decode('utf-8', errors='replace')
                        
                        # Real-time output to console
                        if print_output:
                            print(decoded, end='', flush=True)
                        
                        # Write to file (if specified)
                        if file_handle:
                            file_handle.write(decoded)
                            file_handle.flush()
                            
                        output_buffer.append(decoded)
            finally:
                if file_handle:
                    file_handle.close()
            
            return process_id, ''.join(output_buffer)

    # ====================
    # Other Utility Methods
    # ====================
    def close(self):
        """Close the client connection"""
        self.session.close()

# Usage examples
if __name__ == "__main__":
    client = LLamaClient("http://localhost:9000")
    
    # Example 1: Get server status
    print("Server Status:", client.get_server_status())
    
    # Example 2: Run a command and save output
    pid, result = client.run_command(
        command="echo 'Hello World' && sleep 2",
        output_file="output.log"
    )
    print("Command Result:", result)
    
    # Example 3: Upload a file
    upload_result = client.upload_data_file(Path("test_data.csv"))
    print("Upload Result:", upload_result)
    
    # Example 4: Update configuration
    update_result = client.update_yaml_config(
        file_path="configs/model.yaml",
        config={"training": {"batch_size": 32}}
    )
    print("Config Update:", update_result)
    
    client.close()