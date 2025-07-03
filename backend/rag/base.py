"""
Base classes for the RAG (Retrieval-Augmented Generation) layer.

This module defines abstract base classes for document embedding,
retrieval, and response generation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from ..core.logging import get_logger
from ..etl.base import BudgetDocument


@dataclass
class QueryResult:
    """Represents a query result with relevance score."""
    
    document: BudgetDocument
    score: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'document': self.document.to_dict(),
            'score': self.score,
            'metadata': self.metadata,
        }


@dataclass
class RAGResponse:
    """Represents a complete RAG response."""
    
    query: str
    answer: str
    sources: List[QueryResult]
    confidence: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'answer': self.answer,
            'sources': [source.to_dict() for source in self.sources],
            'confidence': self.confidence,
            'metadata': self.metadata,
        }


class BaseEmbedder(ABC):
    """Abstract base class for document embedding."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"embedder.{name}")
    
    @abstractmethod
    async def embed_documents(self, documents: List[BudgetDocument]) -> List[List[float]]:
        """Generate embeddings for documents."""
        pass
    
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query."""
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        pass


class BaseVectorStore(ABC):
    """Abstract base class for vector storage."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"vectorstore.{name}")
    
    @abstractmethod
    async def add_documents(self, documents: List[BudgetDocument], embeddings: List[List[float]]) -> bool:
        """Add documents with embeddings to the store."""
        pass
    
    @abstractmethod
    async def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[QueryResult]:
        """Perform similarity search."""
        pass
    
    @abstractmethod
    async def hybrid_search(
        self, 
        query: str,
        query_embedding: List[float], 
        k: int = 5,
        alpha: float = 0.5,  # Weight between semantic and keyword search
        filters: Optional[Dict[str, Any]] = None
    ) -> List[QueryResult]:
        """Perform hybrid search (semantic + keyword)."""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents from the store."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if vector store is healthy."""
        pass


class BaseRetriever(ABC):
    """Abstract base class for document retrieval."""
    
    def __init__(self, name: str, vector_store: BaseVectorStore, embedder: BaseEmbedder):
        self.name = name
        self.vector_store = vector_store
        self.embedder = embedder
        self.logger = get_logger(f"retriever.{name}")
    
    @abstractmethod
    async def retrieve(
        self, 
        query: str, 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[QueryResult]:
        """Retrieve relevant documents for a query."""
        pass
    
    @abstractmethod
    async def rerank(self, query: str, results: List[QueryResult]) -> List[QueryResult]:
        """Re-rank search results for better relevance."""
        pass


class BaseGenerator(ABC):
    """Abstract base class for response generation."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"generator.{name}")
    
    @abstractmethod
    async def generate(
        self, 
        query: str, 
        context_documents: List[QueryResult],
        **kwargs
    ) -> str:
        """Generate response based on query and context."""
        pass
    
    @abstractmethod
    def get_prompt_template(self) -> str:
        """Get the prompt template used for generation."""
        pass
    
    @abstractmethod
    async def estimate_confidence(
        self, 
        query: str, 
        generated_response: str, 
        context_documents: List[QueryResult]
    ) -> float:
        """Estimate confidence score for the generated response."""
        pass


class RAGPipeline:
    """Main RAG pipeline coordinator."""
    
    def __init__(
        self, 
        retriever: BaseRetriever, 
        generator: BaseGenerator,
        name: str = "default"
    ):
        self.name = name
        self.retriever = retriever
        self.generator = generator
        self.logger = get_logger(f"rag.pipeline.{name}")
    
    async def query(
        self, 
        query: str, 
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        rerank: bool = True,
        **kwargs
    ) -> RAGResponse:
        """Process a query through the RAG pipeline."""
        self.logger.info(f"Processing query: {query}")
        
        try:
            # Retrieve relevant documents
            retrieved_docs = await self.retriever.retrieve(
                query=query,
                k=k,
                filters=filters,
                **kwargs
            )
            
            self.logger.info(f"Retrieved {len(retrieved_docs)} documents")
            
            # Optional re-ranking
            if rerank and len(retrieved_docs) > 1:
                retrieved_docs = await self.retriever.rerank(query, retrieved_docs)
                self.logger.info("Re-ranked retrieved documents")
            
            # Generate response
            answer = await self.generator.generate(
                query=query,
                context_documents=retrieved_docs,
                **kwargs
            )
            
            # Estimate confidence
            confidence = await self.generator.estimate_confidence(
                query=query,
                generated_response=answer,
                context_documents=retrieved_docs
            )
            
            response = RAGResponse(
                query=query,
                answer=answer,
                sources=retrieved_docs,
                confidence=confidence,
                metadata={
                    'retriever': self.retriever.name,
                    'generator': self.generator.name,
                    'k': k,
                    'rerank': rerank,
                }
            )
            
            self.logger.info(f"Generated response with confidence: {confidence}")
            return response
            
        except Exception as e:
            self.logger.error(f"RAG pipeline failed: {str(e)}")
            raise
    
    async def batch_query(
        self, 
        queries: List[str], 
        **kwargs
    ) -> List[RAGResponse]:
        """Process multiple queries."""
        responses = []
        for query in queries:
            try:
                response = await self.query(query, **kwargs)
                responses.append(response)
            except Exception as e:
                self.logger.error(f"Failed to process query '{query}': {str(e)}")
                # Create error response
                error_response = RAGResponse(
                    query=query,
                    answer=f"Error processing query: {str(e)}",
                    sources=[],
                    confidence=0.0,
                    metadata={'error': str(e)}
                )
                responses.append(error_response)
        
        return responses 