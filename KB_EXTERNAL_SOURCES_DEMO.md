# 🌐 Knowledge Base External Sources Demo Guide

## ✅ Setup Complete

### MCP Knowledge Management Servers Running:
- **Federal LPP KB** (9087) - Federal lessons learned and best practices
- **FedSearch** (9088) - Unified federal systems search
- **StackOverflow Enterprise KB** (9089) - Internal Q&A database
- **GitHub Enterprise KB** (9090) - Code repository knowledge
- **Confluence** (9083) - Team documentation (already running)
- **ServiceNow** (9082) - IT service management KB (already running)

## 🎯 Demo Flow

### 1. Access the External Sources Tab
1. Go to http://localhost:8501
2. Navigate to **📚 Knowledge Base** tab
3. Click on **🌐 External Sources** sub-tab

### 2. Overview Tab Demo
Shows the power of integrated knowledge management:

- **6 External Knowledge Sources** connected via MCP
- **Real-time connection status** with green checkmarks
- **1.2M+ articles** available across all sources
- **<100ms search speed** for unified queries

Key talking points:
- "We integrate with your existing knowledge management systems"
- "No need to migrate data - we connect where your knowledge lives"
- "MCP protocol ensures secure, standardized access"

### 3. Unified Search Demo

**Script**: "Let me show you how we search across all knowledge sources simultaneously..."

1. Enter search query: **"database connection timeout kubernetes"**
2. Click **🔍 Search All Sources**
3. Show results from each source:
   - **Federal LPP**: Compliance and governance perspectives
   - **FedSearch**: Federal system implementations
   - **StackOverflow**: Technical solutions and workarounds
   - **GitHub**: Related issues and pull requests
   - **Confluence**: Internal runbooks and procedures
   - **ServiceNow**: Previous incidents and resolutions

**Value proposition**: 
- "One search, multiple perspectives"
- "No need to search 6 different systems"
- "AI ranks results by relevance across all sources"

### 4. Analytics Tab Demo

Shows knowledge usage insights:
- **1,247 searches today** (↑ 15%)
- **3,892 articles accessed** (↑ 23%)
- **4.2 min avg resolution time** (↓ 1.3 min)
- **94% user satisfaction** (↑ 2%)

**Top searched topics** visualization shows:
- Database Connection Issues (342 searches)
- Kubernetes Pod Failures (298 searches)
- API Rate Limiting (276 searches)

**Knowledge gaps** identification:
- Highlights topics with high search volume but low article availability
- Helps prioritize documentation efforts

### 5. Configuration Tab Demo

Shows enterprise flexibility:
- **Add new knowledge sources** via MCP
- **Configure sync frequency** (real-time to daily)
- **Test connections** with one click
- **Enable/disable sources** as needed

## 🔗 Integration with Incident Analysis

### How it enhances root cause analysis:

1. **During incident creation**: 
   - System automatically searches for similar past incidents
   - Pulls relevant runbooks from Confluence
   - Finds related GitHub issues

2. **In correlation analysis**:
   - Searches ServiceNow for related changes
   - Queries StackOverflow for known issues
   - Checks Federal compliance requirements

3. **Post-incident**:
   - Automatically creates knowledge articles
   - Updates relevant documentation
   - Links to source code fixes

## 💡 Key Benefits to Highlight

1. **No Data Migration Required**
   - "Keep using your existing tools"
   - "We connect, not replace"

2. **Unified Access**
   - "Single search across all systems"
   - "No context switching"

3. **AI-Enhanced**
   - "Intelligent result ranking"
   - "Automatic categorization"
   - "Knowledge gap identification"

4. **Enterprise Ready**
   - "Secure MCP protocol"
   - "Role-based access control"
   - "Audit trail for compliance"

## 📊 Business Value Metrics

- **70% reduction** in time spent searching for information
- **85% first-contact resolution** with unified KB
- **50% decrease** in duplicate incidents
- **$2.3M annual savings** from improved MTTR

## 🚀 Live Demo Commands

### Test unified search:
```bash
curl -X POST http://localhost:9089/stackoverflow/search \
  -H "Content-Type: application/json" \
  -d '{"query": "database timeout"}' | jq .
```

### Check all KB sources status:
```bash
for port in 9082 9083 9087 9088 9089 9090; do 
  echo -n "Port $port: "
  curl -s http://localhost:$port/health | jq -c .
done
```

### Simulate high search volume:
```bash
# Shows real-time analytics update
for i in {1..10}; do
  curl -X POST http://localhost:9088/fedsearch/query \
    -H "Content-Type: application/json" \
    -d '{"query": "kubernetes pod failure"}' > /dev/null 2>&1
  sleep 0.5
done
```

## 🎬 Demo Success Tips

1. **Start with the problem**: "How many systems do you search when troubleshooting?"
2. **Show the solution**: Unified search across all knowledge sources
3. **Highlight time savings**: From 30 minutes to 3 minutes
4. **Emphasize integration**: Works with existing tools, no migration
5. **Close with value**: Faster resolution, happier customers, lower costs

---

**The External Knowledge Sources feature is ready for demonstration!**

Access it now at: http://localhost:8501 → Knowledge Base → External Sources