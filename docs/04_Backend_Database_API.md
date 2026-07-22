# Election Management Platform SRS
# Part 4A – Backend Architecture & Folder Structure

Version: 1.0

---

# 1. Overview

The Backend is the core of the Election Management Platform.

Every component communicates through the backend.

The backend is responsible for:

- Authentication
- Authorization
- Election Management
- Candidate Management
- Position Management
- Image Management
- Node Management
- Synchronization
- Report Generation
- Analytics
- Live Result Broadcasting
- Database Operations

The backend must be written entirely in Python.

---

# 2. Technology Stack

Framework

- FastAPI

ASGI Server

- Uvicorn

ORM

- SQLAlchemy 2.x

Validation

- Pydantic

Authentication

- JWT

Password Hashing

- bcrypt

Database

- MySQL

Real-time Communication

- WebSockets

Queue

- FakeRedis (Local Node Only)

Image Processing

- Pillow

Report Generation

- openpyxl
- pandas
- reportlab

Deployment

- Docker (Optional)
- Railway / Render / VPS
- Cloudflare Tunnel

---

# 3. High-Level Architecture

```
                  INTERNET

                      │

             Cloudflare Tunnel

                      │

              FastAPI Backend

       ┌──────────────┼──────────────┐

       │              │              │

 Authentication   REST API     WebSocket

       │              │              │

       └──────────────┼──────────────┘

                 Service Layer

       ┌──────────────┼──────────────┐

       │              │              │

Election Service Candidate Service Node Service

       │              │              │

        SQLAlchemy Repository Layer

                      │

                   MySQL

                      │

      Voting Nodes + Website + Mobile
```

---

# 4. Backend Philosophy

The backend follows:

- Clean Architecture
- Service-Oriented Design
- Repository Pattern
- Dependency Injection
- Modular Components
- Stateless APIs
- Real-time Updates

---

# 5. Architectural Layers

Presentation Layer

↓

API Layer

↓

Authentication Layer

↓

Service Layer

↓

Repository Layer

↓

Database Layer

Each layer has a single responsibility.

---

# 6. Folder Structure

```
backend/

│

├── app/

│   ├── api/

│   ├── auth/

│   ├── config/

│   ├── database/

│   ├── dependencies/

│   ├── middleware/

│   ├── models/

│   ├── repositories/

│   ├── routers/

│   ├── schemas/

│   ├── services/

│   ├── websocket/

│   ├── reports/

│   ├── analytics/

│   ├── node/

│   ├── security/

│   ├── utils/

│   ├── logging/

│   └── main.py

│

├── uploads/

│

├── generated_reports/

│

├── backups/

│

├── logs/

│

├── tests/

│

├── requirements.txt

│

└── Dockerfile
```

---

# 7. Main Application

main.py is responsible for:

- Loading configuration
- Creating FastAPI app
- Registering routers
- Registering middleware
- Registering WebSockets
- Initializing database
- Starting background tasks

Business logic must never exist inside main.py.

---

# 8. API Layer

Responsibilities

- Receive HTTP Requests
- Validate Input
- Authenticate User
- Call Service Layer
- Return Response

API layer never performs business logic.

---

# 9. Service Layer

Every business rule belongs here.

Examples

Election Service

Candidate Service

Position Service

Report Service

Analytics Service

Authentication Service

Synchronization Service

Node Service

Image Service

Settings Service

---

# 10. Repository Layer

Repositories communicate with SQLAlchemy.

Example

```
CandidateRepository

↓

Create Candidate

Update Candidate

Delete Candidate

Find Candidate

Search Candidate
```

Repositories never perform business rules.

---

# 11. Models

SQLAlchemy models represent database tables.

Examples

User

Candidate

Election

Position

Node

Vote

House

AuditLog

Image

Settings

---

# 12. Schemas

Pydantic schemas validate data.

Every endpoint should use:

Input Schema

↓

Validation

↓

Service

↓

Output Schema

Never expose SQLAlchemy models directly.

---

# 13. Configuration Module

Centralized configuration.

Environment Variables

```
DATABASE_HOST

DATABASE_PORT

DATABASE_NAME

DATABASE_USER

DATABASE_PASSWORD

JWT_SECRET

JWT_EXPIRY

UPLOAD_FOLDER

REPORT_FOLDER

WEBSOCKET_TIMEOUT
```

No hardcoded secrets.

---

# 14. Authentication Module

Responsibilities

Login

Logout

Refresh Token

Password Hashing

JWT Generation

Role Validation

Session Expiry

---

# 15. Security Module

Handles

JWT

Password Hashing

Node Authentication

Permission Checking

CSRF (if applicable)

Rate Limiting

Security Headers

---

# 16. Node Module

Responsible for

Node Registration

Heartbeat

Synchronization

Version Checking

Configuration Download

Health Monitoring

Queue Status

---

# 17. WebSocket Module

Responsible for

Live Results

Dashboard Updates

Node Status

Synchronization Updates

Notifications

Administrator Broadcasts

---

# 18. Report Module

Responsible for

Excel

CSV

PDF

Charts

Statistics

Winner Calculation

---

# 19. Analytics Module

Calculates

Vote Counts

Percentages

Rankings

House Statistics

Turnout

Node Performance

---

# 20. Image Module

Handles

Upload

Crop

Rotate

Resize

Thumbnail Generation

Storage

Serving Images

---

# 21. Middleware

Global middleware includes

Authentication

Logging

Rate Limiting

CORS

Request Timing

Exception Handling

Security Headers

---

# 22. Logging Module

Separate log files

Application

Authentication

Node

Synchronization

Database

Reports

Errors

Logs rotate automatically.

---

# 23. Background Tasks

Run asynchronously.

Tasks include

Heartbeat Monitoring

Queue Cleanup

Expired Session Cleanup

Temporary File Cleanup

Database Health Check

Automatic Backup

Notification Dispatch

---

# 24. Dependency Injection

Use FastAPI Depends()

Example

```
Database Session

↓

Authenticated User

↓

Role Validation

↓

Service

↓

Endpoint
```

No manual object creation inside endpoints.

---

# 25. Exception Handling

Create custom exceptions.

Examples

AuthenticationError

ValidationError

NodeOfflineError

ElectionLockedError

SynchronizationError

DatabaseConnectionError

All exceptions return consistent JSON.

---

# 26. Response Format

Every REST endpoint returns:

Success

```
{
  "success": true,
  "message": "Candidate created successfully",
  "data": {}
}
```

Failure

```
{
  "success": false,
  "message": "Validation failed",
  "errors": []
}
```

Maintain one consistent API format.

---

# 27. Background Scheduler

Scheduled tasks

Every 10 Seconds

Heartbeat Validation

Every Minute

Queue Cleanup

Every Hour

Log Rotation

Daily

Backup

Weekly

Report Cleanup

---

# 28. File Storage

Uploads

```
uploads/

candidates/

themes/

logos/

backgrounds/

temp/
```

Generated Reports

```
reports/

excel/

csv/

pdf/
```

Backups

```
backups/

database/

configuration/
```

---

# 29. Coding Standards

Use

PEP8

Type Hints

Docstrings

Logging

Async Endpoints

Meaningful Variable Names

Maximum Function Length

~100 lines

Maximum File Length

~600 lines (preferred)

Business logic must never be duplicated.

---

# 30. Testing Structure

```
tests/

test_auth.py

test_candidate.py

test_position.py

test_election.py

test_node.py

test_reports.py

test_sync.py

test_api.py
```

Every service should have unit tests.

---

# 31. Scalability

Backend should support

Additional Elections

Additional Houses

Additional Voting Nodes

Additional Administrators

Additional Schools (future)

No redesign required.

---

# 32. Acceptance Criteria

The backend architecture is complete when:

✓ Modular architecture implemented.

✓ Business logic isolated from API.

✓ SQLAlchemy used for persistence.

✓ Pydantic used for validation.

✓ JWT authentication implemented.

✓ Repository pattern followed.

✓ Dependency Injection used consistently.

✓ WebSocket module separated.

✓ Logging centralized.

✓ Background tasks operational.

✓ Clean folder structure maintained.

✓ Codebase remains maintainable and extensible.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

The backend shall follow **Clean Architecture** principles.

Mandatory requirements:

- No business logic inside API routes.
- Every module has a single responsibility.
- Services communicate through repositories only.
- SQLAlchemy models are never exposed directly through the API.
- All configuration is environment-based.
- The backend must remain completely independent of the desktop application UI.
- All communication with voting nodes occurs through authenticated REST APIs and WebSockets.
- The architecture should support future expansion without major restructuring.

---

