import fitz  # PyMuPDF
import os
import json
from typing import List, Dict


class PDFChunker:
    def __init__(self, pdf_path: str, chunk_size: int = 800):
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.chunks = []

    def extract_text(self) -> str:
        doc = fitz.open(self.pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text

    def chunk_text(self, text: str) -> List[Dict]:
        words = text.split()
        chunk = []
        for i in range(0, len(words), self.chunk_size):
            chunk_text = " ".join(words[i:i + self.chunk_size])
            self.chunks.append({
                "chunk_id": len(self.chunks) + 1,
                "text": chunk_text,
                "source": os.path.basename(self.pdf_path)
            })
        return self.chunks

    def save_chunks(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    pdf_files = [
        "knowledge_base/Guide_to_Litigation_in_India.pdf",
        "knowledge_base/Legal_Compliance_ICAI.pdf"
    ]
    output_file = "data/chunks.json"
    all_chunks = []

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    for pdf in pdf_files:
        chunker = PDFChunker(pdf)
        raw_text = chunker.extract_text()
        print(f"{os.path.basename(pdf)} - Total words extracted: {len(raw_text.split())}")
        chunks = chunker.chunk_text(raw_text)
        all_chunks.extend(chunks)


    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"Extracted and chunked {len(all_chunks)} segments across {len(pdf_files)} PDFs.")
