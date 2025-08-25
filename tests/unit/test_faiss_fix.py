#!/usr/bin/env python3
"""Test script to verify our FAISS retriever fixes are working."""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root directory to path so 'api' package can be imported
# Current file is in tests/unit/, so go up two levels to reach project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_faiss_retriever():
    """Test the FAISS retriever directly with GitHub Copilot embeddings."""
    print("🔍 Testing FAISS Retriever with GitHub Copilot embeddings...")
    
    try:
        # Clear any module cache
        modules_to_clear = []
        for module_name in list(sys.modules.keys()):
            if 'adalflow' in module_name:
                modules_to_clear.append(module_name)
        
        for module_name in modules_to_clear:
            del sys.modules[module_name]
            
        print(f"Cleared {len(modules_to_clear)} adalflow modules from cache")
        
        from api.github_copilot_client import GitHubCopilotClient
        from adalflow.core import Embedder
        from adalflow.components.retriever.faiss_retriever import FAISSRetriever
        from adalflow.core.types import Document
        
        print("\n1️⃣ Creating GitHub Copilot embedder...")
        client = GitHubCopilotClient()
        embedder = Embedder(
            model_client=client,
            model_kwargs={
                "model": "text-embedding-3-small",
                "encoding_format": "float"
            }
        )
        
        print("\n2️⃣ Creating test documents...")
        # Create some test documents with embeddings
        test_docs = [
            Document(text="This is the first test document", meta_data={"file": "doc1.txt"}),
            Document(text="This is the second test document", meta_data={"file": "doc2.txt"}),
            Document(text="This is the third test document", meta_data={"file": "doc3.txt"})
        ]
        
        print("\n3️⃣ Embedding documents...")
        # Get embeddings for the documents
        doc_texts = [doc.text for doc in test_docs]
        doc_embeddings_result = await embedder.acall(doc_texts)
        
        if not doc_embeddings_result.data:
            print("❌ Failed to get document embeddings")
            return False
            
        # Assign embeddings to documents
        for i, doc in enumerate(test_docs):
            doc.vector = doc_embeddings_result.data[i]
            
        print(f"✅ Got embeddings for {len(test_docs)} documents")
        
        print("\n4️⃣ Creating FAISS retriever...")
        retriever = FAISSRetriever(
            top_k=2,
            embedder=embedder,
            documents=test_docs,
            document_map_func=lambda doc: doc.vector
        )
        
        print("\n5️⃣ Testing query retrieval...")
        query = "first document"
        print(f"Query: {query}")
        
        results = retriever(query)
        
        if results and len(results) > 0:
            print(f"✅ Retrieved {len(results)} result(s)")
            print(f"   Top result indices: {results[0].doc_indices}")
            print(f"   Top result scores: {results[0].doc_scores}")
            return True
        else:
            print("❌ No results returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_faiss_retriever())
    if success:
        print("\n🎉 FAISS retriever test passed! The fix is working.")
    else:
        print("\n💥 FAISS retriever test failed.")
        sys.exit(1)