# Architecture Summary

```
Desktop Voting App
          │
          │ REST + WebSocket
          ▼
     FastAPI Backend
          │
   ┌──────┼──────┐
   ▼      ▼      ▼
Services Repositories WebSockets
          │
     SQLAlchemy ORM
          │
        MySQL
          │
     NiceGUI Website
```

---

End of Part 4A

# Election Management Platform SRS
# Part 4B-1 – Database Design (MySQL) – Core Tables

Version: 1.0

---

# 1. Overview

The MySQL database serves as the **single source of truth** for the Election Management Platform.

All official election information is stored here.

The desktop voting application only stores temporary data locally for offline operation and synchronization.

The website database stores:

- Administrators
- Elections
- Houses
- Positions
- Candidates
- Candidate Images
- Published Configurations
- Votes
- Reports
- Audit Logs
- Settings

The database shall be normalized to **Third Normal Form (3NF)**.

---

# 2. Database Design Principles

The schema shall follow these principles:

- UUID primary keys wherever practical.
- Foreign key constraints enabled.
- Cascade deletes only where safe.
- Soft delete preferred for master records.
- UTC timestamps.
- Automatic created_at / updated_at fields.
- Indexed search columns.
- ACID-compliant transactions.

---

# 3. Entity Relationship Overview

```
Users
   │
   │
   ├──────────────┐
   │              │
   ▼              ▼

Elections     Audit Logs

   │

   ├───────────────┐

   ▼               ▼

Positions      Houses

   │               │

   └──────┐   ┌────┘
          ▼   ▼

      Candidates

          │

          ▼

 Candidate Images
```

---

# 4. Table: users

Purpose

Stores administrator and viewer accounts.

Table Name

```
users
```

Columns

| Column | Type | Description |
|----------|------|-------------|
| id | CHAR(36) | UUID Primary Key |
| username | VARCHAR(100) | Login Username |
| full_name | VARCHAR(150) | Display Name |
| email | VARCHAR(150) | Email |
| password_hash | VARCHAR(255) | bcrypt hash |
| role_id | CHAR(36) | FK → roles |
| active | BOOLEAN | Active Status |
| last_login | DATETIME | Last Login |
| created_at | DATETIME | Creation Timestamp |
| updated_at | DATETIME | Last Modified |

Indexes

```
username UNIQUE

email UNIQUE

role_id
```

---

# 5. Table: roles

Purpose

Stores available system roles.

Table

```
roles
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| role_name | VARCHAR(50) |
| description | TEXT |

Default Records

```
Super Administrator

Administrator

Viewer
```

---

# 6. User ↔ Role Relationship

```
One Role

↓

Many Users
```

Example

```
Administrator

↓

John

↓

Sarah

↓

David
```

---

# 7. Table: elections

Purpose

Stores election information.

Table

```
elections
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| election_name | VARCHAR(200) |
| academic_year | VARCHAR(20) |
| description | TEXT |
| version | INTEGER |
| status | ENUM |
| start_time | DATETIME |
| end_time | DATETIME |
| logo_path | VARCHAR(255) |
| created_by | CHAR(36) |
| created_at | DATETIME |
| updated_at | DATETIME |

Status Values

```
Draft

Published

Live

Completed

Archived
```

Indexes

```
status

version

academic_year
```

---

# 8. Table: houses

Purpose

Stores available school houses.

Table

```
houses
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| house_name | VARCHAR(50) |
| color | VARCHAR(30) |
| logo_path | VARCHAR(255) |
| active | BOOLEAN |

Default Records

```
Pallava

Pandya

Chera

Chola
```

---

# 9. Table: positions

Purpose

Stores election positions.

Table

```
positions
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| election_id | CHAR(36) |
| election_type | ENUM |
| position_name | VARCHAR(150) |
| winner_count | INTEGER |
| display_order | INTEGER |
| active | BOOLEAN |
| created_at | DATETIME |
| updated_at | DATETIME |

Election Types

```
Regular

House
```

Example

```
School Pupil Leader

Sports Captain

House Captain

Vice Captain
```

Indexes

```
election_id

display_order

election_type
```

---

# 10. Position Relationship

```
Election

↓

Many Positions
```

---

# 11. Table: candidates

Purpose

Stores every candidate.

Table

```
candidates
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| election_id | CHAR(36) |
| position_id | CHAR(36) |
| house_id | CHAR(36) NULL |
| candidate_name | VARCHAR(150) |
| display_order | INTEGER |
| image_id | CHAR(36) |
| status | ENUM |
| created_at | DATETIME |
| updated_at | DATETIME |

Status

```
Draft

Active

Inactive

Published
```

Regular Election

House ID

NULL

House Election

House ID

Required

---

# 12. Candidate Relationship

```
Election

↓

Position

↓

Candidates
```

Example

```
School Pupil Leader

↓

John

↓

Sarah

↓

Kevin
```

---

# 13. Table: candidate_images

Purpose

Stores candidate photographs.

Table

```
candidate_images
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| original_path | VARCHAR(255) |
| processed_path | VARCHAR(255) |
| thumbnail_path | VARCHAR(255) |
| width | INTEGER |
| height | INTEGER |
| file_size | INTEGER |
| mime_type | VARCHAR(50) |
| uploaded_at | DATETIME |
| uploaded_by | CHAR(36) |

---

# 14. Candidate Image Relationship

```
Candidate

↓

One Image
```

Future expansion

```
One Candidate

↓

Multiple Images
```

Architecture should support this.

---

# 15. Foreign Keys

Users

```
role_id

↓

roles.id
```

Elections

```
created_by

↓

users.id
```

Positions

```
election_id

↓

elections.id
```

Candidates

```
election_id

↓

elections.id

position_id

↓

positions.id

house_id

↓

houses.id

image_id

↓

candidate_images.id
```

---

# 16. Cascading Rules

Recommended

Roles

↓

Restrict Delete

Users

↓

Restrict Delete

Election

↓

Cascade Positions

↓

Cascade Candidates

Candidate Images

↓

Restrict Delete

Votes

↓

No Cascade (handled separately)

---

# 17. Soft Delete Policy

Use soft deletes for

Candidates

Positions

Users

Elections

Fields

```
active

deleted_at
```

Never permanently remove historical records unless explicitly required.

---

# 18. Indexing Strategy

Indexes

```
username

email

candidate_name

position_name

house_name

status

version

display_order
```

Composite Indexes

```
(election_id, position_id)

(position_id, display_order)

(election_type, active)
```

---

# 19. Constraints

Examples

```
winner_count > 0

display_order >= 1

candidate_name NOT NULL

position_name NOT NULL

username UNIQUE

email UNIQUE
```

---

# 20. UUID Strategy

Every primary key uses UUID.

Advantages

- No collisions.
- Easier synchronization.
- Safe offline creation.
- Better security than incremental IDs.

Example

```
5c98abdf-4cb7-44f4-ae6b-c35c5df76fd8
```

---

# 21. Timestamp Standards

Every master table includes

```
created_at

updated_at
```

Optional

```
deleted_at
```

Use UTC.

---

# 22. Data Integrity Rules

- Every candidate belongs to one position.
- Every position belongs to one election.
- Every house candidate belongs to exactly one house.
- Every regular candidate has no house assignment.
- Every image belongs to one candidate.
- Every user belongs to one role.

---

# 23. Performance Requirements

Candidate Search

<100 ms

Position Lookup

<50 ms

Election Load

<300 ms

House Lookup

<50 ms

Image Metadata Lookup

<100 ms

---

# 24. Future Expansion

The schema should support:

- Multiple schools
- Additional houses
- Multiple elections running simultaneously
- Multi-language names
- Candidate biographies
- Party/group support
- Election categories

No redesign should be required.

---

# 25. Acceptance Criteria

The Core Database Design is complete when:

✓ UUID primary keys are used.

✓ Foreign key relationships are enforced.

✓ Roles and users are separated.

✓ Elections support versioning.

✓ Regular and House elections share the same schema.

✓ Positions support configurable winner counts.

✓ Candidates support both election types.

✓ Images are stored independently.

✓ Database is normalized to 3NF.

✓ Indexes are added for frequently queried columns.

✓ Soft deletes preserve historical integrity.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

The core database schema forms the foundation of the Election Management Platform.

Mandatory requirements:

- Use SQLAlchemy ORM models that map directly to these tables.
- Enforce foreign key constraints at the database level.
- Store UUIDs as `CHAR(36)` for compatibility.
- Use InnoDB storage engine for transaction support.
- Ensure all timestamps are stored in UTC.
- Avoid redundant data; use relationships instead of duplication.
- Keep the schema extensible for future election types and organizational structures.

