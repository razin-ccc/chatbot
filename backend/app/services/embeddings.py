import os
import onnxruntime as ort
from tokenizers import Tokenizer
import numpy as np
from fastapi.concurrency import run_in_threadpool


class EmbeddingService:
    def __init__(self):
        # Resolve the local path to the ONNX model directory
        self.model_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "models", 
            "onnx", 
            "baai-bge-small"
        )
        os.makedirs(self.model_dir, exist_ok=True)
        
        model_path = os.path.join(self.model_dir, "model.onnx")
        tokenizer_path = os.path.join(self.model_dir, "tokenizer.json")
        
        # Self-healing: if weights are missing or are Git LFS pointers, download them
        is_model_invalid = (
            not os.path.exists(model_path) 
            or os.path.getsize(model_path) < 1024 * 1024  # Less than 1MB (actual is ~133MB)
        )
        if is_model_invalid:
            print("Local model.onnx is missing or is an LFS pointer. Downloading actual weights...")
            import urllib.request
            urllib.request.urlretrieve(
                "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/onnx/model.onnx", 
                model_path
            )
            print("Successfully downloaded model.onnx.")
            
        is_tokenizer_invalid = (
            not os.path.exists(tokenizer_path) 
            or os.path.getsize(tokenizer_path) < 1000  # Less than 1KB (actual is ~740KB)
        )
        if is_tokenizer_invalid:
            print("Local tokenizer.json is missing or is an LFS pointer. Downloading actual tokenizer...")
            import urllib.request
            urllib.request.urlretrieve(
                "https://huggingface.co/Xenova/bge-small-en-v1.5/resolve/main/tokenizer.json", 
                tokenizer_path
            )
            print("Successfully downloaded tokenizer.json.")

        # Load the Hugging Face tokenizer configuration locally
        self.tokenizer = Tokenizer.from_file(tokenizer_path)
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        
        # Let ONNX Runtime parallelize matmuls across cores for CPU inference.
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = os.cpu_count() or 1
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            model_path, 
            sess_options=opts, 
            providers=["CPUExecutionProvider"]
        )

    def _embed_batch_sync(
        self, texts: list[str], batch_size: int = 32
    ) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            # Batch-encode (padding is enabled) and run inference once per batch.
            encoded = self.tokenizer.encode_batch(batch)
            inputs = {
                "input_ids": np.array([e.ids for e in encoded], dtype=np.int64),
                "attention_mask": np.array(
                    [e.attention_mask for e in encoded], dtype=np.int64
                ),
                "token_type_ids": np.array(
                    [e.type_ids for e in encoded], dtype=np.int64
                ),
            }
            outputs = self.session.run(None, inputs)

            # [CLS] token per row, then L2-normalize each embedding.
            cls = outputs[0][:, 0, :]
            norms = np.linalg.norm(cls, axis=1, keepdims=True)
            norms[norms == 0] = 1e-12
            embeddings.extend((cls / norms).tolist())

        return embeddings

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await run_in_threadpool(self._embed_batch_sync, texts)

    async def embed_query(self, text: str) -> list[float]:
        if not text:
            return []
        # Prepend query instruction for BGE query-retrieval task
        instruction_text = (
            f"Represent this sentence for searching relevant passages: {text}"
        )
        embeddings = await self.embed_texts([instruction_text])
        return embeddings[0]
