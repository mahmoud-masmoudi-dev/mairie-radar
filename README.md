# Mairie Radar 🏛️🔍

An AI-powered system for collecting, analyzing, and detecting budget anomalies in French city halls (mairies) using Agentic RAG (Retrieval-Augmented Generation) technology.

## 🎯 Project Overview

Mairie Radar is an intelligent monitoring system that leverages advanced AI techniques to:
- Automatically collect budget data from French city halls
- Analyze financial patterns and expenditures
- Detect anomalies, irregularities, and potential infringements
- Provide insights and alerts for transparency and accountability

## 🚀 Key Features

- **Automated Data Collection**: Web scraping and API integration to gather budget data from various sources
- **Intelligent Document Processing**: Extract and understand budget information from PDFs, websites, and databases
- **Anomaly Detection**: AI-powered analysis to identify unusual spending patterns or budget violations
- **Vector Search**: Efficient semantic search across historical budget data using Weaviate
- **Agentic Workflow**: Autonomous agents that can reason, search, and analyze data independently
- **Real-time Monitoring**: Continuous tracking of budget updates and changes

## 🛠️ Technology Stack

- **Framework**: LangGraph/LangChain for agentic RAG implementation
- **Vector Database**: Weaviate (managed free tier)
- **Language**: Python 3.9+
- **LLM Integration**: OpenAI GPT-4 / Claude / Open-source alternatives
- **Data Sources**: 
  - data.gouv.fr (French government open data)
  - Individual mairie websites
  - Budget PDFs and reports

## 📋 Prerequisites

- Python 3.9 or higher
- Weaviate Cloud account (free tier)
- API keys for chosen LLM provider
- Basic understanding of French administrative structure

## 🏗️ Project Structure

```
mairie-radar/
├── backend/            # Python backend (uv project)
│   ├── core/          # Configuration & logging
│   ├── etl/           # Extract, Transform, Load layer
│   ├── rag/           # Retrieval-Augmented Generation layer
│   ├── agents/        # ACP Intelligence layer
│   └── api/           # FastAPI application
├── frontend/          # React chat UI (@llamaindex/chat-ui)
├── tests/             # Test suite
├── docs/              # Documentation
├── data/              # Local data storage
└── pyproject.toml     # Backend dependencies
```

## 🔧 Installation

```bash
# Clone the repository
git clone https://github.com/mahmoud-masmoudi-dev/mairie-radar.git
cd mairie-radar

# Backend setup (Python with uv)
uv sync  # Install backend dependencies

# Frontend setup (React with npm/yarn)
cd frontend
npm install  # or yarn install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

## 🚦 Quick Start

```python
# Backend API
from backend.api.main import app
import uvicorn

# Start the API server
uvicorn.run(app, host="0.0.0.0", port=8000)

# Or use the CLI
# uv run backend-api

# Frontend - Open http://localhost:3000
# The chat UI will connect to the backend API
```

## 📊 Data Sources

The system collects data from:
1. **Official Government Portals**
   - data.gouv.fr
   - collectivites-locales.gouv.fr
   
2. **Municipal Websites**
   - Direct scraping of budget documents
   - API endpoints when available

3. **Public Registries**
   - DGFIP (Direction générale des Finances publiques)
   - Cour des comptes reports

## 🤖 Agent Architecture

The system uses specialized agents:
- **Collector Agent**: Gathers budget data from various sources
- **Parser Agent**: Extracts structured data from documents
- **Analyzer Agent**: Performs anomaly detection
- **Reporter Agent**: Generates insights and alerts
- **Coordinator Agent**: Orchestrates the workflow

## ⚡ Performance Considerations

- Efficient vector indexing for fast similarity search
- Batch processing for large-scale analysis
- Caching mechanisms to reduce API calls
- Asynchronous operations for concurrent data collection

## 🔐 Security & Privacy

- All data handling complies with RGPD (GDPR)
- No personal data is collected or stored
- Focus exclusively on public budget information
- Secure API key management

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- French Open Data initiatives
- LangChain/LangGraph community
- Weaviate for vector database support

## 📞 Contact

For questions or collaboration opportunities, please open an issue or contact the maintainers.

---

**Note**: This project is in active development. Features and documentation will evolve as we progress through POC, MVP, and production stages. 