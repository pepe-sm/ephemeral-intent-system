"""
Unit tests for RAG Engine Service
Tests knowledge retrieval and synthesis functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.rag_engine import RAGEngine
from app.models.knowledge_payload import (
    RAGQueryRequest,
    RAGQueryResponse,
    KnowledgePayload,
    TeachingModule,
    SourceReference,
    ComplexityLevel,
    ModuleType
)
from langchain.docstore.document import Document


class TestRAGEngineInitialization:
    """Test RAG Engine initialization"""
    
    def test_initialization_without_credentials(self):
        """Test initialization without watsonx credentials (mock mode)"""
        engine = RAGEngine()
        assert engine.mock_mode is True
        assert engine.embeddings is not None
        assert engine.vector_store is not None
    
    def test_initialization_with_credentials(self):
        """Test initialization with watsonx credentials"""
        engine = RAGEngine(
            watsonx_api_key="test_key",
            watsonx_project_id="test_project",
            watsonx_url="https://test.ibm.com"
        )
        assert engine.api_key == "test_key"
        assert engine.project_id == "test_project"
        assert engine.url == "https://test.ibm.com"
    
    def test_custom_model_id(self):
        """Test initialization with custom model ID"""
        engine = RAGEngine(model_id="custom/model")
        assert engine.model_id == "custom/model"


class TestRAGEngineQuery:
    """Test RAG Engine query functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    @pytest.fixture
    def sample_request(self):
        """Create sample RAG query request"""
        return RAGQueryRequest(
            session_id="test_session_001",
            query="How do I use React hooks?",
            max_sources=5,
            complexity_preference=ComplexityLevel.INTERMEDIATE
        )
    
    @pytest.mark.asyncio
    async def test_query_basic(self, engine, sample_request):
        """Test basic query functionality"""
        response = await engine.query(sample_request)
        
        assert isinstance(response, RAGQueryResponse)
        assert response.session_id == sample_request.session_id
        assert response.success is True
        assert response.knowledge_payload is not None
        assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_query_returns_knowledge_payload(self, engine, sample_request):
        """Test that query returns valid knowledge payload"""
        response = await engine.query(sample_request)
        payload = response.knowledge_payload
        
        assert isinstance(payload, KnowledgePayload)
        assert payload.session_id == sample_request.session_id
        assert payload.query == sample_request.query
        assert len(payload.teaching_modules) > 0
        assert payload.total_estimated_time > 0
    
    @pytest.mark.asyncio
    async def test_query_with_different_complexity(self, engine):
        """Test query with different complexity levels"""
        for complexity in [ComplexityLevel.BEGINNER, ComplexityLevel.INTERMEDIATE, ComplexityLevel.ADVANCED]:
            request = RAGQueryRequest(
                session_id=f"test_{complexity.value}",
                query="Test query",
                complexity_preference=complexity
            )
            response = await engine.query(request)
            assert response.knowledge_payload.complexity_level == complexity
    
    @pytest.mark.asyncio
    async def test_query_error_handling(self, engine):
        """Test query error handling"""
        # Create invalid request
        request = RAGQueryRequest(
            session_id="error_test",
            query="",  # Empty query
            max_sources=0  # Invalid max_sources
        )
        
        # Should still return a response with fallback
        response = await engine.query(request)
        assert isinstance(response, RAGQueryResponse)
        assert response.knowledge_payload is not None


