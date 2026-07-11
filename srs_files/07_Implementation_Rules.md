# Election Management Platform SRS
# 07_Implementation_Rules.md

Version: 1.0

---

# 1. Purpose

This document defines the mandatory implementation rules that every
module of the Election Management Platform must follow.

These rules override implementation preferences and ensure that the
entire project remains maintainable, scalable, production-ready and
consistent.

Any generated code that violates these rules should be considered
incorrect.

---

# 2. Project Philosophy

The objective is **not** simply to build a voting application.

The objective is to build a **professional Election Management Platform**
that can reliably conduct elections with live monitoring, fault
tolerance, offline capability, and centralized administration.

Every implementation decision should prioritize:

- Reliability
- Maintainability
- Performance
- Security
- User Experience
- Expandability

---

# 3. Golden Rules

The following rules must never be broken.

✓ Never remove existing functionality.

✓ Never simplify existing workflows.

✓ Never redesign the desktop UI unless required for responsiveness.

✓ Never remove existing image editing features.

✓ Never remove existing candidate management workflow.

✓ Never remove existing election workflow.

✓ Preserve all existing behavior from the original project.

---

# 4. Existing Application Preservation

The uploaded desktop application is the reference implementation.

Cursor shall:

- Preserve every existing feature.
- Preserve every existing workflow.
- Preserve the user experience.
- Preserve keyboard shortcuts where possible.
- Preserve all validation logic.
- Preserve all existing image processing behavior.

The architecture may change.

The behavior may not.

---

# 5. Desktop Application Rules

Desktop application responsibilities:

✓ Download configuration

✓ Cache configuration

✓ Display candidates

✓ Record votes

✓ Synchronize votes

✓ Local configuration

✓ Health monitoring

Desktop application must **never**

- Create candidates
- Delete candidates
- Modify elections
- Edit positions
- Publish elections

---

# 6. Website Rules

The website is the master system.

Only the website may

- Create elections
- Publish elections
- Edit elections
- Manage candidates
- Manage positions
- Configure houses
- Configure nodes
- Configure themes
- Configure reports

Desktop applications are read-only.

---

# 7. Backend Rules

Backend responsibilities

✓ Authentication

✓ Synchronization

✓ Validation

✓ Database

✓ WebSocket

✓ Reports

Backend must contain **no UI code**.

---

# 8. Technology Stack Rules

Desktop

Python

CustomTkinter

Pillow

PyInstaller

Website

NiceGUI

Backend

FastAPI

Database

MySQL

ORM

SQLAlchemy

Validation

Pydantic

Authentication

JWT

Synchronization

FakeRedis + SQLite Queue

No technology substitutions without approval.

---

# 9. FakeRedis Rules

FakeRedis shall only be used

- As an in-memory synchronization queue
- For retry management
- For background processing

FakeRedis shall never store permanent data.

---

# 10. Persistent Storage Rules

Permanent data must always be stored in

SQLite (preferred)

or

Configured Local MySQL

Never rely solely on RAM.

---

# 11. MySQL Rules

Website database

↓

Primary Database

Desktop database

↓

Local Cache

They are independent.

Changing local MySQL settings must never affect the website database.

---

# 12. Synchronization Rules

Votes must always follow

Save

↓

Queue

↓

Upload

↓

ACK

↓

Delete Queue

Never delete queued votes before acknowledgment.

---

# 13. Offline Rules

Voting must continue if

- Internet fails
- Website unavailable
- Cloudflare Tunnel unavailable
- Backend restarting

No vote shall be lost.

---

# 14. UI Rules

Desktop UI must

✓ Auto-scale

✓ Support DPI

✓ Resize automatically

✓ Maintain spacing

✓ Support older Windows versions

Website UI must

✓ Be responsive

✓ Support desktop

✓ Support tablet

✓ Support mobile

---

# 15. Window Management Rules

Every desktop dialog shall

- Open centered
- Stay above parent
- Be modal where appropriate
- Never open behind another window
- Restore focus correctly

---

# 16. Image Processing Rules

The image editor must preserve

✓ Crop

✓ Rotate

✓ Zoom

✓ Preview

✓ Resize

✓ Save

Image quality must not degrade unnecessarily.

---

# 17. Candidate Management Rules

Candidate management must include

- Add
- Edit
- Delete
- Search
- Sort
- Photo Management
- Preview
- Validation

The website UI should closely match the original desktop experience.

---

# 18. Election Rules

Support two simultaneous election types

Regular Election

House Election

Both must operate independently.

Publishing one must not overwrite the other.

---

# 19. House Election Rules

Administrator defines

- Houses
- Positions
- Candidates
- Node Assignment

Teachers never select the house.

Students never log in.

---

# 20. Node Rules

Every node must have

Node UUID

Node Secret

Election Type

Assigned House

Configuration Version

These values remain persistent.

---

# 21. Authentication Rules

Administrators

↓

JWT Login

Desktop Nodes

↓

Node UUID + Node Secret

