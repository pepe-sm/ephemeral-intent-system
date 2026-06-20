"""
RAG Engine Service
Retrieval-Augmented Generation using IBM watsonx.ai and LangChain
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

try:
    from ibm_watsonx_ai import APIClient, Credentials  # type: ignore
    from ibm_watsonx_ai.foundation_models import ModelInference  # type: ignore
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    APIClient = None  # type: ignore
    Credentials = None  # type: ignore
    ModelInference = None  # type: ignore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain.docstore.document import Document

from ..models.knowledge_payload import (
    KnowledgePayload,
    TeachingModule,
    SourceReference,
    ComplexityLevel,
    ModuleType,
    RAGQueryRequest,
    RAGQueryResponse
)

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine
    Integrates IBM watsonx.ai with vector search for knowledge synthesis
    """
    
    def __init__(
        self,
        watsonx_api_key: Optional[str] = None,
        watsonx_project_id: Optional[str] = None,
        watsonx_url: Optional[str] = None,
        vector_store_path: str = "./chroma_db",
        model_id: str = "ibm/granite-13b-chat-v2"
    ):
        """
        Initialize RAG Engine with IBM watsonx.ai credentials
        
        Args:
            watsonx_api_key: IBM Cloud API key
            watsonx_project_id: watsonx.ai project ID
            watsonx_url: watsonx.ai API URL
            vector_store_path: Path to ChromaDB storage
            model_id: watsonx.ai model identifier
        """
        # Get credentials from environment if not provided
        self.api_key = watsonx_api_key or os.getenv("WATSONX_API_KEY")
        self.project_id = watsonx_project_id or os.getenv("WATSONX_PROJECT_ID")
        self.url = watsonx_url or os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        
        if not self.api_key or not self.project_id:
            logger.warning("IBM watsonx.ai credentials not configured. RAG engine will use mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            self._initialize_watsonx()
        
        self.model_id = model_id
        self.vector_store_path = vector_store_path
        
        # Initialize embeddings model (local, no API needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize or load vector store
        self._initialize_vector_store()
        
        logger.info(f"RAGEngine initialized (mock_mode={self.mock_mode})")
    
    def _initialize_watsonx(self):
        """Initialize IBM watsonx.ai client"""
        if not WATSONX_AVAILABLE or not Credentials or not APIClient or not ModelInference:
            logger.warning("IBM watsonx.ai SDK not available")
            self.mock_mode = True
            return
            
        try:
            credentials = Credentials(  # type: ignore
                url=self.url,
                api_key=self.api_key
            )
            
            self.watsonx_client = APIClient(credentials)  # type: ignore
            
            # Initialize model inference
            self.model = ModelInference(  # type: ignore
                model_id=self.model_id,
                credentials=credentials,
                project_id=self.project_id or ""
            )
            
            logger.info("IBM watsonx.ai client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize watsonx.ai: {e}")
            self.mock_mode = True
    
    def _initialize_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            # Try to load existing vector store
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
            logger.info(f"Vector store loaded from {self.vector_store_path}")
            
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}. Creating new one.")
            self.vector_store = Chroma(
                persist_directory=self.vector_store_path,
                embedding_function=self.embeddings
            )
    
    async def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        """
        Main query method - retrieves and synthesizes knowledge
        
        Args:
            request: RAG query request with user question
            
        Returns:
            RAGQueryResponse with synthesized knowledge payload
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Retrieve relevant documents
            relevant_docs = await self._retrieve_documents(
                request.query,
                max_results=request.max_sources
            )
            
            # Step 2: Generate knowledge synthesis
            knowledge_payload = await self._synthesize_knowledge(
                query=request.query,
                documents=relevant_docs,
                session_id=request.session_id,
                complexity_preference=request.complexity_preference
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return RAGQueryResponse(
                session_id=request.session_id,
                knowledge_payload=knowledge_payload,
                processing_time_ms=processing_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}", exc_info=True)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Return error response with fallback payload
            return RAGQueryResponse(
                session_id=request.session_id,
                knowledge_payload=self._create_fallback_payload(request),
                processing_time_ms=processing_time,
                success=False,
                error_message=str(e)
            )
    
    async def _retrieve_documents(
        self,
        query: str,
        max_results: int = 5
    ) -> List[Document]:
        """
        Retrieve relevant documents from vector store
        
        Args:
            query: Search query
            max_results: Maximum number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        try:
            # Perform similarity search
            docs = self.vector_store.similarity_search(
                query,
                k=max_results
            )
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.warning(f"Error retrieving documents: {e}")
            return []
    
    async def _synthesize_knowledge(
        self,
        query: str,
        documents: List[Document],
        session_id: str,
        complexity_preference: Optional[ComplexityLevel] = None
    ) -> KnowledgePayload:
        """
        Synthesize knowledge from retrieved documents using watsonx.ai
        
        Args:
            query: User's question
            documents: Retrieved relevant documents
            session_id: Session identifier
            complexity_preference: Preferred complexity level
            
        Returns:
            Structured KnowledgePayload
        """
        if self.mock_mode or not documents:
            return self._create_mock_payload(query, session_id, complexity_preference)
        
        try:
            # Prepare context from documents
            context = self._prepare_context(documents)
            
            # Generate teaching modules using watsonx.ai
            modules = await self._generate_teaching_modules(
                query=query,
                context=context,
                complexity=complexity_preference or ComplexityLevel.INTERMEDIATE
            )
            
            # Extract metadata
            core_concept = await self._extract_core_concept(query, context)
            related_concepts = await self._extract_related_concepts(query, context)
            keywords = await self._extract_keywords(query, context)
            
            # Create source references
            source_refs = self._create_source_references(documents)
            
            # Calculate total time
            total_time = sum(m.estimated_time for m in modules)
            
            return KnowledgePayload(
                session_id=session_id,
                query=query,
                core_concept=core_concept,
                complexity_level=complexity_preference or ComplexityLevel.INTERMEDIATE,
                teaching_modules=modules,
                related_concepts=related_concepts,
                source_references=source_refs,
                total_estimated_time=total_time,
                keywords=keywords,
                metadata={
                    "search_time_ms": 0,  # Will be set by caller
                    "sources_queried": len(documents),
                    "rag_model": self.model_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error synthesizing knowledge: {e}")
            return self._create_mock_payload(query, session_id, complexity_preference)
    
    def _prepare_context(self, documents: List[Document]) -> str:
        """Prepare context string from documents"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Source {i}]\n{doc.page_content}\n")
        return "\n".join(context_parts)
    
    async def _generate_teaching_modules(
        self,
        query: str,
        context: str,
        complexity: ComplexityLevel
    ) -> List[TeachingModule]:
        """Generate teaching modules using watsonx.ai"""
        
        prompt = f"""Based on the following context, create a structured teaching response for this question: "{query}"

Context:
{context[:2000]}  # Limit context length

Create 2-3 teaching modules that:
1. Explain the core concept clearly
2. Provide practical examples
3. Match {complexity.value} complexity level

Format each module with:
- Title
- Content (2-3 paragraphs)
- Type (explanation, code_example, or step_by_step)
- Estimated time in seconds

Respond in a structured format."""

        try:
            # Generate response using watsonx.ai
            response = self.model.generate_text(
                prompt=prompt,
                params={
                    "max_new_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            # Convert response to string if needed
            response_text = str(response) if not isinstance(response, str) else response
            
            # Parse response into modules (simplified for POC)
            modules = self._parse_modules_from_response(response_text, complexity)
            return modules
            
        except Exception as e:
            logger.error(f"Error generating modules: {e}")
            return self._create_default_modules(query, complexity)
    
    def _parse_modules_from_response(
        self,
        response: str,
        complexity: ComplexityLevel
    ) -> List[TeachingModule]:
        """Parse watsonx.ai response into teaching modules"""
        # Simplified parsing for POC
        # In production, use more sophisticated parsing or structured output
        
        modules = []
        sections = response.split("\n\n")
        
        for i, section in enumerate(sections[:3]):  # Max 3 modules
            if len(section.strip()) > 50:
                modules.append(TeachingModule(
                    module_id=f"mod_{i+1:03d}",
                    type=ModuleType.EXPLANATION if i == 0 else ModuleType.CODE_EXAMPLE,
                    title=f"Module {i+1}",
                    content=section.strip(),
                    estimated_time=60 + (i * 30),
                    complexity=complexity,
                    interactive=i > 0,
                    order=i
                ))
        
        return modules if modules else self._create_default_modules("", complexity)
    
    def _create_default_modules(
        self,
        query: str,
        complexity: ComplexityLevel
    ) -> List[TeachingModule]:
        """Create default teaching modules as fallback"""
        return [
            TeachingModule(
                module_id="mod_001",
                type=ModuleType.EXPLANATION,
                title="Understanding the Concept",
                content=f"Let's explore {query}...",
                estimated_time=60,
                complexity=complexity,
                interactive=False,
                order=0
            ),
            TeachingModule(
                module_id="mod_002",
                type=ModuleType.CODE_EXAMPLE,
                title="Practical Example",
                content="Here's a practical example...",
                estimated_time=90,
                complexity=complexity,
                interactive=True,
                order=1
            )
        ]
    
    async def _extract_core_concept(self, query: str, context: str) -> str:
        """Extract core concept from query and context"""
        # Simplified extraction
        words = query.split()
        return " ".join(words[:5]).title()
    
    async def _extract_related_concepts(self, query: str, context: str) -> List[str]:
        """Extract related concepts"""
        # Simplified extraction
        return ["Related Concept 1", "Related Concept 2", "Related Concept 3"]
    
    async def _extract_keywords(self, query: str, context: str) -> List[str]:
        """Extract keywords"""
        # Simplified extraction
        return query.lower().split()[:5]
    
    def _create_source_references(self, documents: List[Document]) -> List[SourceReference]:
        """Create source references from documents"""
        refs = []
        for i, doc in enumerate(documents[:5]):
            refs.append(SourceReference(
                title=f"Source {i+1}",
                url=doc.metadata.get("source", None),
                relevance_score=0.9 - (i * 0.1),
                excerpt=doc.page_content[:200]
            ))
        return refs
    
    def _create_mock_payload(
        self,
        query: str,
        session_id: str,
        complexity: Optional[ComplexityLevel]
    ) -> KnowledgePayload:
        """Create mock knowledge payload for testing"""
        complexity = complexity or ComplexityLevel.INTERMEDIATE
        
        return KnowledgePayload(
            session_id=session_id,
            query=query,
            core_concept=f"Understanding {query[:30]}",
            complexity_level=complexity,
            teaching_modules=[
                TeachingModule(
                    module_id="mock_001",
                    type=ModuleType.EXPLANATION,
                    title="Introduction",
                    content=f"This is a mock response for: {query}",
                    estimated_time=60,
                    complexity=complexity,
                    interactive=False,
                    order=0
                )
            ],
            related_concepts=["Concept A", "Concept B"],
            source_references=[],
            total_estimated_time=60,
            keywords=query.lower().split()[:3],
            metadata={
                "mock_mode": True,
                "rag_model": "mock"
            }
        )
    
    def _create_fallback_payload(self, request: RAGQueryRequest) -> KnowledgePayload:
        """Create fallback payload on error"""
        return self._create_mock_payload(
            request.query,
            request.session_id,
            request.complexity_preference
        )
    
    def add_documents(self, documents: List[Document]):
        """
        Add documents to vector store
        
        Args:
            documents: List of documents to add
        """
        try:
            # Split documents into chunks
            chunks = []
            for doc in documents:
                doc_chunks = self.text_splitter.split_documents([doc])
                chunks.extend(doc_chunks)
            
            # Add to vector store
            self.vector_store.add_documents(chunks)
            self.vector_store.persist()
            
            logger.info(f"Added {len(chunks)} document chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
    
    def clear_vector_store(self):
        """Clear all documents from vector store"""
        try:
            self.vector_store.delete_collection()
            self._initialize_vector_store()
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")


# Made with Bob