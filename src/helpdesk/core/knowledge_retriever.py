"""
LLM-based Knowledge Retriever
Uses LLM for semantic search instead of vector embeddings
"""

import json
import os
from typing import List, Dict, Any
import numpy as np
import re

import faiss

from ..models.models import RetrievalResult
from .response_generator import ResponseGenerator
from ..utils.config import Config

# Lazy import Groq so code still runs without the package if Groq provider isn't used.
try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


class LLMKnowledgeRetriever:
    """Knowledge retriever using LLM for semantic search"""
    
    def __init__(self):
        self.knowledge_chunks = []
        self.response_generator = ResponseGenerator()

        # Vector search attributes
        self.faiss_index = None
        self.groq_client = None

        # Load KB and build vector index
        self._load_knowledge_base()
        self._build_vector_index()
    
    def _load_knowledge_base(self):
        """Load and chunk knowledge base documents"""
        # Get project root directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_dir = os.path.join(project_root, "data")
        
        knowledge_files = [
            os.path.join(data_dir, "knowledge_base.md"),
            os.path.join(data_dir, "company_it_policies.md"), 
            os.path.join(data_dir, "installation_guides.json"),
            os.path.join(data_dir, "troubleshooting_database.json")
        ]
        
        for file_path in knowledge_files:
            if os.path.exists(file_path):
                if file_path.endswith('.md'):
                    self._load_markdown_file(file_path)
                elif file_path.endswith('.json'):
                    self._load_json_file(file_path)
    
    def _load_markdown_file(self, file_path: str):
        """Load and chunk markdown file by sections"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by ## headers
            sections = re.split(r'\n## ', content)
            
            for i, section in enumerate(sections):
                if section.strip():
                    # Add ## back to section titles (except first)
                    if i > 0:
                        section = "## " + section
                    
                    lines = section.strip().split('\n')
                    title = lines[0].replace('## ', '').replace('# ', '')
                    
                    chunk = {
                        'content': section.strip(),
                        'source': file_path,
                        'section': title,
                        'type': 'markdown'
                    }
                    self.knowledge_chunks.append(chunk)
                    
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    def _load_json_file(self, file_path: str):
        """Load and chunk JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def extract_text_chunks(obj, path=""):
                """Recursively extract text chunks from JSON"""
                chunks = []
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        if isinstance(value, str) and len(value) > 50:
                            # This is substantial text content
                            chunk = {
                                'content': f"{key}: {value}",
                                'source': file_path,
                                'section': current_path,
                                'type': 'json'
                            }
                            chunks.append(chunk)
                        elif isinstance(value, (dict, list)):
                            chunks.extend(extract_text_chunks(value, current_path))
                        elif isinstance(value, list) and value:
                            # Handle list of steps/items
                            if all(isinstance(item, str) for item in value):
                                content = f"{key}:\n" + "\n".join(f"- {item}" for item in value)
                                chunk = {
                                    'content': content,
                                    'source': file_path,
                                    'section': current_path,
                                    'type': 'json'
                                }
                                chunks.append(chunk)
                
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        current_path = f"{path}[{i}]" if path else f"[{i}]"
                        chunks.extend(extract_text_chunks(item, current_path))
                
                return chunks
            
            chunks = extract_text_chunks(data)
            self.knowledge_chunks.extend(chunks)
            
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    def retrieve(self, query: str, category: str = None) -> List[RetrievalResult]:
        """Retrieve relevant knowledge using vector similarity (FAISS + Groq embeddings) with LLM and keyword fallbacks."""
        if not self.knowledge_chunks:
            return []

        # 1) Attempt fast vector search
        vector_results = self._vector_search(query)
        if vector_results:
            return vector_results  # Early return if we found matches
        
        # Create a prompt for the LLM to find relevant chunks
        knowledge_summaries = []
        for i, chunk in enumerate(self.knowledge_chunks):
            summary = f"[{i}] {chunk['section']} ({chunk['source']}): {chunk['content'][:200]}..."
            knowledge_summaries.append(summary)
        
        # Limit to first 20 chunks to avoid token limits
        summaries_text = "\n".join(knowledge_summaries[:20])
        
        prompt = f"""Given this user query: "{query}"

Find the most relevant knowledge chunks from the following list. Return ONLY the numbers (e.g., "3, 7, 12") of the 3 most relevant chunks, ranked by relevance. If none are relevant, return "none".

Knowledge chunks:
{summaries_text}

Most relevant chunk numbers (top 3):"""

        try:
            # Use LLM to find relevant chunks
            response = self.response_generator._generate_response(prompt, max_tokens=50)
            
            # Parse the response to get chunk indices
            relevant_indices = []
            if response.lower() != "none":
                # Extract numbers from response
                numbers = re.findall(r'\d+', response)
                relevant_indices = [int(n) for n in numbers if int(n) < len(self.knowledge_chunks)][:3]
            
            # Convert to RetrievalResult objects
            results = []
            for idx in relevant_indices:
                if idx < len(self.knowledge_chunks):
                    chunk = self.knowledge_chunks[idx]
                    result = RetrievalResult(
                        content=chunk['content'],
                        source=chunk['source'],
                        relevance_score=1.0 - (len(results) * 0.1),  # Decreasing relevance
                        section=chunk['section']
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error in LLM retrieval: {e}")
            # Fallback to keyword search
            return self._fallback_keyword_search(query)
    
    def _fallback_keyword_search(self, query: str) -> List[RetrievalResult]:
        """Fallback keyword-based search if LLM fails"""
        query_words = query.lower().split()
        scored_chunks = []
        
        for chunk in self.knowledge_chunks:
            content_lower = chunk['content'].lower()
            score = sum(1 for word in query_words if word in content_lower)
            
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and take top 3
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, chunk in scored_chunks[:3]:
            result = RetrievalResult(
                content=chunk['content'],
                source=chunk['source'],
                relevance_score=score / len(query_words),
                section=chunk['section']
            )
            results.append(result)
        
        return results
    
    # -------------------- Vector Search helpers --------------------
    def _build_vector_index(self):
        """Build an in-memory FAISS index using Groq embeddings (if credentials available)."""
        if Groq is None or not Config.GROQ_API_KEY:
            # Groq not configured; skip vector search.
            return
        try:
            self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
            texts = [chunk['content'][:1000] for chunk in self.knowledge_chunks]
            if not texts:
                return

            embeddings = []
            batch_size = 96  # Groq batch limit
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                resp = self.groq_client.embeddings.create(
                    model=getattr(Config, 'EMBEDDING_MODEL', 'groq-embed-english-v1'),
                    input=batch,
                )
                embeddings.extend([d.embedding for d in resp.data])

            vecs = np.asarray(embeddings, dtype='float32')
            # Normalise for cosine similarity search
            faiss.normalize_L2(vecs)
            dim = vecs.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(vecs)
            self.faiss_index = index
        except Exception as e:
            print(f"Vector index build failed; continuing without vector search: {e}")

    def _vector_search(self, query: str, top_k: int = 3) -> List[RetrievalResult]:
        """Return top-k KB chunks using FAISS. Empty list if unavailable."""
        if not self.faiss_index or not self.groq_client:
            return []
        try:
            q_emb = self.groq_client.embeddings.create(
                model=getattr(Config, 'EMBEDDING_MODEL', 'groq-embed-english-v1'),
                input=[query],
            ).data[0].embedding
            q_vec = np.asarray([q_emb], dtype='float32')
            faiss.normalize_L2(q_vec)
            D, I = self.faiss_index.search(q_vec, top_k)

            results = []
            for score, idx in zip(D[0], I[0]):
                if idx < len(self.knowledge_chunks):
                    chunk = self.knowledge_chunks[idx]
                    results.append(
                        RetrievalResult(
                            content=chunk['content'],
                            source=chunk['source'],
                            relevance_score=float(score),
                            section=chunk['section'],
                        )
                    )
            return results
        except Exception as e:
            print(f"Vector search failed, falling back to LLM: {e}")
            return []

    # ----------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        return {
            "total_chunks": len(self.knowledge_chunks),
            "sources": list(set(chunk['source'] for chunk in self.knowledge_chunks)),
            "chunk_types": {
                chunk_type: sum(1 for chunk in self.knowledge_chunks if chunk['type'] == chunk_type)
                for chunk_type in ['markdown', 'json']
            }
        }