---

End of Part 4B-1

# Election Management Platform SRS
# Part 4B-2 – Database Design (MySQL) – Voting & Synchronization Tables

Version: 1.0

---

# 1. Overview

This section defines every database table responsible for voting,
offline synchronization, node management and configuration versioning.

These tables ensure:

- Every vote is securely recorded
- Offline voting is supported
- Duplicate votes are prevented
- Nodes automatically synchronize
- Website always maintains the master copy of votes
- Synchronization is completely reliable

Desktop voting applications never directly modify master tables except through authenticated synchronization APIs.

---

# 2. Synchronization Philosophy

Website

↓

Master Database

↓

Voting Nodes

↓

Offline Queue

↓

Automatic Synchronization

↓

Website Database

Every vote must eventually reach the website exactly once.

---

# 3. Table: voting_nodes

Purpose

Stores every authorized voting machine.

Table

```
voting_nodes
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| node_name | VARCHAR(100) |
| node_secret | VARCHAR(255) |
| election_type | ENUM |
| house_id | CHAR(36) NULL |
| app_version | VARCHAR(20) |
| config_version | INTEGER |
| active | BOOLEAN |
| created_at | DATETIME |
| updated_at | DATETIME |

Election Types

```
Regular

House
```

Example

```
Regular-01

Regular

------------

House-01

Pallava
```

---

# 4. Node Relationship

```
House

↓

Many Nodes
```

Regular nodes have

House ID = NULL

House nodes reference one house.

---

# 5. Table: node_heartbeats

Purpose

Stores node heartbeat history.

Table

```
node_heartbeats
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| node_id | CHAR(36) |
| heartbeat_time | DATETIME |
| queue_size | INTEGER |
| last_vote_time | DATETIME |
| sync_status | ENUM |
| app_version | VARCHAR(20) |
| config_version | INTEGER |
| ip_address | VARCHAR(50) |

Sync Status

```
Healthy

Syncing

Pending

Offline
```

---

# 6. Heartbeat Flow

Desktop

↓

Heartbeat

↓

Website

↓

Database

↓

Dashboard Updated

Heartbeat interval

10 Seconds

---

# 7. Table: votes

Purpose

Stores every synchronized vote.

Table

```
votes
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| vote_uuid | CHAR(36) |
| election_id | CHAR(36) |
| position_id | CHAR(36) |
| candidate_id | CHAR(36) |
| node_id | CHAR(36) |
| election_type | ENUM |
| house_id | CHAR(36) NULL |
| voted_at | DATETIME |
| synced_at | DATETIME |

Important

vote_uuid is globally unique.

This is used to prevent duplicate submissions.

---

# 8. Duplicate Prevention

Every vote receives

UUID

Example

```
f08e8d40-08f3-4ec9-8d6b-73a8f1dd4c17
```

Website checks

Already Exists?

YES

↓

Ignore

NO

↓

Insert Vote

Duplicate voting records are impossible.

---

# 9. Vote Relationships

```
Election

↓

Position

↓

Candidate

↓

Vote

↓

Voting Node
```

---

# 10. Table: vote_queue

Purpose

Tracks synchronization status of every vote.

This table exists only on the website for monitoring. Each desktop node keeps its own in-memory/local queue using FakeRedis plus persistent local storage.

Table

```
vote_queue
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| vote_uuid | CHAR(36) |
| node_id | CHAR(36) |
| received_time | DATETIME |
| processed_time | DATETIME |
| retry_count | INTEGER |
| queue_status | ENUM |

Queue Status

```
Pending

Processing

Completed

Failed
```

---

# 11. FakeRedis Queue

Each desktop node maintains

```
Teacher Votes

↓

Local Queue

↓

FakeRedis

↓

REST API

↓

Website
```

Redis Server is **NOT** required.

FakeRedis operates only inside the application.

---

# 12. Table: sync_logs

Purpose

Stores synchronization history.

Table

```
sync_logs
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| node_id | CHAR(36) |
| sync_start | DATETIME |
| sync_end | DATETIME |
| total_votes | INTEGER |
| successful_votes | INTEGER |
| failed_votes | INTEGER |
| status | ENUM |

Status

```
Success

Partial

Failed
```

---

# 13. Synchronization Process

```
Vote Cast

↓

Local SQLite/MySQL Cache

↓

FakeRedis Queue

↓

Send API Request

↓

Website Validates

↓

Insert Vote

↓

ACK

↓

Queue Removed
```

---

# 14. Retry Logic

If upload fails

```
Vote

↓

Queue

↓

Retry 1

↓

Retry 2

↓

Retry 3

↓

Exponential Backoff

↓

Until Success
```

Votes are never discarded automatically.

---

# 15. Table: published_configurations

Purpose

Stores every published election package.

Table

```
published_configurations
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| election_id | CHAR(36) |
| version | INTEGER |
| package_path | VARCHAR(255) |
| checksum | VARCHAR(128) |
| published_at | DATETIME |
| published_by | CHAR(36) |

---

# 16. Configuration Version Check

Desktop Startup

↓

Get Version

↓

Compare

↓

Download Required?

YES

↓

Download

NO

↓

Continue Voting

---

# 17. Table: node_downloads

Purpose

Stores configuration download history.

Table

```
node_downloads
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| node_id | CHAR(36) |
| configuration_id | CHAR(36) |
| download_time | DATETIME |
| install_status | ENUM |

Install Status

```
Downloaded

Installed

Failed
```

---

# 18. Table: node_sessions

Purpose

Tracks authenticated desktop sessions.

Table

```
node_sessions
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| node_id | CHAR(36) |
| login_time | DATETIME |
| logout_time | DATETIME |
| jwt_token_id | VARCHAR(255) |
| session_status | ENUM |

---

# 19. Synchronization Integrity

Every synchronized vote verifies

✓ Node Exists

✓ JWT Valid

✓ Election Exists

✓ Candidate Exists

✓ Vote UUID Unique

✓ Configuration Version Valid

If any validation fails

↓

Reject Vote

↓

Log Failure

---

# 20. Offline Behaviour

If Internet Lost

↓

Continue Voting

↓

Store Locally

↓

Queue Votes

↓

Reconnect

↓

Automatic Upload

Teacher intervention is never required.

---

# 21. Conflict Resolution

If duplicate vote received

↓

Ignore

If outdated configuration detected

↓

Reject

↓

Ask Node to Download Latest Version

---

# 22. Indexing Strategy

Indexes

```
vote_uuid UNIQUE

candidate_id

position_id

node_id

election_id

house_id

heartbeat_time

config_version

queue_status
```

Composite Indexes

```
(node_id, heartbeat_time)

(election_id, candidate_id)

(election_id, position_id)

(node_id, queue_status)
```

---

# 23. Foreign Keys

```
votes.node_id

↓

voting_nodes.id

votes.election_id

↓

elections.id

votes.position_id

↓

positions.id

votes.candidate_id

↓

candidates.id

votes.house_id

↓

houses.id

node_heartbeats.node_id

↓

voting_nodes.id

sync_logs.node_id

↓

voting_nodes.id
```

---

# 24. Performance Requirements

Heartbeat Insert

<100 ms

Vote Insert

<50 ms

Sync Validation

<100 ms

Queue Processing

Real-Time

Configuration Check

<200 ms

---

# 25. Data Retention

Retain

Votes

Sync Logs

Node History

Configuration Versions

Download Logs

These records should never be automatically deleted unless archived by an administrator.

---

# 26. Acceptance Criteria

The Voting & Synchronization schema is complete when:

✓ Every node is uniquely registered.

✓ Heartbeats are stored.

✓ Votes use globally unique UUIDs.

✓ Duplicate vote prevention works.

✓ Synchronization logs are recorded.

✓ Configuration versioning works.

✓ Nodes automatically download published configurations.

✓ Offline voting functions correctly.

✓ Automatic retries function without manual intervention.

✓ Synchronization history is fully auditable.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

Mandatory requirements:

- Every vote must have a globally unique `vote_uuid`.
- Desktop applications use a **local persistent queue + FakeRedis** for fast in-memory processing. Redis Server installation is never required.
- Synchronization is idempotent: resending the same vote must never create duplicates.
- Heartbeats are sent every 10 seconds while the application is running.
- Node authentication must use a unique secret and JWT-based session.
- Configuration packages must include a checksum to verify integrity before installation.
- Voting must continue uninterrupted during network failures and automatically synchronize once connectivity is restored.

---

End of Part 4B-2

# Election Management Platform SRS
# Part 4B-3 – Database Design (MySQL) – Reports, Settings & Audit Tables

