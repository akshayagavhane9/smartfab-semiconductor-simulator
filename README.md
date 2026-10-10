
# SmartFab — Semiconductor MES & AMHS Simulator

A full-stack semiconductor manufacturing automation
simulator demonstrating Manufacturing Execution Systems
(MES), Automated Material Handling Systems (AMHS),
equipment simulation, and manufacturing workflows.

## Problem Statement

Semiconductor manufacturing requires coordinated wafer
lot tracking, equipment operations, process routing,
and material transportation.

SmartFab simulates these operations with a focus on
data integrity, automation, and failure handling.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy
- Database: PostgreSQL, Psycopg
- Infrastructure: Docker Compose
- Frontend (planned): React, TypeScript
- Testing (planned): Pytest

## Implemented Features

- FastAPI application and health-check endpoint
- PostgreSQL database running in Docker
- Wafer lot data model and persistence
- Manufacturing route and process-step models
- Four-step manufacturing route
- Foreign-key relationships and database constraints
- SQL-based manufacturing step retrieval

## Manufacturing Route

1. Deposition
2. Lithography
3. Etching
4. Inspection

## In Development

- Wafer lot management REST APIs
- Automated manufacturing state transitions
- AMHS carrier transportation
- Equipment monitoring and failure simulation
- React operations dashboard
- Automated integration testing and CI/CD

## Project Status

Active development — backend and MES database foundation.

This is a manufacturing simulator and does not
control real semiconductor equipment.
