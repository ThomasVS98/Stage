# Stage
In deze repository ontwikkel ik een een AI-agent die fungeert als digitale assistent.

## Overzicht
Ik ontwikkel dus een agent die gebruikersvragen ontvangt en op basis van die vragen dan een antwoord met doorverwijzingen genereert. Indien onvoldoende informatie, zal een intake opstarten die leidt tot een automatische ticket via TOPdesk.

## Architectuur
Deze oplossing zal gerealiseerd worden via een RAG-framework. Deze zal het Large Language Model de nodige context geven voor een correct en relevant antwoord. Het RAG-systeem zal gebruiken maken van een zelf gekozen embedding model en vector store. De volledige tool stack is open-source.


```
Stage
├─ api
│  ├─ main.py
│  ├─ models
│  │  └─ source_model.py
│  └─ routes
│     ├─ admin_routes.py
│     ├─ intake_routes.py
│     └─ rag_routes.py
├─ clients
│  ├─ ms_graph_client.py
│  └─ topdesk_client.py
├─ config
│  ├─ settings.py
│  └─ sources.json
├─ frontend
│  └─ app.py
├─ ingestion
│  ├─ ingest_pipeline.py
│  ├─ ingest_tickets.py
│  ├─ loaders
│  │  ├─ onedrive_loader.py
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
│  ├─ intake
│  │  ├─ intake_service.py
│  │  ├─ intake_state.py
│  │  └─ validation.py
│  └─ orchestrator.py
├─ stores
│  └─ session_store.py
├─ temp_sharepoint
└─ utils
   ├─ config_loader.py
   ├─ exceptions.py
   ├─ logging.py
   └─ __init__.py

```