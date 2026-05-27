# Architecture

## Overview
Docify uses a Flask application factory with blueprints and a modular chatbot package. The chatbot is FAQ-first with hybrid retrieval and a safe fallback.

## App Structure
- app/ - Flask app package (factory, blueprints, services, middleware)
- chatbot/ - Unified chatbot module
- templates/ - HTML templates
- instance/ - SQLite database storage

## Request Flow
- app/__init__.py creates the Flask app and registers blueprints.
- app/routes/* handles HTTP endpoints.
- app/services/chatbot_service.py delegates to chatbot/.
- chatbot/ loads FAQ content and returns a response.