Version: 1.0

---

# 1. Overview

This section defines all database tables responsible for:

- Report Generation
- Analytics
- System Settings
- Audit Logging
- User Login History
- Notifications
- Backup Management
- Website Configuration

These tables contain the operational and administrative information of the Election Management Platform.

Unlike vote data, these tables primarily support administration, monitoring, reporting and security.

---

# 2. Entity Relationship Overview

```
Users
   │
   │
   ▼
Audit Logs

Users
   │
   ▼
Login History

Elections
   │
   ▼
Reports

Website
   │
   ▼
System Settings

Users
   │
   ▼
Notifications

System
   │
   ▼
Backups
```

---

# 3. Table: reports

Purpose

Stores metadata about every generated report.

Table

```
reports
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| election_id | CHAR(36) |
| report_name | VARCHAR(200) |
| report_type | ENUM |
| file_path | VARCHAR(255) |
| generated_by | CHAR(36) |
| generated_at | DATETIME |
| file_size | BIGINT |

Report Types

```
Excel

CSV

PDF
```

---

# 4. Report Relationship

```
Election

↓

Many Reports
```

---

# 5. Table: report_downloads

Purpose

Tracks every report download.

Table

```
report_downloads
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| report_id | CHAR(36) |
| downloaded_by | CHAR(36) |
| downloaded_at | DATETIME |
| ip_address | VARCHAR(50) |

---

# 6. Table: system_settings

Purpose

Stores website configuration.

Table

```
system_settings
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| school_name | VARCHAR(255) |
| school_logo | VARCHAR(255) |
| election_logo | VARCHAR(255) |
| primary_color | VARCHAR(20) |
| secondary_color | VARCHAR(20) |
| timezone | VARCHAR(100) |
| maintenance_mode | BOOLEAN |
| created_at | DATETIME |
| updated_at | DATETIME |

Only one active settings record should exist.

---

# 7. Table: mysql_settings

Purpose

Stores website MySQL connection settings.

Table

```
mysql_settings
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| host | VARCHAR(255) |
| port | INTEGER |
| database_name | VARCHAR(150) |
| username | VARCHAR(150) |
| encrypted_password | TEXT |
| updated_by | CHAR(36) |
| updated_at | DATETIME |

Passwords must be encrypted.

Never store plaintext credentials.

---

# 8. Desktop MySQL Settings

Desktop applications store MySQL credentials locally.

They are NOT stored in the website database.

The website only stores its own connection settings.

---

# 9. Table: audit_logs

Purpose

Stores every administrative action.

Table

```
audit_logs
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| user_id | CHAR(36) |
| module | VARCHAR(100) |
| action | VARCHAR(150) |
| old_value | JSON |
| new_value | JSON |
| ip_address | VARCHAR(50) |
| browser | VARCHAR(150) |
| created_at | DATETIME |

Examples

```
Candidate Updated

Election Published

Results Cleared

Login

Logout

Database Updated
```

---

# 10. Audit Relationship

```
User

↓

Many Audit Logs
```

Audit logs must never be edited.

---

# 11. Table: login_history

Purpose

Stores login activity.

Table

```
login_history
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| user_id | CHAR(36) |
| login_time | DATETIME |
| logout_time | DATETIME |
| ip_address | VARCHAR(50) |
| browser | VARCHAR(150) |
| login_status | ENUM |

Login Status

```
Success

Failed

Locked
```

---

# 12. Table: notifications

Purpose

Stores system notifications.

Table

```
notifications
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| title | VARCHAR(255) |
| message | TEXT |
| notification_type | ENUM |
| user_id | CHAR(36) NULL |
| created_at | DATETIME |
| read_status | BOOLEAN |

Notification Types

```
Node Offline

Election Published

Election Started

Election Ended

Backup Completed

Synchronization Failed

Database Error
```

---

# 13. Notification Relationship

```
User

↓

Many Notifications
```

Global notifications

User ID = NULL

---

# 14. Table: backups

Purpose

Tracks system backups.

Table

```
backups
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| backup_type | ENUM |
| file_path | VARCHAR(255) |
| backup_size | BIGINT |
| created_by | CHAR(36) |
| created_at | DATETIME |
| status | ENUM |

Backup Types

```
Database

Configuration

System
```

Status

```
Completed

Running

Failed
```

---

# 15. Table: report_templates

Purpose

Stores report layouts.

Table

```
report_templates
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| template_name | VARCHAR(150) |
| report_type | ENUM |
| active | BOOLEAN |
| created_at | DATETIME |

Future-proof for custom templates.

---

# 16. Table: themes

Purpose

Stores UI themes.

Table

```
themes
```

Columns

| Column | Type |
|----------|------|
| id | CHAR(36) |
| theme_name | VARCHAR(100) |
| primary_color | VARCHAR(20) |
| secondary_color | VARCHAR(20) |
| accent_color | VARCHAR(20) |
| logo_path | VARCHAR(255) |
| active | BOOLEAN |

---

# 17. Foreign Keys

```
reports.election_id

↓

elections.id

reports.generated_by

↓

users.id

audit_logs.user_id

↓

users.id

login_history.user_id

↓

users.id

notifications.user_id

↓

users.id

backups.created_by

↓

users.id
```

---

# 18. Indexing Strategy

Indexes

```
generated_at

created_at

user_id

notification_type

login_status

maintenance_mode

backup_type

report_type
```

Composite Indexes

```
(user_id, created_at)

(election_id, report_type)

(notification_type, read_status)
```

---

# 19. Security Rules

Passwords

Encrypted

Audit Logs

Immutable

Settings

Administrator Only

Reports

Role Based

Backups

Administrator Only

---

# 20. Retention Policy

Keep

Audit Logs

5 Years

Login History

2 Years

Reports

Unlimited

Backups

Administrator Configurable

Notifications

180 Days

Expired records may be archived instead of deleted.

---

# 21. Performance Requirements

Generate Report

<5 Seconds

Audit Insert

<20 ms

Notification Insert

<20 ms

Settings Load

<100 ms

Backup Registration

<100 ms

---

# 22. Soft Delete Policy

Use soft deletes for

Reports

Themes

Templates

Notifications

Never delete audit logs.

---

# 23. Future Expansion

The schema should support:

- Email notifications
- SMS notifications
- Push notifications
- Multi-school deployments
- Multi-language reports
- Custom report templates
- Scheduled report generation

No redesign should be necessary.

---

# 24. Acceptance Criteria

The Reports, Settings & Audit schema is complete when:

✓ Reports are tracked.

✓ Downloads are logged.

✓ Website settings are centrally stored.

✓ MySQL settings are securely stored.

✓ Every administrative action is recorded.

✓ Login history is maintained.

✓ Notifications are tracked.

✓ Backups are registered.

✓ Themes are configurable.

✓ Foreign keys are enforced.

✓ Audit logs cannot be modified.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

Mandatory requirements:

- Store passwords and sensitive configuration using encryption, never plaintext.
- Use JSON columns (`old_value`, `new_value`) in `audit_logs` to capture before/after changes.
- Generate immutable audit records for every administrative operation.
- Maintain a single active `system_settings` record.
- Keep report metadata separate from generated files.
- Support future expansion without requiring schema redesign.
- Ensure all administrative tables include UTC timestamps and appropriate indexes.

---

# Database Summary

The complete database now consists of the following functional groups:

### Core Tables
- users
- roles
- elections
- houses
- positions
- candidates
- candidate_images

### Voting & Synchronization
- voting_nodes
- node_heartbeats
- votes
- vote_queue
- sync_logs
- published_configurations
- node_downloads
- node_sessions

### Reports & Administration
- reports
- report_downloads
- system_settings
- mysql_settings
- audit_logs
- login_history
- notifications
- backups
- report_templates
- themes

This schema provides a scalable, normalized foundation for the Election Management Platform while supporting offline voting, live synchronization, comprehensive reporting, and secure administration.

---

End of Part 4B-3

# Election Management Platform SRS
# Part 4C-1 – REST API Specification – Authentication & User APIs

Version: 1.0

---

# 1. Overview

This document defines the Authentication and User Management REST APIs for the Election Management Platform.

These APIs provide secure authentication for:

- Website Administrators
- Website Viewers
- Voting Nodes
- Desktop Applications

Authentication shall use JWT access tokens.

Passwords shall never be transmitted or stored in plaintext.

---

# 2. Base URL

Development

```
http://localhost:8000/api/v1
```

Production

```
https://your-domain.com/api/v1
```

Every endpoint begins with

```
/api/v1
```

---

# 3. Authentication Flow

```
User

↓

POST /login

