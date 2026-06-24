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
        
        # Configure ONNX Runtime to use CPU execution and single-thread optimization
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        self.session = ort.InferenceSession(
            model_path, 
            sess_options=opts, 
            providers=["CPUExecutionProvider"]
        )

    def _embed_batch_sync(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            # Encode inputs using fast Rust tokenizers
            encoded = self.tokenizer.encode(text)

            inputs = {
                "input_ids": np.array([encoded.ids], dtype=np.int64),
                "attention_mask": np.array([encoded.attention_mask], dtype=np.int64),
                "token_type_ids": np.array([encoded.type_ids], dtype=np.int64),
            }

            # Run inference on CPU
            outputs = self.session.run(None, inputs)

            # extract first token [CLS] for BAAI/bge models and normalize
            cls_embedding = outputs[0][0][0]
            norm = np.linalg.norm(cls_embedding)
            normalized = (cls_embedding / norm).tolist()
            embeddings.append(normalized)

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
