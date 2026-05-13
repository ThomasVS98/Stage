# AI-Agent

Deze repository bevat de implementatie van een AI-agent die fungeert als digitale assistent voor het beantwoorden van gebruikersvragen en het ondersteunen van supportprocessen.

---

## Overzicht

De agent verwerkt gebruikersvragen en genereert antwoorden op basis van interne kennisbronnen via een Retrieval-Augmented Generation (RAG) pipeline.

Wanneer onvoldoende informatie beschikbaar is, wordt automatisch een intakeprocedure gestart. Deze intake kan leiden tot het aanmaken van een ticket in TOPdesk.

---

## Architectuur

De oplossing is opgebouwd rond een RAG-architectuur waarbij een Large Language Model wordt verrijkt met context uit externe bronnen.

Belangrijke componenten:

- RAG-pipeline (retrieval + reranking + context building)
- Vector database (ChromaDB)
- Embedding model (SentenceTransformers)
- Backend API (FastAPI)
- Intake- en ticketingflow (TOPdesk integratie)
- Monitoring (Langfuse)

---

## Vereisten

- Windows
- Python 3.x

---

## Installatie

Clone de repository en navigeer naar de map:

```
git clone https://github.com/ThomasVS98/Stage.git
cd Stage
```

Maak en activeer een virtual environment:

```
python -m venv venv
venv\Scripts\activate
```

Installeer dependencies:

```
pip install -r requirements.txt
```

---

## Configuratie

Maak een `.env` bestand op basis van `.env.example`:

```
Copy-Item .env.example .env
```

Vul de vereiste waarden in voor:

- SharePoint / Microsoft Graph  
- TOPdesk  
- Langfuse  

---

## LLM Setup

Deze applicatie gebruikt een lokaal model via Ollama.

Download en installeer Ollama via:
https://ollama.com

Download een model, bijvoorbeeld: `ollama pull llama3.2:3b` of `ollama pull mistral:7b`

Zorg dat Ollama actief is voordat je de backend start.

---

## Gebruik

Start de backend:

```
uvicorn api.main:app --reload
```

Start de frontend:

```
streamlit run frontend/app.py
```

---

## Evaluatie

In de map `evaluation/` bevinden zich testsets die gebruikt zijn om de kwaliteit van de retrieval en gegenereerde antwoorden te evalueren.

---

## Projectstructuur

```
Stage
├─ api
│  ├─ main.py
│  ├─ models
│  │  └─ source_model.py
│  └─ routes
│     ├─ admin_routes.py
│     ├─ feedback_routes.py
│     ├─ intake_routes.py
│     └─ rag_routes.py
├─ clients
│  ├─ ms_graph_client.py
│  └─ topdesk_client.py
├─ config
│  ├─ settings.py
│  └─ sources.json
├─ evaluation
│  ├─ test_vragen_llama.xlsx
│  └─ test_vragen_mistral.xlsx
├─ frontend
│  └─ app.py
├─ ingestion
│  ├─ ingest_pipeline.py
│  ├─ ingest_tickets.py
│  ├─ loaders
│  │  ├─ onedrive_loader.py
│  │  ├─ sharepoint_external_links_loader.py
│  │  ├─ sharepoint_loader.py
│  │  └─ topdesk_loader.py
│  ├─ loader_registry.py
│  ├─ preprocessing
│  │  ├─ cleaning.py
│  │  ├─ docling_parser.py
│  │  ├─ docling_worker.py
│  │  └─ __init__.py
│  ├─ processing
│  │  └─ file_processor.py
│  └─ __init__.py
├─ pytest.ini
├─ rag
│  ├─ context_builder.py
│  ├─ embedding.py
│  ├─ llm.py
│  ├─ pipeline.py
│  ├─ prompts.py
│  ├─ reranker.py
│  ├─ retriever.py
│  ├─ ticket_matcher.py
│  ├─ vector_store.py
│  └─ __init__.py
├─ README.md
├─ requirements.txt
├─ services
│  ├─ admin_service.py
│  ├─ feedback_service.py
│  ├─ intake
│  │  ├─ intake_service.py
│  │  ├─ intake_state.py
│  │  └─ validation.py
│  └─ qa_service.py
├─ stores
│  └─ session_store.py
├─ tests
│  ├─ integration
│  │  └─ test_main.py
│  └─ unit
│     ├─ clients
│     │  ├─ test_ms_graph_client.py
│     │  └─ test_topdesk_client.py
│     ├─ ingestion
│     │  ├─ loaders
│     │  │  ├─ test_sharepoint_external_links_loader.py
│     │  │  ├─ test_sharepoint_loader.py
│     │  │  └─ test_topdesk_loader.py
│     │  ├─ preprocessing
│     │  │  ├─ test_cleaning.py
│     │  │  ├─ test_docling_parser.py
│     │  │  └─ test_docling_worker.py
│     │  ├─ processing
│     │  │  └─ test_file_processor.py
│     │  ├─ test_ingest_pipeline.py
│     │  ├─ test_ingest_tickets.py
│     │  └─ test_loader_registry.py
│     ├─ rag
│     │  ├─ test_context_builder.py
│     │  ├─ test_embedding.py
│     │  ├─ test_llm.py
│     │  ├─ test_pipeline.py
│     │  ├─ test_prompts.py
│     │  ├─ test_reranker.py
│     │  ├─ test_retriever.py
│     │  ├─ test_ticket_matcher.py
│     │  └─ test_vector_store.py
│     ├─ services
│     │  ├─ intake
│     │  │  ├─ test_intake_service.py
│     │  │  └─ test_validation.py
│     │  ├─ test_admin_service.py
│     │  ├─ test_feedback_service.py
│     │  └─ test_qa_service.py
│     ├─ stores
│     │  └─ test_session_store.py
│     └─ utils
│        └─ test_config_loader.py
└─ utils
   ├─ config_loader.py
   ├─ exceptions.py
   ├─ logging.py
   └─ __init__.py
```

---

## Opmerking

Deze applicatie maakt gebruik van externe systemen en vereist correcte configuratie van API-sleutels en endpoints.