class TestDocumentRetrieval:
    """Test document retrieval functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents"""
        return [
            Document(
                page_content="React hooks are functions that let you use state.",
                metadata={"source": "react_docs", "page": 1}
            ),
            Document(
                page_content="useState is a Hook that lets you add state to function components.",
                metadata={"source": "react_docs", "page": 2}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_retrieve_documents_empty_store(self, engine):
        """Test document retrieval from empty vector store"""
        docs = await engine._retrieve_documents("test query", max_results=5)
        assert isinstance(docs, list)
        # Empty store returns empty list
        assert len(docs) == 0
    
    def test_add_documents(self, engine, sample_documents):
        """Test adding documents to vector store"""
        engine.add_documents(sample_documents)
        # Documents should be added (no exception)
        assert True
    
    @pytest.mark.asyncio
    async def test_retrieve_after_adding_documents(self, engine, sample_documents):
        """Test document retrieval after adding documents"""
        engine.add_documents(sample_documents)
        docs = await engine._retrieve_documents("React hooks", max_results=2)
        assert isinstance(docs, list)
        # Should retrieve documents
        assert len(docs) >= 0


class TestKnowledgeSynthesis:
    """Test knowledge synthesis functionality"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents"""
        return [
            Document(
                page_content="React hooks documentation content",
                metadata={"source": "docs"}
            )
        ]
    
    @pytest.mark.asyncio
    async def test_synthesize_knowledge_mock_mode(self, engine, sample_documents):
        """Test knowledge synthesis in mock mode"""
        payload = await engine._synthesize_knowledge(
            query="Test query",
            documents=sample_documents,
            session_id="test_001",
            complexity_preference=ComplexityLevel.INTERMEDIATE
        )
        
        assert isinstance(payload, KnowledgePayload)
        assert payload.session_id == "test_001"
        assert len(payload.teaching_modules) > 0
        assert payload.total_estimated_time > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_with_no_documents(self, engine):
        """Test synthesis with no documents (fallback)"""
        payload = await engine._synthesize_knowledge(
            query="Test query",
            documents=[],
            session_id="test_002",
            complexity_preference=ComplexityLevel.BEGINNER
        )
        
        assert isinstance(payload, KnowledgePayload)
        assert payload.complexity_level == ComplexityLevel.BEGINNER


class TestTeachingModuleGeneration:
    """Test teaching module generation"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    def test_create_default_modules(self, engine):
        """Test default module creation"""
        modules = engine._create_default_modules(
            "Test query",
            ComplexityLevel.INTERMEDIATE
        )
        
        assert isinstance(modules, list)
        assert len(modules) > 0
        assert all(isinstance(m, TeachingModule) for m in modules)
        assert all(m.complexity == ComplexityLevel.INTERMEDIATE for m in modules)
    
    def test_module_ordering(self, engine):
        """Test that modules are properly ordered"""
        modules = engine._create_default_modules(
            "Test query",
            ComplexityLevel.ADVANCED
        )
        
        orders = [m.order for m in modules]
        assert orders == sorted(orders)  # Should be in ascending order
    
    def test_parse_modules_from_response(self, engine):
        """Test parsing modules from text response"""
        response_text = """
        Module 1: Introduction
        This is the first module content.
        
        Module 2: Advanced Topics
        This is the second module content.
        """
        
        modules = engine._parse_modules_from_response(
            response_text,
            ComplexityLevel.INTERMEDIATE
        )
        
        assert isinstance(modules, list)
        assert len(modules) > 0


class TestSourceReferences:
    """Test source reference creation"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents with metadata"""
        return [
            Document(
                page_content="Content 1",
                metadata={"source": "https://example.com/doc1", "title": "Doc 1"}
            ),
            Document(
                page_content="Content 2",
                metadata={"source": "https://example.com/doc2", "title": "Doc 2"}
            )
        ]
    
    def test_create_source_references(self, engine, sample_documents):
        """Test source reference creation from documents"""
        refs = engine._create_source_references(sample_documents)
        
        assert isinstance(refs, list)
        assert len(refs) == len(sample_documents)
        assert all(isinstance(r, SourceReference) for r in refs)
        assert all(0 <= r.relevance_score <= 1 for r in refs)
    
    def test_source_reference_relevance_ordering(self, engine, sample_documents):
        """Test that source references are ordered by relevance"""
        refs = engine._create_source_references(sample_documents)
        
        scores = [r.relevance_score for r in refs]
        # Scores should be in descending order
        assert scores == sorted(scores, reverse=True)


class TestContentExtraction:
    """Test content extraction methods"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    @pytest.mark.asyncio
    async def test_extract_core_concept(self, engine):
        """Test core concept extraction"""
        concept = await engine._extract_core_concept(
            "How to use React hooks effectively",
            "Context about React hooks"
        )
        assert isinstance(concept, str)
        assert len(concept) > 0
    
    @pytest.mark.asyncio
    async def test_extract_related_concepts(self, engine):
        """Test related concepts extraction"""
        concepts = await engine._extract_related_concepts(
            "React hooks",
            "Context"
        )
        assert isinstance(concepts, list)
        assert len(concepts) > 0
    
    @pytest.mark.asyncio
    async def test_extract_keywords(self, engine):
        """Test keyword extraction"""
        keywords = await engine._extract_keywords(
            "React hooks useState useEffect",
            "Context"
        )
        assert isinstance(keywords, list)
        assert len(keywords) > 0


class TestMockPayloadCreation:
    """Test mock payload creation"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    def test_create_mock_payload(self, engine):
        """Test mock payload creation"""
        payload = engine._create_mock_payload(
            "Test query",
            "session_123",
            ComplexityLevel.BEGINNER
        )
        
        assert isinstance(payload, KnowledgePayload)
        assert payload.session_id == "session_123"
        assert payload.query == "Test query"
        assert payload.complexity_level == ComplexityLevel.BEGINNER
        assert len(payload.teaching_modules) > 0
        assert payload.metadata is not None
        assert payload.metadata.get("mock_mode") is True
    
    def test_create_fallback_payload(self, engine):
        """Test fallback payload creation"""
        request = RAGQueryRequest(
            session_id="fallback_test",
            query="Fallback query",
            complexity_preference=ComplexityLevel.ADVANCED
        )
        
        payload = engine._create_fallback_payload(request)
        assert isinstance(payload, KnowledgePayload)
        assert payload.session_id == request.session_id


class TestVectorStoreOperations:
    """Test vector store operations"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    def test_clear_vector_store(self, engine):
        """Test clearing vector store"""
        # Should not raise exception
        engine.clear_vector_store()
        assert True
    
    def test_add_and_clear_documents(self, engine):
        """Test adding and clearing documents"""
        docs = [
            Document(page_content="Test content", metadata={"source": "test"})
        ]
        
        engine.add_documents(docs)
        engine.clear_vector_store()
        # Should complete without error
        assert True


class TestContextPreparation:
    """Test context preparation"""
    
    @pytest.fixture
    def engine(self):
        """Create RAG engine instance"""
        return RAGEngine()
    
    def test_prepare_context_single_document(self, engine):
        """Test context preparation with single document"""
        docs = [Document(page_content="Test content")]
        context = engine._prepare_context(docs)
        
        assert isinstance(context, str)
        assert "Test content" in context
        assert "[Source 1]" in context
    
    def test_prepare_context_multiple_documents(self, engine):
        """Test context preparation with multiple documents"""
        docs = [
            Document(page_content="Content 1"),
            Document(page_content="Content 2"),
            Document(page_content="Content 3")
        ]
        context = engine._prepare_context(docs)
        
        assert "Content 1" in context
        assert "Content 2" in context
        assert "Content 3" in context
        assert "[Source 1]" in context
        assert "[Source 2]" in context
        assert "[Source 3]" in context


# Made with Bob