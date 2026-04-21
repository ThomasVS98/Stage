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
│  ├─ utils
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
│  ├─ intake
│  │  ├─ intake_service.py
│  │  ├─ intake_state.py
│  │  └─ validation.py
│  └─ qa_service.py
├─ stores
│  └─ session_store.py
├─ temp_sharepoint
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
│     │  │  └─ test_docling_parser.py
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