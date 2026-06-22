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
        """Create mock knowledge payload with educational content"""
        complexity = complexity or ComplexityLevel.INTERMEDIATE
        
        # Generate educational content based on query keywords
        query_lower = query.lower()
        
        # Determine topic and create relevant content
        if any(word in query_lower for word in ['code', 'coding', 'program', 'python', 'javascript', 'java']):
            modules = self._create_coding_modules(query, complexity)
            core_concept = "Programming Fundamentals"
        elif any(word in query_lower for word in ['react', 'vue', 'angular', 'frontend', 'web']):
            modules = self._create_web_dev_modules(query, complexity)
            core_concept = "Web Development"
        elif any(word in query_lower for word in ['data', 'machine learning', 'ai', 'algorithm']):
            modules = self._create_data_science_modules(query, complexity)
            core_concept = "Data Science & AI"
        else:
            # Generic educational content
            modules = self._create_generic_modules(query, complexity)
            core_concept = f"Understanding {query[:50]}"
        
        return KnowledgePayload(
            session_id=session_id,
            query=query,
            core_concept=core_concept,
            complexity_level=complexity,
            teaching_modules=modules,
            related_concepts=self._generate_related_concepts(query),
            source_references=[],
            total_estimated_time=sum(m.estimated_time for m in modules),
            keywords=query.lower().split()[:5],
            metadata={
                "mock_mode": True,
                "rag_model": "mock",
                "note": "This is generated content for demonstration. Configure watsonx.ai for real knowledge retrieval."
            }
        )
    
    def _create_coding_modules(self, query: str, complexity: ComplexityLevel) -> List[TeachingModule]:
        """Create coding-related educational modules with comprehensive content"""
        return [
            TeachingModule(
                module_id="coding_001",
                type=ModuleType.EXPLANATION,
                title="What is Programming?",
                content="""Programming is the art and science of creating instructions for computers to execute. At its core, programming involves:

Key Concepts:
• Algorithms: Step-by-step procedures to solve problems
• Data Structures: Ways to organize and store data efficiently
• Logic: Using conditional statements and loops to control program flow
• Abstraction: Breaking complex problems into manageable pieces

Why Learn Programming?
Programming empowers you to automate tasks, analyze data, build applications, and bring your ideas to life. It's a fundamental skill in our digital age, applicable across industries from healthcare to finance to entertainment.

The Programming Mindset:
Think like a programmer by breaking problems into smaller steps, testing your assumptions, and iterating on solutions. Debugging is part of the process - every error is a learning opportunity!""",
                estimated_time=120,
                complexity=complexity,
                interactive=False,
                order=0
            ),
            TeachingModule(
                module_id="coding_002",
                type=ModuleType.STEP_BY_STEP,
                title="Your Programming Journey",
                content="""Step 1: Choose Your First Language
Python is excellent for beginners due to its readable syntax. JavaScript is great for web development. Java and C++ are powerful for larger applications.

Step 2: Set Up Your Environment
• Install Python from python.org or use an online IDE like Replit
• Choose a code editor: VS Code, PyCharm, or Sublime Text
• Learn to use the terminal/command line

Step 3: Master the Fundamentals
• Variables: Store and manipulate data
• Data Types: Numbers, strings, booleans, lists
• Operators: Arithmetic, comparison, logical
• Control Flow: if/else statements, loops (for, while)
• Functions: Reusable blocks of code

Step 4: Practice Daily
• Solve coding challenges on LeetCode, HackerRank, or Codewars
• Build small projects: calculator, to-do list, simple game
• Read other people's code to learn different approaches

Step 5: Build Real Projects
Start with something you're passionate about - a personal website, a data analysis tool, or a game. Real projects teach you problem-solving and debugging skills that tutorials can't.""",
                estimated_time=180,
                complexity=complexity,
                interactive=False,
                order=1
            ),
            TeachingModule(
                module_id="coding_003",
                type=ModuleType.CODE_EXAMPLE,
                title="Python Fundamentals - Interactive Examples",
                content="""Example 1: Variables and Data Types

# Variables store data
name = "Alice"
age = 25
height = 5.6
is_student = True

print(f"{name} is {age} years old and {height} feet tall")


Example 2: Lists and Loops

# Lists store multiple items
fruits = ["apple", "banana", "cherry", "date"]

# Loop through the list
for fruit in fruits:
    print(f"I like {fruit}s!")

# List operations
fruits.append("elderberry")
print(f"Total fruits: {len(fruits)}")


Example 3: Functions

def calculate_area(length, width):
    area = length * width
    return area

# Use the function
room_area = calculate_area(10, 12)
print(f"Room area: {room_area} square feet")


Example 4: Conditional Logic

temperature = 75

if temperature > 80:
    print("It's hot! Stay hydrated.")
elif temperature > 60:
    print("Nice weather!")
else:
    print("It's cold. Wear a jacket.")


Try It Yourself:
Modify these examples! Change values, add new features, or combine concepts to create something unique.""",
                estimated_time=150,
                complexity=complexity,
                interactive=True,
                order=2
            ),
            TeachingModule(
                module_id="coding_004",
                type=ModuleType.EXPLANATION,
                title="Common Programming Patterns",
                content="""1. Input-Process-Output Pattern
Most programs follow this flow: get input from user, process it, display output.

2. Iteration Pattern
Use loops to repeat actions: processing lists, reading files, or retrying operations.

3. Conditional Pattern
Make decisions based on conditions: validating input, handling different cases, error checking.

4. Function Pattern
Break code into reusable functions: each function does one thing well, making code maintainable.

5. Error Handling Pattern
Anticipate and handle errors gracefully using try-except blocks (Python) or try-catch (JavaScript/Java).

Best Practices:
• Write clear, descriptive variable names
• Comment your code to explain "why", not "what"
• Keep functions small and focused
• Test your code frequently
• Use version control (Git) from day one""",
                estimated_time=90,
                complexity=complexity,
                interactive=False,
                order=3
            )
        ]
    
    def _create_web_dev_modules(self, query: str, complexity: ComplexityLevel) -> List[TeachingModule]:
        """Create comprehensive web development educational modules"""
        return [
            TeachingModule(
                module_id="web_001",
                type=ModuleType.EXPLANATION,
                title="Web Development Fundamentals",
                content="""Web development is the process of building websites and web applications that run in browsers. It encompasses:

Frontend Development (Client-Side):
• HTML: Structure and content of web pages
• CSS: Styling, layout, and visual design
• JavaScript: Interactivity and dynamic behavior
• Frameworks: React, Vue, Angular for complex applications

Backend Development (Server-Side):
• Server logic and APIs
• Database management
• Authentication and security
• Languages: Python, Node.js, Java, PHP

Full-Stack Development:
Combines both frontend and backend skills to build complete web applications.

Modern Web Technologies:
• Responsive Design: Works on all devices
• Progressive Web Apps: App-like experiences
• Single Page Applications: Fast, smooth navigation
• RESTful APIs: Communication between frontend and backend""",
                estimated_time=120,
                complexity=complexity,
                interactive=False,
                order=0
            ),
            TeachingModule(
                module_id="web_002",
                type=ModuleType.STEP_BY_STEP,
                title="Building Your First Website",
                content="""Step 1: Set Up Your Project
Create a folder for your website and open it in VS Code or your preferred editor.

Step 2: Create HTML Structure (index.html)
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My First Website</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Welcome to My Website</h1>
        <nav>
            <a href="#about">About</a>
            <a href="#projects">Projects</a>
            <a href="#contact">Contact</a>
        </nav>
    </header>
    <main>
        <section id="about">
            <h2>About Me</h2>
            <p>Your introduction here...</p>
        </section>
    </main>
    <script src="script.js"></script>
</body>
</html>

Step 3: Add Styling (styles.css)
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.6;
}

header {
    background: #333;
    color: white;
    padding: 1rem;
    text-align: center;
}

Step 4: Add Interactivity (script.js)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Website loaded!');
    // Add your JavaScript here
});

Step 5: Test Your Website
Open index.html in a web browser to see your creation!

Step 6: Deploy Online
Use GitHub Pages, Netlify, or Vercel to share your website with the world.""",
                estimated_time=180,
                complexity=complexity,
                interactive=False,
                order=1
            ),
            TeachingModule(
                module_id="web_003",
                type=ModuleType.CODE_EXAMPLE,
                title="Interactive Web Components",
                content="""Example 1: Responsive Navigation Menu

<nav class="navbar">
    <div class="logo">MyBrand</div>
    <ul class="nav-links">
        <li><a href="#home">Home</a></li>
        <li><a href="#about">About</a></li>
        <li><a href="#services">Services</a></li>
    </ul>
</nav>

CSS:
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background: #2c3e50;
}

.nav-links {
    display: flex;
    list-style: none;
    gap: 2rem;
}


Example 2: Form Validation

<form id="contactForm">
    <input type="email" id="email" placeholder="Your email" required>
    <button type="submit">Submit</button>
</form>

JavaScript:
document.getElementById('contactForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    if (email.includes('@')) {
        alert('Thank you for subscribing!');
    } else {
        alert('Please enter a valid email');
    }
});


Example 3: Dynamic Content Loading

<button id="loadBtn">Load Data</button>
<div id="content"></div>

JavaScript:
document.getElementById('loadBtn').addEventListener('click', async function() {
    const response = await fetch('https://api.example.com/data');
    const data = await response.json();
    document.getElementById('content').innerHTML = data.message;
});""",
                estimated_time=150,
                complexity=complexity,
                interactive=True,
                order=2
            ),
            TeachingModule(
                module_id="web_004",
                type=ModuleType.EXPLANATION,
                title="Modern Web Development Best Practices",
                content="""1. Semantic HTML
Use meaningful tags: <header>, <nav>, <main>, <article>, <footer> instead of generic <div> tags.

2. Mobile-First Design
Design for mobile devices first, then enhance for larger screens using CSS media queries.

3. Accessibility (a11y)
• Use alt text for images
• Ensure keyboard navigation works
• Maintain good color contrast
• Use ARIA labels when needed

4. Performance Optimization
• Minimize HTTP requests
• Compress images and assets
• Use lazy loading for images
• Minify CSS and JavaScript

5. Security Best Practices
• Validate all user input
• Use HTTPS
• Implement Content Security Policy
• Protect against XSS and CSRF attacks

6. Version Control
Use Git to track changes and collaborate with others.

7. Testing
Test across different browsers and devices to ensure compatibility.""",
                estimated_time=90,
                complexity=complexity,
                interactive=False,
                order=3
            )
        ]
    
    def _create_data_science_modules(self, query: str, complexity: ComplexityLevel) -> List[TeachingModule]:
        """Create comprehensive data science educational modules"""
        return [
            TeachingModule(
                module_id="ds_001",
                type=ModuleType.EXPLANATION,
                title="Introduction to Data Science",
                content="""Data science is an interdisciplinary field that uses scientific methods, algorithms, and systems to extract knowledge and insights from structured and unstructured data.

Core Components:

1. Statistics & Mathematics
• Probability theory
• Statistical inference
• Hypothesis testing
• Linear algebra and calculus

2. Programming & Tools
• Python (NumPy, Pandas, Scikit-learn)
• R for statistical computing
• SQL for database queries
• Jupyter notebooks for analysis

3. Machine Learning
• Supervised learning (classification, regression)
• Unsupervised learning (clustering, dimensionality reduction)
• Deep learning and neural networks
• Model evaluation and validation

4. Data Visualization
• Matplotlib, Seaborn, Plotly
• Tableau, Power BI
• Storytelling with data
• Interactive dashboards

5. Domain Knowledge
Understanding the business context and asking the right questions is crucial for meaningful analysis.

Applications:
• Healthcare: Disease prediction, drug discovery
• Finance: Fraud detection, risk assessment
• Marketing: Customer segmentation, recommendation systems
• Technology: Natural language processing, computer vision""",
                estimated_time=150,
                complexity=complexity,
                interactive=False,
                order=0
            ),
            TeachingModule(
                module_id="ds_002",
                type=ModuleType.STEP_BY_STEP,
                title="The Data Science Workflow",
                content="""Step 1: Define the Problem
• What question are you trying to answer?
• What metrics will measure success?
• What are the constraints and requirements?

Step 2: Collect Data
• Identify data sources (databases, APIs, web scraping)
• Gather relevant datasets
• Consider data quality and quantity
• Ensure ethical data collection

Step 3: Clean and Prepare Data
• Handle missing values
• Remove duplicates
• Fix inconsistencies
• Convert data types
• Feature engineering: create new meaningful features

Step 4: Exploratory Data Analysis (EDA)
• Calculate summary statistics
• Create visualizations (histograms, scatter plots, box plots)
• Identify patterns and correlations
• Detect outliers and anomalies

Step 5: Model Building
• Select appropriate algorithms
• Split data into training and testing sets
• Train models on training data
• Tune hyperparameters
• Validate with cross-validation

Step 6: Evaluate and Interpret
• Assess model performance (accuracy, precision, recall, F1-score)
• Understand feature importance
• Check for overfitting or underfitting
• Interpret results in business context

Step 7: Deploy and Monitor
• Deploy model to production
• Create APIs or dashboards
• Monitor performance over time
• Retrain as needed with new data""",
                estimated_time=180,
                complexity=complexity,
                interactive=False,
                order=1
            ),
            TeachingModule(
                module_id="ds_003",
                type=ModuleType.CODE_EXAMPLE,
                title="Python Data Science Examples",
                content="""Example 1: Data Analysis with Pandas

import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('sales_data.csv')

# Basic exploration
print(df.head())
print(df.describe())
print(df.info())

# Data cleaning
df = df.dropna()
df['date'] = pd.to_datetime(df['date'])

# Analysis
monthly_sales = df.groupby(df['date'].dt.month)['sales'].sum()
print(monthly_sales)


Example 2: Data Visualization

import matplotlib.pyplot as plt
import seaborn as sns

# Create visualizations
plt.figure(figsize=(10, 6))
sns.barplot(x='month', y='sales', data=df)
plt.title('Monthly Sales')
plt.xlabel('Month')
plt.ylabel('Sales ($)')
plt.show()


Example 3: Machine Learning Model

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Prepare data
X = df[['feature1', 'feature2', 'feature3']]
y = df['target']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f'MSE: {mse:.2f}')
print(f'R² Score: {r2:.2f}')""",
                estimated_time=180,
                complexity=complexity,
                interactive=True,
                order=2
            ),
            TeachingModule(
                module_id="ds_004",
                type=ModuleType.EXPLANATION,
                title="Data Science Best Practices",
                content="""1. Start with Questions, Not Data
Define clear objectives before diving into analysis. What decisions will this analysis inform?

2. Understand Your Data
• Know the source and collection method
• Understand each variable's meaning
• Check for biases in the data
• Document data lineage

3. Reproducibility
• Use version control (Git)
• Document your process
• Use virtual environments
• Write clean, commented code
• Create reproducible notebooks

4. Validate Rigorously
• Use proper train/test splits
• Apply cross-validation
• Test on unseen data
• Check for data leakage
• Validate assumptions

5. Communicate Effectively
• Create clear visualizations
• Tell a story with your data
• Explain technical concepts to non-technical audiences
• Provide actionable insights
• Document limitations

6. Ethics and Privacy
• Respect data privacy
• Avoid algorithmic bias
• Be transparent about limitations
• Consider societal impact
• Follow data protection regulations (GDPR, etc.)""",
                estimated_time=120,
                complexity=complexity,
                interactive=False,
                order=3
            )
        ]
    
    def _create_generic_modules(self, query: str, complexity: ComplexityLevel) -> List[TeachingModule]:
        """Create comprehensive generic educational modules"""
        return [
            TeachingModule(
                module_id="gen_001",
                type=ModuleType.EXPLANATION,
                title=f"Understanding {query[:50]}",
                content=f"""Let's explore {query} in depth.

What You'll Learn:
This comprehensive guide will help you understand the fundamental concepts, practical applications, and best practices related to this topic.

Key Learning Objectives:
• Grasp the core principles and terminology
• Understand real-world applications
• Learn practical techniques and methods
• Develop problem-solving skills
• Build a strong foundation for advanced topics

Why This Matters:
Understanding {query} is valuable because it provides you with knowledge and skills that can be applied in various contexts. Whether you're learning for personal growth, career advancement, or academic purposes, this topic offers important insights.

Learning Approach:
We'll break down complex concepts into manageable pieces, use clear examples, and provide step-by-step guidance to ensure you can follow along and apply what you learn.""",
                estimated_time=120,
                complexity=complexity,
                interactive=False,
                order=0
            ),
            TeachingModule(
                module_id="gen_002",
                type=ModuleType.STEP_BY_STEP,
                title="Structured Learning Path",
                content="""Step 1: Build Your Foundation
Start with the fundamental concepts. Don't rush - take time to understand the basics thoroughly. Use multiple resources: articles, videos, tutorials, and hands-on practice.

Step 2: Learn Through Examples
Theory is important, but examples bring concepts to life. Look for real-world applications and case studies. Try to understand not just "what" but "why" and "how."

Step 3: Practice Actively
Active learning is more effective than passive reading. Take notes, create summaries in your own words, teach concepts to others, and work on practical exercises.

Step 4: Apply Your Knowledge
Find opportunities to use what you've learned in real situations. Start with small projects or problems, then gradually tackle more complex challenges.

Step 5: Review and Reinforce
Regularly revisit key concepts to strengthen your understanding. Use spaced repetition - review material at increasing intervals over time.

Step 6: Explore Advanced Topics
Once you're comfortable with the basics, dive deeper into specialized areas that interest you. Connect new knowledge to what you already know.

Step 7: Stay Curious and Keep Learning
Learning is a continuous journey. Stay updated with new developments, join communities, ask questions, and never stop exploring!""",
                estimated_time=150,
                complexity=complexity,
                interactive=False,
                order=1
            ),
            TeachingModule(
                module_id="gen_003",
                type=ModuleType.EXPLANATION,
                title="Effective Learning Strategies",
                content="""1. Active Recall
Test yourself regularly instead of just re-reading material. This strengthens memory and identifies gaps in understanding.

2. Spaced Repetition
Review material at increasing intervals (1 day, 3 days, 1 week, 1 month). This technique dramatically improves long-term retention.

3. Interleaving
Mix different topics or types of problems rather than focusing on one thing at a time. This improves your ability to distinguish between concepts.

4. Elaboration
Explain concepts in your own words and connect them to things you already know. Ask yourself "why" and "how" questions.

5. Concrete Examples
Use specific examples to understand abstract concepts. Create your own examples to test understanding.

6. Dual Coding
Combine words with visuals. Draw diagrams, create mind maps, or use other visual representations alongside text.

7. Metacognition
Think about your thinking. Monitor your understanding, identify what you don't know, and adjust your learning strategies accordingly.

8. Practice Testing
Regular self-testing is one of the most effective learning techniques. Use flashcards, practice problems, or teach others.

9. Break It Down
Divide complex topics into smaller, manageable chunks. Master each piece before moving to the next.

10. Stay Consistent
Regular, shorter study sessions are more effective than occasional long cramming sessions. Build a sustainable learning routine.""",
                estimated_time=120,
                complexity=complexity,
                interactive=False,
                order=2
            )
        ]
    
    def _generate_related_concepts(self, query: str) -> List[str]:
        """Generate related concepts based on query"""
        query_lower = query.lower()
        
        if 'code' in query_lower or 'program' in query_lower:
            return ["Variables", "Functions", "Loops", "Data Structures", "Algorithms"]
        elif 'web' in query_lower:
            return ["HTML", "CSS", "JavaScript", "Responsive Design", "APIs"]
        elif 'data' in query_lower:
            return ["Statistics", "Visualization", "Machine Learning", "Python", "Analysis"]
        else:
            return ["Fundamentals", "Best Practices", "Applications", "Tools", "Resources"]
    
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