↓

Validate Credentials

↓

Generate JWT

↓

Return Token

↓

Use Token

↓

Authorized Requests
```

---

# 4. Authorization Header

Every protected endpoint requires

```
Authorization: Bearer <JWT_TOKEN>
```

Example

```
Authorization: Bearer eyJhbGc...
```

---

# 5. JWT Payload

```
{
    "user_id": "UUID",
    "username": "admin",
    "role": "Administrator",
    "exp": 1710000000
}
```

---

# 6. User Roles

Available roles

```
Super Administrator

Administrator

Viewer

Voting Node
```

---

# 7. Permission Matrix

| Endpoint | Super Admin | Admin | Viewer | Node |
|-----------|-------------|--------|---------|------|
| Login | ✓ | ✓ | ✓ | ✓ |
| Logout | ✓ | ✓ | ✓ | ✓ |
| View Profile | ✓ | ✓ | ✓ | ✓ |
| Create User | ✓ | ✓ | ✗ | ✗ |
| Edit User | ✓ | ✓ | ✗ | ✗ |
| Delete User | ✓ | ✗ | ✗ | ✗ |
| View Users | ✓ | ✓ | ✓ | ✗ |
| Change Password | ✓ | ✓ | ✓ | ✓ |

---

# 8. POST /auth/login

Purpose

Authenticate website users.

Request

```json
{
    "username":"admin",
    "password":"password123"
}
```

Success

```json
{
    "success":true,
    "message":"Login successful",
    "data":{
        "access_token":"JWT",
        "refresh_token":"JWT",
        "expires_in":3600,
        "role":"Administrator"
    }
}
```

Errors

401 Unauthorized

403 Account Disabled

429 Too Many Attempts

---

# 9. POST /auth/logout

Purpose

Invalidate current session.

Request

JWT Required

Response

```json
{
    "success":true,
    "message":"Logout successful"
}
```

---

# 10. POST /auth/refresh

Purpose

Generate a new access token.

Request

```json
{
    "refresh_token":"JWT"
}
```

Response

```json
{
    "access_token":"NEW_TOKEN",
    "expires_in":3600
}
```

---

# 11. GET /users/me

Purpose

Return current logged-in user.

Response

```json
{
    "id":"UUID",
    "username":"admin",
    "full_name":"Election Admin",
    "role":"Administrator"
}
```

---

# 12. GET /users

Purpose

List users.

Permissions

Administrator

Super Administrator

Response

```json
[
    {
        "id":"UUID",
        "username":"admin",
        "role":"Administrator",
        "active":true
    }
]
```

Supports

Pagination

Search

Sorting

---

# 13. POST /users

Purpose

Create user.

Request

```json
{
    "username":"john",
    "full_name":"John Doe",
    "email":"john@example.com",
    "password":"Password@123",
    "role":"Viewer"
}
```

Validation

Username unique

Email unique

Password policy

---

# 14. PUT /users/{id}

Purpose

Update user.

Editable

Full Name

Email

Role

Status

Password (optional)

---

# 15. DELETE /users/{id}

Purpose

Soft delete user.

Rules

Cannot delete own account.

Cannot delete final Super Administrator.

Audit log required.

---

# 16. GET /users/{id}

Returns

Complete user profile.

Includes

Role

Status

Created Date

Last Login

---

# 17. PATCH /users/{id}/status

Purpose

Enable or disable user.

Request

```json
{
    "active":false
}
```

---

# 18. PATCH /users/change-password

Purpose

Change password.

Request

```json
{
    "old_password":"OldPassword",
    "new_password":"NewPassword@123"
}
```

Validation

Current password correct.

Password policy satisfied.

---

# 19. POST /users/reset-password

Purpose

Administrator resets another user's password.

Request

```json
{
    "user_id":"UUID",
    "new_password":"Password@123"
}
```

Audit log mandatory.

---

# 20. GET /roles

Returns

```json
[
    "Super Administrator",
    "Administrator",
    "Viewer"
]
```

---

# 21. POST /auth/node-login

Purpose

Authenticate voting node.

Request

```json
{
    "node_id":"UUID",
    "node_secret":"SECRET"
}
```

Response

```json
{
    "access_token":"JWT",
    "expires_in":86400
}
```

---

# 22. POST /auth/node-refresh

Refresh node JWT.

Desktop application calls automatically.

---

# 23. POST /auth/verify

Purpose

Verify token.

Response

```json
{
    "valid":true,
    "expires_in":2800
}
```

---

# 24. GET /users/activity

Returns

Recent login activity.

Fields

Login

Logout

IP

Browser

Status

---

# 25. GET /audit/user/{id}

Returns

Audit history.

Includes

Login

Logout

Profile changes

Password changes

Role updates

---

# 26. Password Policy

Minimum

8 characters

Require

Uppercase

Lowercase

Number

Special character

Passwords hashed using bcrypt.

---

# 27. Account Lockout

Five failed logins

↓

Account locked

↓

15 Minutes

Administrator may unlock.

---

# 28. Token Expiry

Website

Access Token

1 Hour

Refresh Token

7 Days

Voting Node

24 Hours

Refresh automatically.

---

# 29. Error Responses

Example

```json
{
    "success":false,
    "message":"Invalid username or password"
}
```

Validation Error

```json
{
    "success":false,
    "errors":[
        {
            "field":"email",
            "message":"Email already exists"
        }
    ]
}
```

---

# 30. Rate Limiting

Login

10 requests/minute

Password Reset

5 requests/minute

Token Refresh

20 requests/minute

Protect against brute force attacks.

---

# 31. Security Headers

Include

```
X-Frame-Options

Content-Security-Policy

X-Content-Type-Options

Referrer-Policy

