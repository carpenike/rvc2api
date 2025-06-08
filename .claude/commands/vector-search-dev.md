# Vector Search Development

Set up and develop FAISS-based vector search functionality for RV-C documentation with advanced chunking strategies and performance optimization.

## Vector Search Setup

### 1. Enable Vector Search Feature
```bash
# Enable vector search feature
export COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true

# Verify feature is enabled
poetry run python -c "
from backend.services.feature_manager import FeatureManager
import asyncio

async def check_vector_feature():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    if feature_manager.is_enabled('vector_search'):
        print('✓ Vector search feature is enabled')
        vector_feature = feature_manager.get_feature('vector_search')
        print(f'✓ Vector feature status: {vector_feature.health}')
    else:
        print('✗ Vector search feature is disabled')
        print('Enable with COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true')

    await feature_manager.shutdown()

asyncio.run(check_vector_feature())
"
```

### 2. Prepare RV-C Documentation
```bash
# Ensure RV-C PDF documentation exists
if [ ! -f "resources/rvc-2023-11.pdf" ]; then
    echo "✗ RV-C PDF not found in resources/ directory"
    echo "Please place RV-C specification PDF in resources/rvc-2023-11.pdf"
    exit 1
else
    echo "✓ RV-C PDF found"
    ls -lh resources/rvc-2023-11.pdf
fi

# Verify resource directory structure
mkdir -p resources/vector_store
echo "✓ Vector store directory ready"
```

## Document Processing and Chunking

### 3. Process RV-C Documentation
```bash
# Run enhanced document processor with advanced chunking
poetry run python dev_tools/enhanced_document_processor.py \
    --input resources/rvc-2023-11.pdf \
    --output resources/rvc-2023-11_chunks.json \
    --strategy mixed \
    --chunk-size 1000 \
    --chunk-overlap 200

# Verify chunks were created
if [ -f "resources/rvc-2023-11_chunks.json" ]; then
    echo "✓ Document chunks created"
    # Show chunk statistics
    poetry run python -c "
import json
with open('resources/rvc-2023-11_chunks.json', 'r') as f:
    chunks = json.load(f)
print(f'Created {len(chunks)} chunks')
print(f'Average chunk size: {sum(len(chunk[\"content\"]) for chunk in chunks) / len(chunks):.0f} characters')
"
else
    echo "✗ Failed to create document chunks"
    exit 1
fi
```

### 4. Test Document Chunking Strategies
```bash
# Test different chunking strategies for comparison
echo "Testing chunking strategies..."

# Test semantic chunking
poetry run python dev_tools/enhanced_document_processor.py \
    --input resources/rvc-2023-11.pdf \
    --output resources/chunks_semantic.json \
    --strategy semantic \
    --chunk-size 800

# Test hierarchical chunking
poetry run python dev_tools/enhanced_document_processor.py \
    --input resources/rvc-2023-11.pdf \
    --output resources/chunks_hierarchical.json \
    --strategy hierarchical \
    --chunk-size 1200

# Compare chunking results
poetry run python dev_tools/test_sample_chunks.py

echo "✓ Chunking strategy testing complete"
```

## FAISS Index Creation and Management

### 5. Build FAISS Vector Index
```bash
# Create FAISS index from document chunks
poetry run python -c "
import asyncio
from backend.services.vector_service import VectorService
from backend.core.config import get_settings

async def build_faiss_index():
    settings = get_settings()
    vector_service = VectorService(settings.vector_search)

    print('Building FAISS index from document chunks...')

    # Load chunks and build index
    chunks_file = 'resources/rvc-2023-11_chunks.json'

    try:
        await vector_service.build_index_from_chunks(chunks_file)
        print('✓ FAISS index built successfully')

        # Verify index was created
        index_stats = await vector_service.get_index_stats()
        print(f'✓ Index contains {index_stats[\"total_vectors\"]} vectors')
        print(f'✓ Index size: {index_stats[\"index_size_mb\"]} MB')

    except Exception as e:
        print(f'✗ Failed to build FAISS index: {e}')
        raise

    await vector_service.shutdown()

asyncio.run(build_faiss_index())
"

# Verify vector store files were created
if [ -d "resources/vector_store" ]; then
    echo "✓ Vector store created:"
    ls -la resources/vector_store/
else
    echo "✗ Vector store directory not found"
fi
```

