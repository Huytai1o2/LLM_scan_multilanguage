import os
from huggingface_hub import snapshot_download

repo_id = "google/gemma-3n-E4B-it"
local_dir = os.path.expanduser(f"~/local_llm/{repo_id.split('/')[-1]}")

local_path = snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks="auto"
)

print("Model downloaded to:", local_path)