Strict-Transport-Security
```

---

# 32. Audit Logging

Log

Login

Logout

Password Change

Password Reset

Role Change

User Created

User Updated

User Disabled

User Deleted

---

# 33. Validation Rules

Username

3–50 characters

Email

RFC compliant

Password

Policy compliant

Role

Valid enum only

---

# 34. HTTP Status Codes

200

Success

201

Created

400

Validation Error

401

Unauthorized

403

Forbidden

404

Not Found

409

Conflict

422

Validation Failed

429

Rate Limited

500

Internal Error

---

# 35. Acceptance Criteria

Authentication module is complete when:

✓ JWT authentication implemented

✓ Refresh tokens implemented

✓ Role-based authorization works

✓ Password hashing enabled

✓ Login history recorded

✓ Audit logs generated

✓ Node authentication supported

✓ Account lockout works

✓ Password reset works

✓ REST responses follow common schema

✓ Security headers enabled

✓ Rate limiting enabled

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

- JWT authentication must be implemented using secure signing algorithms (HS256 or RS256).
- Passwords must be hashed using bcrypt (or Argon2 if preferred).
- Refresh tokens must be revocable.
- Every authentication-related operation must create an audit log entry.
- Voting nodes authenticate using a unique node ID and secret instead of username/password.
- All protected endpoints require a valid Bearer token.
- Authentication middleware must be reusable across all API modules.
- Responses must always follow the standardized JSON response format defined in this specification.

---

End of Part 4C-1

# Election Management Platform SRS
# Part 4C-2 – REST API Specification – Election, Candidate & Position APIs

Version: 1.0

---

# 1. Overview

This document specifies the REST APIs responsible for managing:

- Elections
- Positions
- Candidates
- Candidate Images
- House Configuration
- Election Publishing

These APIs are used **only by the Website Administration Portal**.

The desktop voting application **never** creates or edits election data.

It only downloads published configurations.

---

# 2. Base URL

Development

```
http://localhost:8000/api/v1
```

Production

```
https://your-domain.com/api/v1
```

All endpoints require JWT authentication unless otherwise stated.

---

# 3. Permission Matrix

| Endpoint | Super Admin | Admin | Viewer | Voting Node |
|------------|-------------|--------|---------|--------------|
| View Elections | ✓ | ✓ | ✓ | ✗ |
| Create Election | ✓ | ✓ | ✗ | ✗ |
| Edit Election | ✓ | ✓ | ✗ | ✗ |
| Publish Election | ✓ | ✓ | ✗ | ✗ |
| View Candidates | ✓ | ✓ | ✓ | Download Only |
| Create Candidate | ✓ | ✓ | ✗ | ✗ |
| Upload Image | ✓ | ✓ | ✗ | ✗ |
| View Positions | ✓ | ✓ | ✓ | Download Only |
| Create Position | ✓ | ✓ | ✗ | ✗ |

---

# 4. GET /elections

Purpose

Returns all elections.

Supports

- Pagination
- Search
- Sorting
- Status Filter

Response

```json
[
  {
    "id":"UUID",
    "name":"Annual Election 2027",
    "version":3,
    "status":"Published"
  }
]
```

---

# 5. GET /elections/{id}

Returns complete election details.

Includes

- Election Info
- Positions
- Candidates
- House Configuration
- Version

---

# 6. POST /elections

Purpose

Create new election.

Request

```json
{
  "name":"Annual Election 2027",
  "academic_year":"2027-2028",
  "description":"Student Council Election",
  "start_time":"2027-08-15T09:00:00",
  "end_time":"2027-08-15T16:00:00"
}
```

Response

```json
{
  "success":true,
  "election_id":"UUID"
}
```

---

# 7. PUT /elections/{id}

Update election.

Editable

- Name
- Description
- Dates
- Logo
- Theme

Cannot edit while LIVE.

---

# 8. DELETE /elections/{id}

Soft delete election.

Blocked if

- Published
- Live
- Completed

Audit log required.

---

# 9. POST /elections/{id}/publish

Purpose

Publish election.

Server performs

✓ Validation

✓ Candidate Check

✓ Position Check

✓ Image Check

✓ House Validation

✓ Generate Configuration Package

✓ Increment Version

Response

```json
{
 "success":true,
 "version":5
}
```

---

# 10. POST /elections/{id}/start

Starts voting.

Status

Published

↓

Live

---

# 11. POST /elections/{id}/end

Ends voting.

Status

Live

↓

Completed

Reports become available.

---

# 12. POST /elections/{id}/clear-results

Administrator Password Required.

Request

```json
{
 "password":"********",
 "confirmation":"CLEAR"
}
```

Deletes

Votes only.

Does NOT delete

Candidates

Positions

Images

Configuration

---

# 13. GET /positions

Returns all positions.

Supports

Election Filter

House Filter

Search

Example

```json
[
 {
   "id":"UUID",
   "name":"School Pupil Leader",
   "winner_count":1
 }
]
```

---

# 14. POST /positions

Create Position.

Request

```json
{
 "name":"Sports Captain",
 "election_type":"Regular",
 "winner_count":1,
 "display_order":4
}
```

---

# 15. PUT /positions/{id}

Update Position.

Editable

- Name
- Winner Count
- Display Order

Cannot edit while LIVE.

---

# 16. DELETE /positions/{id}

Delete Position.

Blocked if

Candidates exist.

---

# 17. GET /positions/{id}/candidates

Returns every candidate assigned to that position.

---

# 18. GET /candidates

Supports

Election

House

Position

Status

Search

Pagination

Response

```json
[
 {
   "id":"UUID",
   "name":"John Doe",
   "position":"School Pupil Leader",
   "status":"Active"
 }
]
```

---

# 19. GET /candidates/{id}

Returns

Full Candidate Profile.

Includes

Photo

Election

House

Position

Display Order

---

# 20. POST /candidates

Create Candidate.

Request

```json
{
 "candidate_name":"John Doe",
 "position_id":"UUID",
 "house_id":null,
 "display_order":1
}
```

House ID required only for House Election.

---

# 21. PUT /candidates/{id}

Update

- Name
- Position
- House
- Display Order
- Status

---

# 22. DELETE /candidates/{id}

Soft Delete.

Blocked if

Election LIVE.

---

# 23. POST /candidates/{id}/image

Upload Candidate Image.

Multipart Form Data

Returns

```json
{
 "image_id":"UUID"
}
```

---

# 24. PUT /candidates/{id}/image

Replace existing image.

Original retained until Publish.

---

# 25. GET /images/{id}

Returns processed image.

Supports

Thumbnail

Original

Preview

---

# 26. POST /images/{id}/crop

Request

```json
{
 "x":120,
 "y":80,
 "width":400,
 "height":500
}
```

---

# 27. POST /images/{id}/rotate

Request

```json
{
 "angle":90
}
```

---

# 28. POST /images/{id}/zoom

Request

```json
{
 "scale":1.4
}
```

---

# 29. POST /images/{id}/reset

Restores original image.

---

# 30. GET /houses

Returns

```json
[
 "Pallava",
 "Pandya",
 "Chera",
 "Chola"
]
```

---

# 31. PUT /houses/configuration

Configure

- Leadership Positions
- Display Order

Example

```json
{
 "positions":[
   "House Captain",
   "Vice Captain",
   "Sports Captain"
 ]
}
```

Automatically applies to all four houses.

---

# 32. GET /elections/{id}/configuration

Returns published configuration metadata.

Includes

Version

Checksum

Package Size

Publish Date

---

# 33. GET /configuration/download

Authenticated endpoint for desktop applications.

Downloads

- Candidates
- Images
- Positions
- House Configuration
- Theme
- Election Metadata

Returns ZIP package.

---

# 34. Validation Rules

Election

Must contain at least one position.

Position

Must contain candidates.

Candidate

Requires image.

House Candidate

Requires house assignment.

Duplicate candidate names within the same position are prohibited.

---

# 35. Standard Success Response

```json
{
 "success":true,
 "message":"Candidate created successfully",
 "data":{}
}
```

---

# 36. Standard Error Response

```json
{
 "success":false,
 "message":"Validation Failed",
 "errors":[]
}
```

---

# 37. HTTP Status Codes

200 Success

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Error

---

# 38. Audit Logging

Every API generates audit entries.

Examples

Election Created

Election Published

Candidate Created

Candidate Updated

Image Uploaded

Position Deleted

---

# 39. Performance Requirements

Create Candidate

<500 ms

Upload Image

<2 s

Publish Election

<5 s

Download Configuration

<10 s

Search

<100 ms

---

# 40. Acceptance Criteria

The Election, Candidate & Position APIs are complete when:

✓ Elections can be created and managed.

✓ Publishing generates versioned configurations.

✓ Positions support configurable winner counts.

✓ House configuration is centralized.

✓ Candidate CRUD is complete.

✓ Image upload, crop, rotate, zoom and reset APIs function correctly.

✓ Desktop applications can securely download published configurations.

✓ Validation prevents invalid election data.

✓ Audit logs record every modification.

✓ All endpoints follow the standardized REST response format.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

- Only the website may modify elections, candidates and positions.
- Desktop voting applications are strictly read-only for configuration data.
- Publishing is the only mechanism that distributes election changes.
- Candidate image editing APIs must preserve the original image until publication.
- House positions are defined once and automatically apply to Pallava, Pandya, Chera and Chola.
- Every modifying endpoint must create an audit log entry.
- All APIs must be fully documented using FastAPI's OpenAPI/Swagger interface.

---

End of Part 4C-2

# Election Management Platform SRS
# Part 4C-3 – REST API Specification – Node, Synchronization, Reports & Settings APIs

Version: 1.0

---

# 1. Overview

This document defines all REST APIs used by:

- Desktop Voting Nodes
- Synchronization Engine
- Live Website
- Reports Module
- Node Monitoring
- Website Settings

These APIs allow secure communication between every voting node and the central website.

Only authenticated nodes may synchronize votes.

---

# 2. API Categories

The APIs are divided into five major groups.

```
Node APIs

Synchronization APIs

Report APIs

Settings APIs

Health APIs
```

---

# 3. Permission Matrix

| API | Super Admin | Admin | Viewer | Voting Node |
|------|-------------|--------|---------|-------------|
| Node Heartbeat | ✗ | ✗ | ✗ | ✓ |
| Upload Votes | ✗ | ✗ | ✗ | ✓ |
| Download Configuration | ✗ | ✗ | ✗ | ✓ |
| View Reports | ✓ | ✓ | ✓ | ✗ |
| Export Reports | ✓ | ✓ | ✓ | ✗ |
| Website Settings | ✓ | ✓ | ✗ | ✗ |
| Node Monitor | ✓ | ✓ | ✓ | ✗ |

---

# 4. POST /nodes/heartbeat

Purpose

Desktop applications send heartbeat every 10 seconds.

Request

```json
{
    "node_id":"UUID",
    "app_version":"2.0.0",
    "config_version":5,
    "queue_size":2,
    "last_vote_time":"2027-07-20T10:30:12"
}
```

Response

```json
{
    "success":true,
    "server_time":"2027-07-20T10:30:15",
    "status":"Healthy"
}
```

---

# 5. GET /nodes

Returns every registered voting node.

Response

```json
[
    {
        "node_name":"Regular-01",
        "status":"Online",
        "queue_size":0,
        "last_seen":"10 seconds ago"
    }
]
```

Supports

- Search
- Pagination
- Filter by Election Type
- Filter by House

---

# 6. GET /nodes/{id}

Returns

- Node Information
- Current Status
- Assigned House
- Election Type
- Queue Size
- Sync Status
- App Version
- Configuration Version

---

# 7. PUT /nodes/{id}

Administrator may update

- Node Name
- Election Type
- Assigned House
- Status

Cannot edit while election is LIVE.

---

# 8. POST /sync/votes

Purpose

Uploads vote batches from voting node.

Request

```json
{
    "node_id":"UUID",
    "votes":[
        {
            "vote_uuid":"UUID",
            "candidate_id":"UUID",
            "position_id":"UUID",
            "timestamp":"2027-07-20T10:30:45"
        }
    ]
}
```

---

# 9. Vote Validation

Server verifies

✓ JWT

✓ Node Exists

✓ Configuration Version

✓ Candidate Exists

✓ Position Exists

✓ Vote UUID Unique

Only valid votes are accepted.

---

# 10. Synchronization Response

```json
{
    "success":true,
    "accepted":18,
    "duplicates":0,
    "failed":0
}
```

Desktop removes only accepted votes from local queue.

---

# 11. POST /sync/status

Returns synchronization status.

```json
{
    "pending":3,
    "uploaded":150,
    "failed":0
}
```

---

# 12. GET /sync/version

Desktop checks for updates.

Response

```json
{
    "latest_version":7,
    "download_required":true
}
```

---

# 13. GET /configuration/package

Downloads latest published election package.

Contains

```
Election.json

