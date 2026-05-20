<div align="center">
  
  
  # 🏢 Real Estate AI Insights & Verification Platform

  **Transforming Real Estate with Intelligent AI and Immutable Blockchain Trust**

  [![Next.js](https://img.shields.io/badge/Next.js-black?logo=next.js)](https://nextjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com/)
  [![Algorand](https://img.shields.io/badge/Algorand-000000?logo=algorand&logoColor=white)](https://algorand.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org/)
</div>

---

An enterprise-grade, microservices-driven platform engineered to revolutionize property search, analysis, and verification. Built for the modern web, this system blends state-of-the-art **Retrieval-Augmented Generation (RAG)** for intelligent property insights with **Algorand Blockchain Technology** for immutable data integrity and trust.

---

## 📑 Table of Contents
<details>
<summary>Click to expand</summary>

- [Hackathon Blockchain Submission Details](#-hackathon-blockchain-submission-details)
- [Demo Preview](#-demo-preview)
- [Key Highlights](#-key-highlights)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Microservices Overview](#-microservices-overview)
- [AI & RAG Pipeline](#-ai--rag-pipeline)
- [Blockchain Verification Flow](#-blockchain-verification-flow)
- [Folder Structure](#-folder-structure)
- [Installation](#-installation)
- [Environment Variables](#-environment-variables)
- [Running with Docker](#-running-with-docker)
- [API Endpoints](#-api-endpoints)
- [Screenshots](#-screenshots)
- [Performance & Security](#-performance--security)
- [Future Improvements](#-future-improvements)
- [Troubleshooting & FAQ](#-troubleshooting--faq)
- [Contribution Guide](#-contribution-guide)
- [Authors](#-authors)

</details>

---

## 🏆 Hackathon Blockchain Submission Details

### Project
**AI + RAG + Real Estate Platform** with Algorand TestNet property verification.

### Network Status
- **Network**: Algorand TestNet
- **Status**: Deployed and proof-write verified
- **Node Provider**: AlgoNode TestNet
- **Algod Endpoint**: https://testnet-api.algonode.cloud
- **Indexer Endpoint**: https://testnet-idx.algonode.cloud
- **Explorer**: https://testnet.algoexplorer.io

### Contract Details
- **Smart Contract**: Property Verification Smart Contract
- **Purpose**: Store a lightweight verification proof for a seller property listing.
- **APP_ID**: `762869297`
- **CONTRACT_ADDRESS**: `TEFR3OFQYD5WKMEWHUUDD35S4X4IKRSHCIDDJQQWEPSQNV33FWAUBUTSHE`
- **DEPLOY_TX_ID**: `IHB7FMCQ2MAMPMWJJK27VEKWBZAMIBBJ4F6AZ4UKTPUH23EFWJEQ`

### Explorer Links
- **Application**: [AlgoExplorer Application 762869297](https://testnet.algoexplorer.io/application/762869297)
- **Deployment Transaction**: [AlgoExplorer Deploy TX](https://testnet.algoexplorer.io/tx/IHB7FMCQ2MAMPMWJJK27VEKWBZAMIBBJ4F6AZ4UKTPUH23EFWJEQ)

### Live Proof Transaction
- **Proof TX Hash**: `RLEP67JTGESSQGHJYMTOQTFAIFWGT7I3DCU3YWN3XQ7ULWGEXVXQ`
- **Proof TX Explorer**: [AlgoExplorer Proof TX](https://testnet.algoexplorer.io/tx/RLEP67JTGESSQGHJYMTOQTFAIFWGT7I3DCU3YWN3XQ7ULWGEXVXQ)

### Stored Proof Fields
The contract stores only hashes and proof metadata:
- `propertyId`
- `propertyHash`
- `documentHash`
- `walletAddress`
- `timestamp`

### Latest Verified Demo Record
- **propertyId**: `demo-skyline-001`
- **propertyHash**: `99f30901a195b2f300d460dd79a5dfbc1985562dd9be7696c09537ee7dadb105`
- **documentHash**: `demo-document-hash`
- **walletAddress**: `DEMO-WALLET-ADDRESS`
- **timestamp**: `1779215679`

### Wallet Integration Details
- **Ecosystem Integration Used**: Pera Wallet SDK
- **Package**: `@perawallet/connect`
- **Frontend Store**: `frontend/store/useWallet.ts`
- **Navbar Integration**: `frontend/components/Navbar.tsx`
- **Seller Flow Integration**: `frontend/app/seller/page.tsx`

### Wallet Features
- Connect Pera Wallet
- Approve connection in Pera popup
- Show shortened wallet address in UI
- Reconnect existing Pera session
- Disconnect wallet
- Keep `walletAddress` optional in seller verification payload

### Blockchain Architecture
- Frontend Next.js app
- `->` FastAPI backend
- `->` `backend/app/services/verify_service.py`
- `->` `backend/app/services/blockchain_service.py`
- `->` blockchain microservice at `http://blockchain:8002/verify`
- `->` Algorand TestNet

The backend does not talk directly to Algorand. All Algorand SDK calls stay inside the blockchain microservice.

### Verification Workflow
1. Seller connects Pera Wallet.
2. Seller enters property metadata and document reference.
3. Frontend sends an optional `walletAddress` plus propertyData to `/api/verify`.
4. Backend generates `SHA256(property_json)`.
5. Backend generates `SHA256(document_file` or document reference when no file bytes are provided).
6. Backend forwards proof payload to the blockchain microservice.
7. Blockchain microservice submits an `ApplicationNoOp` transaction to APP_ID `762869297`.
8. Smart contract stores `propertyId`, `propertyHash`, `documentHash`, `walletAddress`, and `timestamp`.
9. UI shows Blockchain Verified after `tx_id` is returned.
10. Verification can be checked with `blockchain/scripts/verify_data.py`.
11. Verification history is available from the blockchain microservice at `/history`.

### Smart Contract Purpose
The PyTeal smart contract provides a minimal immutable TestNet proof layer for real estate verification. It intentionally does not implement NFTs, escrow, tokenization, DAO logic, payments, images, PDFs, embeddings, AI data, search data, or analytics.

### Deployment Commands

**Install frontend dependency:**
```bash
cd frontend
npm install @perawallet/connect
```

**Install blockchain dependencies:**
```bash
cd blockchain
pip install -r requirements.txt
```

**Deploy to Algorand TestNet:**
```bash
cd D:\hackathon_projects\Real_estate
python blockchain\scripts\deploy.py testnet
```

**AlgoKit-compatible deployment command for submission docs:**
```bash
algokit project deploy testnet
```

**Run Docker stack:**
```bash
cd D:\hackathon_projects\Real_estate
docker compose up --build
```

**Verify stored hashes:**
```bash
cd D:\hackathon_projects\Real_estate
python blockchain\scripts\verify_data.py --property-hash 99f30901a195b2f300d460dd79a5dfbc1985562dd9be7696c09537ee7dadb105 --document-hash demo-document-hash
```

### Required Submission Content
- **APP ID**: `762869297`
- **Contract Address**: `TEFR3OFQYD5WKMEWHUUDD35S4X4IKRSHCIDDJQQWEPSQNV33FWAUBUTSHE`
- **Deploy TX Hash**: `IHB7FMCQ2MAMPMWJJK27VEKWBZAMIBBJ4F6AZ4UKTPUH23EFWJEQ`
- **Proof TX Hash**: `RLEP67JTGESSQGHJYMTOQTFAIFWGT7I3DCU3YWN3XQ7ULWGEXVXQ`
- **Network**: Algorand TestNet
- **Explorer App Link**: [Application 762869297](https://testnet.algoexplorer.io/application/762869297)
- **Explorer Deploy TX Link**: [Deploy TX](https://testnet.algoexplorer.io/tx/IHB7FMCQ2MAMPMWJJK27VEKWBZAMIBBJ4F6AZ4UKTPUH23EFWJEQ)
- **Explorer Proof TX Link**: [Proof TX](https://testnet.algoexplorer.io/tx/RLEP67JTGESSQGHJYMTOQTFAIFWGT7I3DCU3YWN3XQ7ULWGEXVXQ)
- **Ecosystem Integration**: Pera Wallet SDK for wallet connection

### Demo Flow
1. Connect Pera Wallet
2. Approve connection
3. Wallet address becomes visible
4. Seller uploads or selects property document
5. AI trust score remains available in existing app flow
6. Property hash generated by backend
7. Document hash generated by backend
8. Verification stored on Algorand TestNet
9. Blockchain Verified badge/result visible
10. Open AlgoExplorer application and transaction links
11. Show live app and proof transaction

### Breakage Prevention Notes
- Existing routes were preserved.
- Existing frontend layout and Tailwind classes were preserved.
- Existing FastAPI service boundary was preserved.
- Existing Docker services, ports, networking, and hot reload assumptions were preserved.
- RAG, search, and data pipeline services were not refactored.
- Only minimal blockchain-specific integration points were changed.

---

## 🎥 Demo Preview

Watch the full demo on YouTube:
[![Demo Video](https://img.youtube.com/vi/bn2UhVcfqh8/0.jpg)](https://youtu.be/bn2UhVcfqh8?si=iDUAAlYLUnXuN8va)

---

## 🚀 Key Highlights

- **Complex Microservices Architecture**: Decoupled, horizontally scalable services communicating seamlessly via REST API and orchestrated completely within Docker.
- **Advanced AI Integration**: Custom RAG pipeline using FAISS and Groq LLMs to empower users to "chat" directly with real estate data.
- **Web3 Meets PropTech**: Practical application of blockchain to solve real-world trust issues in real estate through immutable verification.
- **Robust Data Engineering**: Automated ETL pipelines handling data scraping, geospatial encoding, and deduplication continuously.

---

## ✨ Features

- **🧠 AI-Powered Contextual Insights**: Query property trends, neighborhood statistics, and amenities through a natural language interface.
- **🔗 Blockchain Auditing**: Every property listing is hashed and anchored to the Algorand blockchain to guarantee immutability.
- **🗺️ Interactive Geospatial Analysis**: Advanced map views, radius searching, and geographic filtering.
- **⚡ Blazing Fast UX**: Built on Next.js and Tailwind CSS for SSR, SEO optimization, and a seamless client-side experience.
- **🔄 Automated Data Ingestion**: Background workers scrape, validate, and vectorize property updates dynamically.

---

## 🏗️ Architecture

The application employs a cloud-native, domain-driven microservices layout.

![System Architecture Diagram](architecture.png)

### System Flowchart

```mermaid
flowchart TD
    User(("User"))

    subgraph Docker["Docker Compose Environment"]
        %% Client Layer
        subgraph ClientLayer["Client Layer"]
            Frontend["Frontend: Next.js"]
        end

        %% Core Backend Layer
        subgraph CoreBackend["Core Backend Layer"]
            Backend["Backend: FastAPI"]
            MapsSvc["Maps Service"]
            PropertySvc["Property Service"]
            RAGConn["RAG Connector"]
        end

        %% AI / RAG Engine
        subgraph RAGEngine["AI / RAG Engine"]
            RAGSvc["RAG Service: FastAPI"]
            Embedder["Embedder: MiniLM/Fallback"]
        end

        %% Blockchain Verification
        subgraph BlockchainLayer["Blockchain Verification"]
            BlockchainSvc["Blockchain Service"]
        end

        %% Data Pipeline Layer
        subgraph DataPipeline["Data Pipeline Layer"]
            DataWorker["Data Pipeline Worker"]
        end

        %% Data Storage Layer
        subgraph DataStorage["Data Storage Layer"]
            Postgres["PostgreSQL"]
            VectorStore["FAISS Vector Store"]
        end
    end

    subgraph External["External Services: APIs & Networks"]
        GeoAPI["Google Geocoding API"]
        GroqAPI["Groq LLM API"]
        Algorand["Algorand Network"]
        Scraped["Scraped Websites"]
    end

    %% Interactions
    User -->|Interacts with UI| Frontend
    Frontend -->|REST POST /api/*| Backend

    Backend -->|Resolve Location| MapsSvc
    Backend -->|Filter & Fetch| PropertySvc
    Backend -->|Get Insights| RAGConn
    
    Backend -.->|Fallback| GeoAPI
    Backend -.-> MapsSvc
    RAGConn -->|Prompt & Context| RAGSvc
    Backend -.->|Prompt & Context| RAGSvc
    Backend -.->|Verify Hash| BlockchainSvc

    RAGSvc -->|Prompt & Context| GroqAPI
    RAGSvc <--> Embedder
    RAGSvc -->|Read/Write Vectors| VectorStore

    BlockchainSvc -->|Verify Hash| Algorand

    DataWorker -.->|Read averages| Postgres
    DataWorker --> VectorStore
    DataWorker -.-> Scraped
    
    %% Styling
    classDef ui fill:#1E293B,stroke:#38BDF8,stroke-width:2px,color:#F8FAFC;
    classDef backend fill:#0F172A,stroke:#10B981,stroke-width:2px,color:#F8FAFC;
    classDef ai fill:#0F172A,stroke:#8B5CF6,stroke-width:2px,color:#F8FAFC;
    classDef blockchain fill:#0F172A,stroke:#F59E0B,stroke-width:2px,color:#F8FAFC;
    classDef data fill:#0F172A,stroke:#EF4444,stroke-width:2px,color:#F8FAFC;
    classDef ext fill:#1E293B,stroke:#94A3B8,stroke-width:2px,color:#F8FAFC;

    class Frontend ui;
    class Backend,MapsSvc,PropertySvc,RAGConn backend;
    class RAGSvc,Embedder ai;
    class BlockchainSvc blockchain;
    class DataWorker,Postgres,VectorStore data;
    class GeoAPI,GroqAPI,Algorand,Scraped ext;
```

---

## 💻 Tech Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend UI** | Next.js 14, React, TypeScript, Tailwind CSS, Zustand |
| **Core API Gateway** | Python, FastAPI, Pydantic, Uvicorn |
| **AI / RAG Engine** | Groq API, FAISS, MiniLM Embeddings, Langchain |
| **Blockchain** | Algorand SDK, PyTeal (Smart Contracts) |
| **Data Storage** | PostgreSQL, SQLAlchemy, FAISS Vector Store |
| **DevOps & Infrastructure** | Docker, Docker Compose, GitHub Actions |

---

## 🧩 Microservices Overview

- **Frontend (`/frontend`)**: Serves the user interface. Handles routing, state management, and maps rendering.
- **Backend API (`/backend`)**: The main gateway handling user requests, orchestrating interactions between the property database, maps, blockchain, and AI services.
- **RAG Engine (`/rag_engine`)**: A specialized, independent NLP service responsible for text chunking, embedding generation, semantic similarity search in FAISS, and final LLM answer synthesis.
- **Blockchain Service (`/blockchain`)**: An isolated service executing Algorand Web3 transactions and verifying PyTeal smart contracts.
- **Data Pipeline (`/data_pipeline`)**: Asynchronous workers and cron jobs dedicated to continuous data ingestion, cleaning, and indexing.

---

## 🤖 AI & RAG Pipeline

Our Retrieval-Augmented Generation approach avoids LLM hallucination by rooting answers in verified data.
1. **Ingestion**: Raw real-estate descriptions and statistics are chunked using semantic splitters.
2. **Embedding**: Chunks are processed via local MiniLM embeddings.
3. **Storage**: Vectors are indexed in FAISS for sub-millisecond retrieval.
4. **Retrieval**: User queries are embedded, matched in FAISS, and context is injected into a strict system prompt.
5. **Generation**: Groq's high-speed API processes the prompt and returns precise, data-backed insights.

---

## 🔗 Blockchain Verification Flow

To establish absolute trust, property verification data is anchored on the **Algorand Blockchain** using custom PyTeal smart contracts.

### `property_verification.py` (PyTeal Contract)
Acts as a decentralized registry for property data proofs.
- **State Variables Stored:**
  - `propertyId`: Unique identifier of the real estate listing.
  - `propertyHash`: Cryptographic hash of the property's metadata.
  - `documentHash`: Hash of the official legal/registration documents.
  - `walletAddress`: The Algorand wallet of the entity verifying the property.
  - `timestamp`: The exact epoch time of verification.
  - `creator`: The deployer's address enforcing strict access control.

*Workflow:* The `Blockchain Service` invokes a NoOp transaction to update the global state with property attributes, cryptographically proving data existed at that time and hasn't been tampered with.

---

## 📂 Folder Structure

```text
Real_estate/
├── backend/                # Core FastAPI handling business logic, routes, and DB
│   ├── app/                # Main application package
│   │   ├── config/         # App constants & settings
│   │   ├── db/             # PostgreSQL connection logic
│   │   ├── models/         # Pydantic Request/Response models
│   │   ├── routes/         # Endpoints (ai, property, search, verify)
│   │   └── services/       # Integrations (geo_service, rag_connector, blockchain_service)
├── blockchain/             # Algorand Smart Contracts and Web3 APIs
│   ├── scripts/            # Deployment scripts
│   ├── sdk/                # Algo client utilities
│   └── smart_contracts/    # PyTeal contracts (property_verification.py)
├── data_pipeline/          # Asynchronous workers for ETL
│   ├── collectors/         # Govt & Listing scrapers
│   ├── loaders/            # DB & Vector DB writers
│   └── processors/         # Deduplicator, Validator, Geo-encoder
├── docker/                 # Container definitions for all services
│   ├── backend.Dockerfile
│   ├── docker-compose.yml
│   └── frontend.Dockerfile
├── frontend/               # Next.js Application UI
│   ├── app/                # Next.js App Router pages and layouts
│   ├── components/         # Reusable UI (PropertyCard, Map, ChatBox, BlockchainBadge)
│   ├── lib/                # API helpers and custom hooks
│   └── store/              # Zustand state management
├── rag_engine/             # Dedicated LLM and Vector Engine
│   ├── embeddings/         # FAISS Vector store integration
│   ├── generation/         # LLM Client (Groq) and Prompts
│   ├── ingestion/          # Data chunkers and cleaners
│   └── retrieval/          # Ranker and retriever logic
└── shared/                 # Shared utilities like common loggers
```

---

## 🛠️ Installation

### Prerequisites
- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose
- Node.js (v18+) & Python (3.10+) (For local, non-docker development)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/atharv0o/Real_estate.git
   cd Real_estate
   ```

---

## 🔐 Environment Variables

Create a `.env` file in the root directory. Configure the following keys:

```env
# AI Services
GROQ_API_KEY=your_groq_api_key

# Blockchain Identity
ALGORAND_MNEMONIC="your twenty five word mnemonic phrase..."
ALGORAND_NODE_TOKEN=your_algorand_node_token
ALGORAND_NODE_URL=https://testnet-api.algonode.cloud

# Database (Automatically mapped in Docker Compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=realestate
```

---

## 🐳 Running with Docker

This project is built to be run entirely in Docker, mapping all microservice ports automatically.

1. **Build and Run All Services**
   ```bash
   docker-compose up --build -d
   ```
2. **Access the Application**
   - **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **RAG Engine Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
   - **Blockchain Docs**: [http://localhost:8002/docs](http://localhost:8002/docs)

3. **Tear Down**
   ```bash
   docker-compose down -v
   ```

---

## 📡 API Endpoints

Our API adheres to OpenAPI specifications. Below are a few core examples.

### 1. Ask AI about a Property
```bash
curl -X 'POST' \
  'http://localhost:8000/api/ai/ask' \
  -H 'Content-Type: application/json' \
  -d '{
  "property_id": "12345",
  "question": "Is this property in a flood zone and what are the nearby schools?"
}'
```

### 2. Verify Property Blockchain Hash
```bash
curl -X 'GET' \
  'http://localhost:8000/api/verify/12345' \
  -H 'accept: application/json'
```

---

## 📸 Screenshots

<div align="center">
  <img src="https://via.placeholder.com/600x300.png?text=Dashboard+View" alt="Dashboard" width="48%" />
  <img src="https://via.placeholder.com/600x300.png?text=Interactive+Map" alt="Map View" width="48%" />
  <br/>
  <img src="https://via.placeholder.com/600x300.png?text=AI+Chatbot" alt="AI Insights" width="48%" />
  <img src="https://via.placeholder.com/600x300.png?text=Blockchain+Audit" alt="Blockchain Details" width="48%" />
</div>

*(Note: Replace placeholders with actual application screenshots in `/docs`)*

---

## ⚡ Performance & Security

- **Scalability**: Docker Compose orchestration allows independent horizontal scaling of the RAG engine or frontend.
- **Latency Optimization**: FAISS index remains in memory for sub-10ms vector similarity lookups. 
- **Security**: 
  - Stateless JWT implementation (if integrated).
  - API Gateway limits exposure of the Blockchain and RAG microservices.
  - No sensitive PII is embedded into the blockchain; only non-reversible cryptographic hashes.

---

## 🔮 Future Improvements

- [ ] **Kubernetes Migration**: Translate `docker-compose.yml` into Helm charts for production K8s deployment.
- [ ] **Multi-Chain Verification**: Expand from Algorand to Polygon for cross-chain proof of existence.
- [ ] **Multimodal AI**: Allow users to upload images of properties and receive GenAI-driven structural analysis.

---

## ❓ Troubleshooting & FAQ

<details>
<summary><b>Docker containers fail to build?</b></summary>
Ensure Docker Desktop is running and you have sufficient memory allocated (minimum 4GB recommended for the RAG Engine).
</details>

<details>
<summary><b>Blockchain verification returns false?</b></summary>
Verify that your `ALGORAND_NODE_URL` is responsive and that the testnet node isn't rate-limiting your IP.
</details>

<details>
<summary><b>Groq API Errors?</b></summary>
Ensure your `GROQ_API_KEY` is valid and has not exceeded quota limits.
</details>

---

## 🤝 Contribution Guide

We welcome contributions from the community!

1. **Fork** the repository
2. **Clone** your fork locally
3. **Branch** off `main` (`git checkout -b feature/amazing-feature`)
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to your fork (`git push origin feature/amazing-feature`)
6. **Open a Pull Request** against the `main` branch.

---

## 👥 Authors

- **Atharv Chivte** - [![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/atharvchivate/)
- **Aseem Gulbarga** - [![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/aseem-gulbarga-5704b12b0/)
- **Manoj Jeur** - [![LinkedIn](https://img.shields.io/badge/LinkedIn-Profile-0A66C2?style=flat&logo=linkedin)](https://www.linkedin.com/in/manoj-jeur-3845b02b0/)

---
<div align="center">
  <i>If you found this project helpful, please consider leaving a ⭐!</i>
</div>