Teachers never authenticate.

---

# 22. Security Rules

Passwords

↓

Hash using bcrypt/Argon2

Never store plaintext passwords.

Use HTTPS everywhere.

Validate every API request.

---

# 23. API Rules

REST API responsibilities

Authentication

CRUD

Synchronization

Reports

Configuration

WebSockets shall only be used for

- Live Results
- Node Monitoring
- Dashboard Updates

---

# 24. Database Rules

Never perform direct SQL inside UI code.

Always use SQLAlchemy models.

Every table must have

- Primary Key
- Created At
- Updated At

Use foreign keys where applicable.

---

# 25. Error Handling Rules

Every exception must

- Be logged
- Display user-friendly messages
- Never crash the application
- Preserve unsaved votes

---

# 26. Logging Rules

Log categories

Application

Synchronization

Database

Authentication

Configuration

Recovery

Errors

Audit

Logs must rotate automatically.

---

# 27. Coding Style Rules

Follow

PEP-8

Type hints

Docstrings

Meaningful variable names

No magic numbers

No duplicated logic

No unused code

---

# 28. Folder Rules

Every module shall have a single responsibility.

Example

```
backend/

desktop/

website/

database/

services/

api/

models/

schemas/

utils/

assets/

docs/
```

Avoid circular imports.

---

# 29. Performance Rules

Desktop startup

<10 sec

Vote processing

<10 ms

Heartbeat

<100 ms

Dashboard update

<250 ms

Configuration download

<5 sec

Synchronization

Background only

---

# 30. Reporting Rules

Reports must export

Excel

CSV

PDF

Reports include

Votes

Candidates

Houses

Positions

Percentages

Winners

Timestamps

---

# 31. Deployment Rules

Default deployment

Cloudflare Tunnel

Future support

Custom Domain

Docker

Reverse Proxy

HTTPS mandatory.

---

# 32. Testing Rules

Each module should include

- Unit Tests
- Integration Tests
- API Tests
- Synchronization Tests
- UI Tests (where practical)
- Recovery Tests

Critical workflows must be tested before release.

---

# 33. Documentation Rules

Every major module must include

- Purpose
- Responsibilities
- Dependencies
- Public Interfaces
- Error Handling
- Configuration Options

Keep documentation synchronized with implementation.

---

# 34. Cursor Implementation Rules

Cursor shall:

✓ Analyze before coding.

✓ Preserve existing functionality.

✓ Build module-by-module.

✓ Wait for approval after documentation phase.

✓ Avoid introducing breaking changes.

✓ Keep code production-ready.

✓ Maintain consistency with this SRS.

---

# 35. Future Expansion Rules

Architecture shall allow future addition of

- Multiple schools
- Multiple election sessions
- Multiple administrators
- Additional election types
- Cloud deployment
- Docker
- Kubernetes
- PostgreSQL
- Redis Server
- Push notifications

without major redesign.

---

# 36. Code Quality Checklist

Every completed module must satisfy:

✓ PEP-8 compliant

✓ Type hinted

✓ Documented

✓ Exception handling implemented

✓ Logging implemented

✓ No duplicated code

✓ Modular

✓ Easily testable

✓ Cross-platform

✓ Responsive

---

# 37. Things That Must Never Change

The following are considered project requirements:

- Preserve the original desktop voting experience.
- Preserve all candidate image editing features.
- Website is always the master control center.
- Desktop nodes remain read-only for election management.
- Teachers are the operators of voting machines.
- Students never authenticate.
- Mobile devices remain view-only.
- House assignment is configured only by the administrator.
- Votes are always stored locally before synchronization.
- Synchronization must continue automatically after failures.

---

# 38. Development Order

Implementation shall proceed in this order:

1. Existing Project Analysis
2. Database Models
3. Backend APIs
4. Authentication
5. Website Framework
6. Candidate Manager
7. Image Editor
8. Position Manager
9. Election Management
10. Configuration Download
11. Desktop Refactoring
12. Synchronization Engine
13. Heartbeat & Node Monitoring
14. Live Results
15. Reports
16. Deployment
17. Testing
18. Production Validation

Each phase must be completed and verified before moving to the next.

---

# 39. Final Acceptance Criteria

The project is considered complete only when:

✓ All existing desktop functionality is preserved.

✓ The website completely replaces desktop administration.

✓ Desktop nodes can operate offline.

✓ Live synchronization is reliable.

✓ No vote loss occurs.

✓ Reports export correctly.

✓ Mobile users can securely view live results.

✓ Node health is monitored in real time.

✓ Configuration management is centralized.

✓ The system is production-ready and deployable.

---

# 40. Master Principle

> **Reliability takes precedence over convenience.**

When multiple implementation choices are possible, always choose the solution that provides:

- Greater reliability
- Better maintainability
- Stronger security
- Easier scalability
- Cleaner architecture
- Better user experience

Even if it requires more development effort.

---

# End of Document

End of 07_Implementation_Rules.md