Candidates.json

Positions.json

Houses.json

Theme.json

Images/

Checksum
```

ZIP archive.

---

# 14. POST /configuration/checksum

Desktop verifies package integrity.

Request

```json
{
    "checksum":"SHA256_HASH"
}
```

Response

```json
{
    "valid":true
}
```

---

# 15. GET /reports

Returns available reports.

Supports

- Election Filter
- Date Filter
- Report Type Filter

---

# 16. POST /reports/generate

Generates report.

Request

```json
{
    "election_id":"UUID",
    "format":"Excel"
}
```

Formats

```
Excel

CSV

PDF
```

---

# 17. GET /reports/{id}/download

Downloads generated report.

Supported Formats

- XLSX
- CSV
- PDF

Response

Binary File

---

# 18. Report Contents

Every report includes

✓ Election

✓ Position

✓ House

✓ Candidate

✓ Vote Count

✓ Percentage

✓ Winner

✓ Timestamp

---

# 19. GET /analytics/dashboard

Returns

```json
{
    "total_votes":1250,
    "active_nodes":16,
    "online_nodes":15,
    "completed_sync":99.8
}
```

---

# 20. GET /analytics/regular

Returns live statistics for

Regular Election.

Includes

- Candidate Votes
- Rankings
- Percentages

---

# 21. GET /analytics/houses

Returns

```
Pallava

Pandya

Chera

Chola
```

Each contains

- Votes
- Rankings
- Charts
- Percentages

---

# 22. GET /settings

Returns website settings.

Includes

- School Name
- Theme
- Logo
- Election Logo
- Colors
- Maintenance Mode

Administrator only.

---

# 23. PUT /settings

Updates website settings.

Editable

- School Name
- Theme
- Logos
- Colors
- Timezone

Audit log mandatory.

---

# 24. GET /settings/database

Returns current MySQL configuration.

Sensitive fields masked.

Example

```json
{
    "host":"localhost",
    "database":"ElectionDB",
    "username":"admin",
    "password":"********"
}
```

---

# 25. PUT /settings/database

Update MySQL connection.

Request

```json
{
    "host":"localhost",
    "port":3306,
    "database":"ElectionDB",
    "username":"root",
    "password":"password"
}
```

Server immediately tests connection.

---

# 26. POST /settings/database/test

Returns

```json
{
    "success":true,
    "latency":"15ms"
}
```

---

# 27. GET /health

Public endpoint.

Returns

```json
{
    "status":"Healthy",
    "database":"Connected",
    "uptime":"4 Days"
}
```

---

# 28. GET /health/database

Checks

MySQL

Returns

```json
{
    "connected":true,
    "latency":"12ms"
}
```

---

# 29. GET /health/websocket

Returns

```
Connected Clients

Active Channels

Broadcast Queue
```

---

# 30. GET /health/node/{id}

Returns

- Last Heartbeat
- Queue Size
- Sync Status
- Last Vote
- App Version

---

# 31. Standard Success Response

```json
{
    "success":true,
    "message":"Operation completed successfully",
    "data":{}
}
```

---

# 32. Standard Error Response

```json
{
    "success":false,
    "message":"Validation Failed",
    "errors":[]
}
```

---

# 33. HTTP Status Codes

```
200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

429 Too Many Requests

500 Internal Server Error
```

---

# 34. Rate Limits

Heartbeat

Unlimited (Authenticated Nodes)

Vote Upload

Unlimited (Authenticated Nodes)

Report Generation

20/hour

Database Test

20/hour

Settings Update

10/hour

---

# 35. Audit Logging

The following actions must be recorded.

✓ Vote Synchronization

✓ Configuration Download

✓ Database Update

✓ Report Download

✓ Report Generation

✓ Node Registration

✓ Node Assignment

✓ Website Settings Update

✓ Theme Change

✓ Election Result Clearance

---

# 36. Security Requirements

All node APIs require

- JWT Authentication
- Node Secret Verification
- HTTPS Only
- TLS 1.2+

Vote uploads must be idempotent.

Duplicate vote submissions must never create duplicate records.

---

# 37. Performance Requirements

Heartbeat Response

<100 ms

Vote Upload

<500 ms

Configuration Download

<5 seconds

Report Generation

<5 seconds

Dashboard Analytics

<300 ms

Health Check

<100 ms

---

# 38. Acceptance Criteria

The Node, Synchronization, Reports & Settings APIs are complete when:

✓ Nodes automatically send heartbeats every 10 seconds.

✓ Offline vote synchronization is reliable and idempotent.

✓ Published election configurations can be securely downloaded.

✓ Reports can be generated in Excel, CSV and PDF formats.

✓ Dashboard analytics return live election statistics.

✓ Website settings, including MySQL configuration, can be viewed, tested and updated.

✓ Health endpoints provide accurate diagnostics.

✓ Every administrative and synchronization event is recorded in the audit log.

✓ All APIs follow the standardized response format.

✓ Security, authentication and authorization requirements are enforced consistently.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

- Vote synchronization must support batch uploads to minimize network overhead.
- The desktop application shall continue operating offline and retry synchronization automatically until successful.
- Every synchronization request must be idempotent using `vote_uuid`.
- Configuration packages must include a version number and SHA-256 checksum for integrity verification.
- Report generation should execute asynchronously for large datasets.
- Health APIs should be lightweight and suitable for monitoring tools.
- All APIs must be documented automatically using FastAPI OpenAPI (Swagger UI).

---

# REST API Summary

The backend REST API is organized into the following modules:

### Authentication & User APIs
- Login
- Logout
- JWT Refresh
- User Management
- Role Management

### Election Management APIs
- Elections
- Positions
- Candidates
- Image Processing
- Publish Workflow

### Node & Synchronization APIs
- Heartbeats
- Vote Upload
- Configuration Download
- Queue Status
- Health Monitoring

### Reports & Analytics APIs
- Report Generation
- Report Download
- Live Analytics
- Dashboard Statistics

### Settings APIs
- Website Settings
- Theme Management
- Database Configuration
- System Health

This completes the full REST API specification for the Election Management Platform and provides a complete contract between the NiceGUI website, FastAPI backend, desktop voting applications, and future mobile viewers.

---

End of Part 4C-3

# Election Management Platform SRS
# Part 4C-3 – REST API Specification – Node, Synchronization, Reports & Settings APIs

Version: 1.0

---

# 1. Overview

This document defines all REST APIs used by:

- Desktop Voting Nodes
- Synchronization Engine
- Live Website
- Reports Module
- Node Monitoring
- Website Settings

These APIs allow secure communication between every voting node and the central website.

Only authenticated nodes may synchronize votes.

---

# 2. API Categories

The APIs are divided into five major groups.

```
Node APIs

Synchronization APIs

Report APIs

Settings APIs

