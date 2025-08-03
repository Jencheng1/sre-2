# Knowledge Base Auto-Indexing Demo Guide

## Overview
This guide demonstrates how incidents created in the SRE Copilot system are automatically indexed to the Knowledge Base and can be searched for similar incidents, best practices, and resolution guides.

## Demo Flow in Streamlit

### 1. Create an Incident
**In Streamlit (Incident Management Tab):**
1. Go to "Generate Incident" section
2. Select incident type: "Performance Issue"
3. Select service: "Database"
4. Click "🚨 Generate Incident"
5. Note the OpsItem ID created (e.g., `oi-xxxxxxxx`)

### 2. Verify KB Indexing
**In Streamlit (Knowledge Base Tab → Search):**
1. Wait 5-10 seconds for indexing
2. Search Type: "Similar Incidents"
3. Enter query: "database connection" or the OpsItem ID
4. Click "🔍 Search"
5. You should see your newly created incident in results

### 3. Browse by Category
**In Streamlit (Knowledge Base Tab → Browse):**
1. Select Category: "performance" (or "All")
2. Document Type: "incident"
3. Click "📖 Browse"
4. Your new incident will appear with other performance incidents

### 4. Find Similar Incidents
**In Streamlit (Knowledge Base Tab → Search):**
1. Search Type: "Similar Incidents"
2. Query: "database connection pool exhaustion timeout"
3. Category: "performance"
4. The system will show:
   - Your new incident
   - Historical similar incidents
   - Similarity scores

### 5. Get Best Practices
**In Streamlit (Knowledge Base Tab → Search):**
1. Search Type: "Best Practices"
2. Query: "database connection pool"
3. Results show relevant best practices like:
   - Database Connection Pool Management
   - Circuit Breaker Pattern Implementation

### 6. Test Knowledge-Enhanced Analysis
**In Streamlit (Knowledge Base Tab → Test Analysis):**
1. Enter incident description (or use default)
2. Select incident type: "performance"
3. Click "🔬 Analyze with Knowledge Base"
4. See analysis enriched with:
   - Similar past incidents
   - Relevant best practices
   - Resolution guides

## What Happens Behind the Scenes

1. **Incident Creation**: When you create an incident, it becomes an AWS Systems Manager OpsItem
2. **Auto-Indexing**: The Knowledge Base Lambda automatically indexes the OpsItem
3. **Vector Embeddings**: The incident description is converted to a vector for similarity search
4. **Searchability**: The incident immediately becomes searchable in the KB
5. **Context Enhancement**: Future incidents benefit from this historical data

## Key Features Demonstrated

- **Automatic Knowledge Capture**: Every incident enriches the knowledge base
- **Similarity Search**: Find past incidents similar to current ones
- **Best Practice Matching**: Get relevant guidelines for incident types
- **Resolution Guides**: Access step-by-step resolution procedures
- **AI-Enhanced Analysis**: Get root cause analysis with historical context

## Benefits

1. **Faster Resolution**: Learn from past incidents
2. **Knowledge Retention**: No incident resolution is lost
3. **Pattern Recognition**: Identify recurring issues
4. **Proactive Prevention**: Apply best practices before issues occur
5. **Reduced MTTR**: Mean Time To Resolution improves with each incident

## Try It Yourself

1. Create multiple incidents of different types
2. Search for patterns across incidents
3. Use the knowledge base to resolve new incidents faster
4. Add custom best practices and resolution guides
5. Watch the system get smarter with each incident!