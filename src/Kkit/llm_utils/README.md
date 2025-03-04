# LLM utils

## LoRA fine tuning server

This service provides an API endpoint for fine-tuning large language models using Low-Rank Adaptation (LoRA) technique. Built with FastAPI, it supports asynchronous training jobs with progress tracking and integrates with Weights & Biases for experiment logging.

### Install

```bash
pip install git+https://github.com/erwinliyh/kylis_kit@main[llm]
```

Install flash attantion (optional):

```bash
conda install -c nvidia cuda-python # (optional)
pip install flash_attn
```

### Start server

```bash
kkit-lora-server --base_path /path/to/models --port 8000
```

Or call `train_model` in one line without server, see [example](examples/llm_sft_example/fine_tune.py).

### API Endpoints

1. Start Training (`POST /train`)

**Request Format:**

```
{
  "config": {
    "model_name": "Qwen/Qwen2.5-0.5B",
    "lora_path": null,
    "lora_rank": 8,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 3e-4,
    "max_length": null,
    "model_save_path": "my_lora_model",
    "response_template": "<|im_start|>assistant\n",
    "lora_target_modules": "all-linear",
    "lora_modules_to_save": ["lm_head", "embed_token"],
    "tokenizer_padding_side": "left",
    "attn_implementation": "flash_attention_2"
  },
  "file": "<UPLOADED_JSON_FILE>"
}
```

**Parameters:**

- `config`: Training configuration object (see Configuration Options)
- `file`: Training dataset in JSON format (see Dataset Format)

**Responses:**

- 202 Accepted: Training started successfully
- 409 Conflict: Training already in progress
- 500 Internal Server Error: File upload failed

### 2. Get Training Status (`GET /status`)

**Response Format:**

```
{
  "status": "training",
  "message": "Training...",
  "current_step": 150,
  "total_steps": 1000,
  "current_epoch": 1,
  "total_epochs": 3,
  "model_path": "/path/to/models/my_lora_model" // Only in completed status
}
```

Possible status values: `idle`, `training`, `completed`, `error`

### Configuration Options

| Parameter                | Type         | Default                     | Description                          |
|--------------------------|--------------|-----------------------------|--------------------------------------|
| model_name               | str          | "Qwen/Qwen2.5-0.5B"         | Base model identifier                |
| lora_path                | str?         | null                        | Path to existing LoRA checkpoint     |
| lora_rank                | int          | 8                           | LoRA rank dimension                  |
| lora_alpha               | int          | 32                          | LoRA alpha scaling factor            |
| lora_dropout             | float        | 0.05                        | LoRA dropout rate                    |
| epochs                   | int          | 3                           | Number of training epochs            |
| batch_size               | int          | 4                           | Per-device batch size                |
| learning_rate            | float        | 3e-4                        | Training learning rate               |
| max_length               | int?         | null                        | Maximum sequence length              |
| model_save_path          | str?         | null                        | Custom model output path             |
| response_template        | str          | "<\|im_start\|>assistant\n" | Response separator template          |
| lora_target_modules      | List/str     | "all-linear"                | Modules to apply LoRA to             |
| lora_modules_to_save     | List[str]    | ["lm_head", "embed_token"]  | Modules to fully train               |
| tokenizer_padding_side   | str?         | "left"                      | Tokenizer padding direction          |
| attn_implementation      | str          | "flash_attention_2"         | Attention implementation             |

## Dataset Format

JSON format with chat-style conversations:

```json
{
  "messages": [
    {"role": "user", "content": "What color is the sky?"},
    {"role": "assistant", "content": "It's blue on Earth."}
  ]
}
```

Requirements:

Each entry must have alternating user/assistant messages

File must be valid JSON lines with .jsonl extension

Recommended size: 100-10,000 examples

### Example Usage of API

**Starting Training**

```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: multipart/form-data" \
  -F "config={\"epochs\": 3, \"batch_size\": 4};type=application/json" \
  -F "file=@training_data.json;type=application/json"
```

**Monitoring Progress**

```bash
curl http://localhost:8000/status
```