Health APIs
```

---

# 3. Permission Matrix

| API | Super Admin | Admin | Viewer | Voting Node |
|------|-------------|--------|---------|-------------|
| Node Heartbeat | ✗ | ✗ | ✗ | ✓ |
| Upload Votes | ✗ | ✗ | ✗ | ✓ |
| Download Configuration | ✗ | ✗ | ✗ | ✓ |
| View Reports | ✓ | ✓ | ✓ | ✗ |
| Export Reports | ✓ | ✓ | ✓ | ✗ |
| Website Settings | ✓ | ✓ | ✗ | ✗ |
| Node Monitor | ✓ | ✓ | ✓ | ✗ |

---

# 4. POST /nodes/heartbeat

Purpose

Desktop applications send heartbeat every 10 seconds.

Request

```json
{
    "node_id":"UUID",
    "app_version":"2.0.0",
    "config_version":5,
    "queue_size":2,
    "last_vote_time":"2027-07-20T10:30:12"
}
```

Response

```json
{
    "success":true,
    "server_time":"2027-07-20T10:30:15",
    "status":"Healthy"
}
```

---

# 5. GET /nodes

Returns every registered voting node.

Response

```json
[
    {
        "node_name":"Regular-01",
        "status":"Online",
        "queue_size":0,
        "last_seen":"10 seconds ago"
    }
]
```

Supports

- Search
- Pagination
- Filter by Election Type
- Filter by House

---

# 6. GET /nodes/{id}

Returns

- Node Information
- Current Status
- Assigned House
- Election Type
- Queue Size
- Sync Status
- App Version
- Configuration Version

---

# 7. PUT /nodes/{id}

Administrator may update

- Node Name
- Election Type
- Assigned House
- Status

Cannot edit while election is LIVE.

---

# 8. POST /sync/votes

Purpose

Uploads vote batches from voting node.

Request

```json
{
    "node_id":"UUID",
    "votes":[
        {
            "vote_uuid":"UUID",
            "candidate_id":"UUID",
            "position_id":"UUID",
            "timestamp":"2027-07-20T10:30:45"
        }
    ]
}
```

---

# 9. Vote Validation

Server verifies

✓ JWT

✓ Node Exists

✓ Configuration Version

✓ Candidate Exists

✓ Position Exists

✓ Vote UUID Unique

Only valid votes are accepted.

---

# 10. Synchronization Response

```json
{
    "success":true,
    "accepted":18,
    "duplicates":0,
    "failed":0
}
```

Desktop removes only accepted votes from local queue.

---

# 11. POST /sync/status

Returns synchronization status.

```json
{
    "pending":3,
    "uploaded":150,
    "failed":0
}
```

---

# 12. GET /sync/version

Desktop checks for updates.

Response

```json
{
    "latest_version":7,
    "download_required":true
}
```

---

# 13. GET /configuration/package

Downloads latest published election package.

Contains

```
Election.json

Candidates.json

Positions.json

Houses.json

Theme.json

Images/

Checksum
```

ZIP archive.

---

# 14. POST /configuration/checksum

Desktop verifies package integrity.

Request

```json
{
    "checksum":"SHA256_HASH"
}
```

Response

```json
{
    "valid":true
}
```

---

# 15. GET /reports

Returns available reports.

Supports

- Election Filter
- Date Filter
- Report Type Filter

---

# 16. POST /reports/generate

Generates report.

Request

```json
{
    "election_id":"UUID",
    "format":"Excel"
}
```

Formats

```
Excel

CSV

PDF
```

---

# 17. GET /reports/{id}/download

Downloads generated report.

Supported Formats

- XLSX
- CSV
- PDF

Response

Binary File

---

# 18. Report Contents

Every report includes

✓ Election

✓ Position

✓ House

✓ Candidate

✓ Vote Count

✓ Percentage

✓ Winner

✓ Timestamp

---

# 19. GET /analytics/dashboard

Returns

```json
{
    "total_votes":1250,
    "active_nodes":16,
    "online_nodes":15,
    "completed_sync":99.8
}
```

---

# 20. GET /analytics/regular

Returns live statistics for

Regular Election.

Includes

- Candidate Votes
- Rankings
- Percentages

---

# 21. GET /analytics/houses

Returns

```
Pallava

Pandya

Chera

Chola
```

Each contains

- Votes
- Rankings
- Charts
- Percentages

---

# 22. GET /settings

Returns website settings.

Includes

- School Name
- Theme
- Logo
- Election Logo
- Colors
- Maintenance Mode

Administrator only.

---

# 23. PUT /settings

Updates website settings.

Editable

- School Name
- Theme
- Logos
- Colors
- Timezone

Audit log mandatory.

---

# 24. GET /settings/database

Returns current MySQL configuration.

Sensitive fields masked.

Example

```json
{
    "host":"localhost",
    "database":"ElectionDB",
    "username":"admin",
    "password":"********"
}
```

---

# 25. PUT /settings/database

Update MySQL connection.

Request

```json
{
    "host":"localhost",
    "port":3306,
    "database":"ElectionDB",
    "username":"root",
    "password":"password"
}
```

Server immediately tests connection.

---

# 26. POST /settings/database/test

Returns

```json
{
    "success":true,
    "latency":"15ms"
}
```

---

# 27. GET /health

Public endpoint.

Returns

```json
{
    "status":"Healthy",
    "database":"Connected",
    "uptime":"4 Days"
}
```

---

# 28. GET /health/database

Checks

MySQL

Returns

```json
{
    "connected":true,
    "latency":"12ms"
}
```

---

# 29. GET /health/websocket

Returns

```
Connected Clients

Active Channels

Broadcast Queue
```

---

# 30. GET /health/node/{id}

Returns

- Last Heartbeat
- Queue Size
- Sync Status
- Last Vote
- App Version

---

# 31. Standard Success Response

```json
{
    "success":true,
    "message":"Operation completed successfully",
    "data":{}
}
```

---

# 32. Standard Error Response

```json
{
    "success":false,
    "message":"Validation Failed",
    "errors":[]
}
```

---

# 33. HTTP Status Codes

```
200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

429 Too Many Requests

500 Internal Server Error
```

---

# 34. Rate Limits

Heartbeat

Unlimited (Authenticated Nodes)

Vote Upload

Unlimited (Authenticated Nodes)

Report Generation

20/hour

Database Test

20/hour

Settings Update

10/hour

---

# 35. Audit Logging

The following actions must be recorded.

✓ Vote Synchronization

✓ Configuration Download

✓ Database Update

✓ Report Download

✓ Report Generation

✓ Node Registration

✓ Node Assignment

✓ Website Settings Update

✓ Theme Change

✓ Election Result Clearance

---

# 36. Security Requirements

All node APIs require

- JWT Authentication
- Node Secret Verification
- HTTPS Only
- TLS 1.2+

Vote uploads must be idempotent.

Duplicate vote submissions must never create duplicate records.

---

# 37. Performance Requirements

Heartbeat Response

<100 ms

Vote Upload

<500 ms

Configuration Download

<5 seconds

Report Generation

<5 seconds

Dashboard Analytics

<300 ms

Health Check

<100 ms

---

# 38. Acceptance Criteria

The Node, Synchronization, Reports & Settings APIs are complete when:

✓ Nodes automatically send heartbeats every 10 seconds.

✓ Offline vote synchronization is reliable and idempotent.

✓ Published election configurations can be securely downloaded.

✓ Reports can be generated in Excel, CSV and PDF formats.

✓ Dashboard analytics return live election statistics.

✓ Website settings, including MySQL configuration, can be viewed, tested and updated.

✓ Health endpoints provide accurate diagnostics.

✓ Every administrative and synchronization event is recorded in the audit log.

✓ All APIs follow the standardized response format.

✓ Security, authentication and authorization requirements are enforced consistently.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

- Vote synchronization must support batch uploads to minimize network overhead.
- The desktop application shall continue operating offline and retry synchronization automatically until successful.
- Every synchronization request must be idempotent using `vote_uuid`.
- Configuration packages must include a version number and SHA-256 checksum for integrity verification.
- Report generation should execute asynchronously for large datasets.
- Health APIs should be lightweight and suitable for monitoring tools.
- All APIs must be documented automatically using FastAPI OpenAPI (Swagger UI).

---

# REST API Summary

The backend REST API is organized into the following modules:

### Authentication & User APIs
- Login
- Logout
- JWT Refresh
- User Management
- Role Management

### Election Management APIs
- Elections
- Positions
- Candidates
- Image Processing
- Publish Workflow

### Node & Synchronization APIs
- Heartbeats
- Vote Upload
- Configuration Download
- Queue Status
- Health Monitoring

### Reports & Analytics APIs
- Report Generation
- Report Download
- Live Analytics
- Dashboard Statistics

### Settings APIs
- Website Settings
- Theme Management
- Database Configuration
- System Health

This completes the full REST API specification for the Election Management Platform and provides a complete contract between the NiceGUI website, FastAPI backend, desktop voting applications, and future mobile viewers.

---

End of Part 4C-3