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
            "baai-bge-small",
        )

        # Load the Hugging Face tokenizer configuration locally
        self.tokenizer = Tokenizer.from_file(
            os.path.join(self.model_dir, "tokenizer.json")
        )
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")

        # Configure ONNX Runtime to use CPU execution and single-thread optimization
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

        self.session = ort.InferenceSession(
            os.path.join(self.model_dir, "model.onnx"),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
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