### 6. Test Vector Search Functionality
```bash
# Test basic search queries
echo "Testing vector search queries..."

# Test RV-C protocol queries
poetry run python dev_tools/query_faiss.py "DC dimmer control messages"
poetry run python dev_tools/query_faiss.py "PGN parameter group numbers"
poetry run python dev_tools/query_faiss.py "SPN suspect parameter numbers"
poetry run python dev_tools/query_faiss.py "CAN bus message format"

# Test search with different parameters
poetry run python dev_tools/query_faiss.py \
    --query "lighting control protocol" \
    --top-k 5 \
    --threshold 0.7

echo "✓ Vector search testing complete"
```

## API Integration Testing

### 7. Test Vector Search API Endpoints
```bash
# Start backend with vector search enabled
COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true poetry run python run_server.py --debug &
BACKEND_PID=$!

# Wait for startup
sleep 5

# Test vector search API endpoint
echo "Testing vector search API..."

# Test search endpoint
curl -X GET "http://localhost:8000/api/docs/search?query=DC%20dimmer%20control" \
    -H "Accept: application/json" | python -m json.tool

# Test search with parameters
curl -X GET "http://localhost:8000/api/docs/search?query=PGN%20definition&limit=3&threshold=0.8" \
    -H "Accept: application/json" | python -m json.tool

# Test health endpoint
curl -X GET "http://localhost:8000/api/docs/health" \
    -H "Accept: application/json" | python -m json.tool

# Cleanup
kill $BACKEND_PID 2>/dev/null || true

echo "✓ API integration testing complete"
```

### 8. Performance Benchmarking
```bash
# Benchmark vector search performance
poetry run python -c "
import asyncio
import time
from backend.services.vector_service import VectorService
from backend.core.config import get_settings

async def benchmark_search():
    settings = get_settings()
    vector_service = VectorService(settings.vector_search)
    await vector_service.startup()

    # Test queries for benchmarking
    test_queries = [
        'DC dimmer control',
        'PGN parameter group',
        'CAN bus message format',
        'lighting control protocol',
        'RV-C specification',
        'suspect parameter number',
        'diagnostic messages',
        'device instance'
    ]

    print('Running search performance benchmark...')

    total_time = 0
    for i, query in enumerate(test_queries):
        start_time = time.time()

        results = await vector_service.search(query, top_k=5)

        end_time = time.time()
        query_time = end_time - start_time
        total_time += query_time

        print(f'Query {i+1}: \"{query}\" - {query_time:.3f}s ({len(results)} results)')

    avg_time = total_time / len(test_queries)
    print(f'\\nAverage search time: {avg_time:.3f}s')
    print(f'Total benchmark time: {total_time:.3f}s')

    await vector_service.shutdown()

asyncio.run(benchmark_search())
"
```

## Index Optimization and Maintenance

### 9. Optimize Vector Index
```bash
# Optimize FAISS index for better performance
poetry run python -c "
import asyncio
from backend.services.vector_service import VectorService
from backend.core.config import get_settings

async def optimize_index():
    settings = get_settings()
    vector_service = VectorService(settings.vector_search)
    await vector_service.startup()

    print('Optimizing FAISS index...')

    # Get current index stats
    stats_before = await vector_service.get_index_stats()
    print(f'Before optimization: {stats_before[\"index_size_mb\"]} MB')

    # Perform index optimization
    await vector_service.optimize_index()

    # Get stats after optimization
    stats_after = await vector_service.get_index_stats()
    print(f'After optimization: {stats_after[\"index_size_mb\"]} MB')

    size_reduction = stats_before['index_size_mb'] - stats_after['index_size_mb']
    print(f'Size reduction: {size_reduction:.2f} MB')

    await vector_service.shutdown()

asyncio.run(optimize_index())
"
```

