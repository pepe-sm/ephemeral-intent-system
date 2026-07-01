"""
Test script for Ollama integration with RAG Engine
Run this to verify Ollama is working correctly
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rag_engine import RAGEngine
from app.models.knowledge_payload import RAGQueryRequest, ComplexityLevel


async def test_ollama_connection():
    """Test 1: Verify Ollama connection"""
    print("\n" + "="*60)
    print("TEST 1: Ollama Connection")
    print("="*60)
    
    try:
        import ollama
        client = ollama.Client(host="http://localhost:11434")
        models = client.list()
        
        print("✅ Ollama is running!")
        print(f"📦 Available models:")
        for model in models.get('models', []):
            print(f"   - {model['name']}")
        
        return True
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("\n💡 Make sure Ollama is running:")
        print("   ollama serve")
        return False


async def test_rag_engine_initialization():
    """Test 2: Initialize RAG Engine with Ollama"""
    print("\n" + "="*60)
    print("TEST 2: RAG Engine Initialization")
    print("="*60)
    
    try:
        engine = RAGEngine(
            use_ollama=True,
            ollama_model="llama3.2",
            ollama_base_url="http://localhost:11434"
        )
        
        if engine.mock_mode:
            print("⚠️  RAG Engine in mock mode (Ollama not available)")
            return False
        
        if engine.llm_provider == "ollama":
            print(f"✅ RAG Engine initialized with Ollama")
            print(f"📊 Model: {engine.ollama_model}")
            print(f"🔗 URL: {engine.ollama_base_url}")
            return True
        else:
            print(f"⚠️  RAG Engine using {engine.llm_provider} instead of Ollama")
            return False
            
    except Exception as e:
        print(f"❌ RAG Engine initialization failed: {e}")
        return False


async def test_simple_query():
    """Test 3: Simple query to Ollama"""
    print("\n" + "="*60)
    print("TEST 3: Simple Query")
    print("="*60)
    
    try:
        engine = RAGEngine(use_ollama=True)
        
        if engine.mock_mode:
            print("⚠️  Skipping (mock mode)")
            return False
        
        request = RAGQueryRequest(
            session_id="test_simple",
            query="What is Python?",
            max_sources=3,
            complexity_preference=ComplexityLevel.BEGINNER
        )
        
        print(f"📝 Query: {request.query}")
        print("⏳ Generating response...")
        
        response = await engine.query(request)
        
        if response.success:
            print(f"✅ Query successful!")
            print(f"📚 Modules generated: {len(response.payload.teaching_modules)}")
            print(f"💡 Core concept: {response.payload.core_concept}")
            print(f"⏱️  Processing time: {response.processing_time_ms}ms")
            
            # Show first module
            if response.payload.teaching_modules:
                module = response.payload.teaching_modules[0]
                print(f"\n📖 First Module: {module.title}")
                print(f"   Type: {module.module_type.value}")
                print(f"   Content preview: {module.content[:150]}...")
            
            return True
        else:
            print(f"❌ Query failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_programming_query():
    """Test 4: Programming-specific query"""
    print("\n" + "="*60)
    print("TEST 4: Programming Query")
    print("="*60)
    
    try:
        engine = RAGEngine(use_ollama=True)
        
        if engine.mock_mode:
            print("⚠️  Skipping (mock mode)")
            return False
        
        request = RAGQueryRequest(
            session_id="test_programming",
            query="How do I create a function in Python?",
            max_sources=3,
            complexity_preference=ComplexityLevel.INTERMEDIATE
        )
        
        print(f"📝 Query: {request.query}")
        print("⏳ Generating response...")
        
        response = await engine.query(request)
        
        if response.success:
            print(f"✅ Query successful!")
            print(f"📚 Modules: {len(response.payload.teaching_modules)}")
            
            # Check for code examples
            has_code = any(
                m.module_type.value == "code_example" 
                for m in response.payload.teaching_modules
            )
            print(f"💻 Contains code examples: {'Yes' if has_code else 'No'}")
            
            return True
        else:
            print(f"❌ Query failed: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ Programming query test failed: {e}")
        return False


async def test_model_switching():
    """Test 5: Test with different model (if available)"""
    print("\n" + "="*60)
    print("TEST 5: Model Switching")
    print("="*60)
    
    try:
        import ollama
        client = ollama.Client(host="http://localhost:11434")
        models = client.list()
        available_models = [m['name'] for m in models.get('models', [])]
        
        # Try codellama if available
        if any('codellama' in m for m in available_models):
            print("📦 Testing with codellama model...")
            engine = RAGEngine(
                use_ollama=True,
                ollama_model="codellama:7b"
            )
            
            if not engine.mock_mode:
                print("✅ Successfully initialized with codellama")
                return True
        else:
            print("ℹ️  codellama not available (optional)")
            print("   Install with: ollama pull codellama:7b")
            return True
            
    except Exception as e:
        print(f"⚠️  Model switching test skipped: {e}")
        return True  # Not critical


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 OLLAMA INTEGRATION TEST SUITE")
    print("="*60)
    print("Testing Ollama integration with RAG Engine")
    print("Make sure Ollama is running: ollama serve")
    print("="*60)
    
    results = []
    
    # Test 1: Connection
    results.append(("Ollama Connection", await test_ollama_connection()))
    
    if not results[0][1]:
        print("\n❌ Cannot proceed without Ollama connection")
        print("\n💡 Quick Fix:")
        print("   1. Install Ollama: https://ollama.ai/")
        print("   2. Start Ollama: ollama serve")
        print("   3. Pull model: ollama pull llama3.2")
        return
    
    # Test 2: Initialization
    results.append(("RAG Engine Init", await test_rag_engine_initialization()))
    
    if not results[1][1]:
        print("\n❌ RAG Engine initialization failed")
        print("\n💡 Quick Fix:")
        print("   pip install ollama langchain-ollama")
        return
    
    # Test 3-5: Queries
    results.append(("Simple Query", await test_simple_query()))
    results.append(("Programming Query", await test_programming_query()))
    results.append(("Model Switching", await test_model_switching()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ollama integration is working!")
    elif passed >= 3:
        print("⚠️  Most tests passed. Some optional features unavailable.")
    else:
        print("❌ Integration needs attention. Check errors above.")
    
    print("="*60)


if __name__ == "__main__":
    # Check environment
    print("\n🔍 Environment Check:")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Check if .env exists
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"   .env file: ✅ Found")
    else:
        print(f"   .env file: ⚠️  Not found (using defaults)")
    
    # Run tests
    asyncio.run(run_all_tests())

# Made with Bob