### 10. Validate Search Quality
```bash
# Test search result quality and relevance
poetry run python -c "
import asyncio
from backend.services.vector_service import VectorService
from backend.core.config import get_settings

async def validate_search_quality():
    settings = get_settings()
    vector_service = VectorService(settings.vector_search)
    await vector_service.startup()

    # Test specific RV-C concepts with expected results
    test_cases = [
        {
            'query': 'DC dimmer brightness control',
            'expected_keywords': ['dimmer', 'brightness', 'DC', 'control']
        },
        {
            'query': 'PGN 65240 lighting command',
            'expected_keywords': ['PGN', '65240', 'lighting', 'command']
        },
        {
            'query': 'SPN suspect parameter number',
            'expected_keywords': ['SPN', 'suspect', 'parameter', 'number']
        }
    ]

    print('Validating search result quality...')

    for i, test in enumerate(test_cases):
        query = test['query']
        expected = test['expected_keywords']

        results = await vector_service.search(query, top_k=3)

        print(f'\\nTest {i+1}: \"{query}\"')
        print(f'Found {len(results)} results')

        # Check if expected keywords appear in top results
        for j, result in enumerate(results[:2]):  # Check top 2 results
            content = result['content'].lower()
            matched_keywords = [kw for kw in expected if kw.lower() in content]

            print(f'  Result {j+1}: {len(matched_keywords)}/{len(expected)} keywords matched')
            print(f'    Score: {result[\"score\"]:.3f}')
            print(f'    Matched: {matched_keywords}')

    await vector_service.shutdown()
    print('\\nSearch quality validation complete')

asyncio.run(validate_search_quality())
"
```

## Cleanup and Verification

### 11. Vector Search Health Check
```bash
echo "=== Vector Search Health Check ==="

# Check feature status
poetry run python -c "
from backend.services.feature_manager import FeatureManager
import asyncio

async def check_vector_health():
    feature_manager = FeatureManager()
    await feature_manager.startup()

    if feature_manager.is_enabled('vector_search'):
        print('✓ Vector search feature enabled')
        vector_feature = feature_manager.get_feature('vector_search')
        print(f'✓ Health status: {vector_feature.health}')
    else:
        print('✗ Vector search feature disabled')

    await feature_manager.shutdown()

asyncio.run(check_vector_health())
"

# Check required files
echo "=== File Status ==="
[ -f "resources/rvc-2023-11.pdf" ] && echo "✓ RV-C PDF found" || echo "✗ RV-C PDF missing"
[ -f "resources/rvc-2023-11_chunks.json" ] && echo "✓ Document chunks found" || echo "✗ Document chunks missing"
[ -d "resources/vector_store" ] && echo "✓ Vector store directory exists" || echo "✗ Vector store missing"

# Check vector store contents
if [ -d "resources/vector_store" ]; then
    echo "Vector store contents:"
    ls -la resources/vector_store/
fi

# Performance summary
echo "=== Performance Summary ==="
poetry run python dev_tools/query_faiss.py "test query" --benchmark 2>/dev/null || echo "Run vector search tests for performance data"

echo "=== Vector Search Development Complete ==="
echo "Use 'poetry run python dev_tools/query_faiss.py \"your query\"' to test searches"
echo "API endpoint: GET /api/docs/search?query=your+query"
```

## Arguments

$ARGUMENTS can specify:
- `--rebuild-index` - Rebuild FAISS index from scratch
- `--optimize` - Optimize existing index for performance
- `--benchmark` - Run comprehensive performance benchmarks
- `--validate-only` - Only run search quality validation
- `--chunking-strategy <strategy>` - Use specific chunking strategy (semantic, hierarchical, mixed)
- `--skip-api-test` - Skip API endpoint testing
- `chunk-only` - Only process documents and create chunks
- `index-only` - Only build FAISS index (requires existing chunks)

## Development Notes

### Vector Search Configuration
- Enable with `COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true`
- Embeddings model: sentence-transformers (configurable)
- FAISS index type: IndexFlatIP (inner product)
- Default chunk size: 1000 characters with 200 character overlap

### File Structure
- `resources/rvc-2023-11.pdf` - Source RV-C specification
- `resources/rvc-2023-11_chunks.json` - Processed document chunks
- `resources/vector_store/` - FAISS index and metadata files

### Troubleshooting
- If PDF processing fails, check PyPDF2 dependencies and file permissions
- For FAISS errors, ensure sufficient memory for index building
- If search quality is poor, try different chunking strategies
- For API errors, verify vector search feature is enabled in backend

This command provides complete vector search development workflow for RV-C documentation, including document processing, index optimization, and quality validation.
