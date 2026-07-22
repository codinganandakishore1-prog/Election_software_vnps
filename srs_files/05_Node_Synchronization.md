# Election Management Platform SRS
# Part 05A – Node Registration & Configuration

Version: 1.0

---

# 1. Overview

This document defines how every desktop voting application (Node)
registers, authenticates, downloads election configurations, stores
configuration locally, and prepares itself before voting begins.

The objective is to ensure that every node is correctly configured
before voting starts while allowing the election to continue even if the
network becomes unavailable later.

---

# 2. Scope

This module is responsible for:

- Node Registration
- Node Authentication
- Configuration Version Checking
- Election Package Download
- Local Storage
- Configuration Validation
- House Assignment
- Node Locking
- Local Database Configuration

This module **does not** handle vote synchronization.

That is covered in **05B – Vote Synchronization Engine**.

---

# 3. Registration Philosophy

The website is the **master system**.

Desktop nodes are **clients**.

All election data originates from the website.

The desktop app never creates elections or candidates.

---

# 4. Node Types

Two node types exist.

### Regular Election Node

Used for School Election.

Example

```
Regular-01
Regular-02
...
Regular-08
```

House Assignment

```
NULL
```

---

### House Election Node

Used for House Elections.

Example

```
House-01
House-02
...
House-08
```

Each node is permanently assigned by the administrator.

Example

```
House-01

↓

Pallava

House-02

↓

Pallava

House-03

↓

Pandya

...
```

Teachers never select the house.

Students never see the house selection.

---

# 5. Node Identity

Each node contains a permanent identity.

```
Node UUID

Node Secret

Node Name

Election Type

Assigned House

Configuration Version
```

Example

```
Node UUID

3f60d...

Node Name

Regular-04

Election Type

Regular

House

NULL
```

---

# 6. Node Registration Flow

```
Administrator

↓

Website

↓

Create Node

↓

Assign House

↓

Generate Secret

↓

Save

↓

Desktop Downloads Configuration
```

Desktop applications are **never manually registered**.

---

# 7. Node Authentication

Desktop authenticates using

```
Node UUID

+

Node Secret
```

NOT

```
Username

Password
```

Authentication endpoint

```
POST

/auth/node-login
```

Returns

```
JWT Token
```

---

# 8. Configuration Version

Every published election receives

```
Version

1

2

3

4
```

Desktop stores

```
Current Version
```

Every startup

```
Website Version

>

Local Version ?

YES

↓

Download

NO

↓

Continue
```

---

# 9. Configuration Package

Downloaded package contains

```
Election.json

Candidates.json

Positions.json

Houses.json

Settings.json

Theme.json

Images/

Logo/

Checksum.sha256
```

Everything required for offline voting.

---

# 10. Configuration Download

Desktop checks

```
GET

/configuration/package
```

If newer version exists

↓

Download ZIP

↓

Extract

↓

Validate

↓

Install

---

# 11. Configuration Validation

Before installation

Desktop verifies

✓ Version

✓ SHA256 Checksum

✓ Image Count

✓ Candidate Count

✓ Position Count

✓ House Data

Only valid packages are installed.

---

# 12. Local Storage Structure

```
Desktop/

config/

election.json

positions.json

candidates.json

houses.json

settings.json

theme.json

checksum.sha256

images/

logos/

backgrounds/
```

Everything required for voting exists locally.

---

# 13. Local Database

Each desktop contains a local database.

Preferred

```
SQLite
```

Alternative

Existing local MySQL

Stores

- Configuration Version
- Vote Queue
- Settings
- Download History

This database is independent of the website database.

---

# 14. Local MySQL Configuration

The desktop application includes a Settings page where administrators may configure the local database connection.

Editable fields

```
Host

Port

Database Name

Username

Password
```

Buttons

```
Test Connection

Save Configuration

Reconnect
```

Changes take effect without restarting the application.

---

# 15. Website MySQL Configuration

The website maintains its own MySQL configuration.

Desktop configuration and website configuration are completely independent.

---

# 16. House Assignment

House assignment is configured **only** on the website.

Administrator selects

```
House-01

↓

Pallava
```

Configuration download stores

```
Assigned House

Pallava
```

Teachers never choose.

---

# 17. Election Type

Every node stores

```
Election Type

Regular

or

House
```

Desktop automatically opens the correct voting mode.

No manual selection required.

---

# 18. Published Configuration

Only

Published Elections

may be downloaded.

Draft elections remain invisible to nodes.

---

# 19. Read-Only Configuration

Desktop displays

Candidates

Positions

Images

Election Logo

Theme

House

But cannot edit them.

Editing is allowed only through the website.

---

# 20. Candidate Images

Images downloaded include

```
PNG

JPEG
```

Each image includes

```
Thumbnail

Processed Image

Original
```

Used by the desktop application.

---

# 21. Candidate Display

Desktop displays

Candidate Name

Photo

Position

House (if applicable)

Display Order

Exactly matching the website.

---

# 22. Theme Download

The package also includes

School Logo

Election Logo

Background Images

Theme Colors

Application Icons

Fonts (if required)

This ensures all nodes have identical appearance.

---

# 23. Configuration Lock

After download

Configuration becomes read-only.

Teachers cannot

Edit

Delete

Rename

Move Candidates

Everything remains locked.

---

# 24. Configuration Update

If administrator republishes

Version increases.

Desktop

```
Version 3

↓

Website Version 4

↓

Download Required
```

No automatic download during an active election.

Updates occur only before voting starts.

---

# 25. Installation Workflow

```
Download

↓

Checksum Validation

↓

Extract

↓

Replace Previous Configuration

↓

Update Version

↓

Restart UI

↓

Ready
```

---

# 26. Failed Download

If download fails

↓

Retain previous configuration.

Never leave the node in a partially updated state.

---

# 27. Corrupted Package

If checksum mismatch

↓

Reject Installation

↓

Display Error

↓

Retry Download

---

# 28. Configuration Backup

Before installation

Desktop creates

```
Backup/

Version3.zip
```

Rollback possible.

---

# 29. Startup Workflow

```
Launch App

↓

Read Local Settings

↓

Authenticate Node

↓

Check Version

↓

Download If Needed

↓

Load Configuration

↓

Initialize Local Database

↓

Ready For Voting
```

---

# 30. Security

Downloaded packages are

Authenticated

Versioned

Checksum Protected

Read Only

Node Specific

Only registered nodes may download.

---

# 31. Audit Logging

Website logs

Configuration Published

Node Download

Configuration Installed

Failed Validation

Checksum Failure

Node Authentication

---

# 32. Performance Targets

Version Check

<100 ms

Configuration Download

<5 seconds

Checksum Verification

<2 seconds

Configuration Installation

<3 seconds

Startup Time

<10 seconds

---

# 33. Error Handling

Network Failure

↓

Retry

Invalid JWT

↓

Reauthenticate

Corrupted Package

↓

Reject

Missing Images

↓

Abort Installation

Database Failure

↓

Display Configuration Error

---

# 34. Acceptance Criteria

The Node Registration & Configuration module is complete when:

✓ Nodes authenticate using Node ID and Secret.

✓ Every node has a unique UUID.

✓ Configuration packages are versioned.

✓ SHA-256 checksum validation is enforced.

✓ House assignments are downloaded automatically.

✓ Teachers are never asked to select a house.

✓ Desktop application supports both Regular and House Election modes automatically.

✓ Candidate data, images, themes and settings are downloaded successfully.

✓ Configuration remains read-only on the desktop.

✓ Local MySQL settings can be updated without restarting.

✓ Previous configuration is retained if download fails.

✓ Backups are created before every installation.

---

# 35. IMPORTANT IMPLEMENTATION REQUIREMENTS

- The website is the only authority for election configuration.
- Desktop applications must never modify downloaded configuration files.
- Configuration packages must be digitally verified using SHA-256 checksums before installation.
- Every node must have a permanent UUID and unique secret generated by the website.
- House assignment is downloaded automatically and never entered by teachers.
- Desktop startup must gracefully handle missing internet by using the latest valid local configuration.
- Configuration downloads must be atomic: either the entire package installs successfully or the previous version remains active.
- The application UI must refresh automatically after a successful configuration update.

---

# Architecture Summary

```
Administrator
      │
      ▼
 NiceGUI Website
      │
Publish Election
      │
      ▼
Generate Versioned Package
      │
      ▼
FastAPI Backend
      │
      ▼
Desktop Voting Node
      │
Check Version
      │
Download Package
      │
Validate SHA-256
      │
Install
      │
Load Local Configuration
      │
Ready for Voting
```

---

End of Part 05A – Node Registration & Configuration

# Election Management Platform SRS
# Part 05B – Vote Synchronization Engine

Version: 1.0

---

# 1. Overview

This document defines the complete synchronization engine used by every
desktop voting application.

The synchronization engine guarantees:

- Zero vote loss
- Offline voting
- Automatic synchronization
- Duplicate prevention
- Fast synchronization
- Reliable delivery
- Live website updates

The synchronization engine is completely automatic.

Teachers never need to manually synchronize votes.

---

# 2. Design Philosophy

The website is the **single source of truth**.

Desktop applications act as intelligent clients.

Every vote flows through the backend before reaching the website.

```
Teacher

↓

Desktop App

↓

Local Queue

↓

FastAPI

↓

MySQL

↓

Website

↓

Live Dashboard
```

---

# 3. Synchronization Objectives

The synchronization engine must:

✓ Never lose votes

✓ Continue during network failure

✓ Resume automatically

✓ Prevent duplicate votes

✓ Minimize bandwidth

✓ Support real-time updates

✓ Recover from crashes

---

# 4. Vote Lifecycle

```
Teacher Clicks Vote

↓

Vote Validation

↓

Local Database

↓

FakeRedis Queue

↓

Background Synchronizer

↓

REST API

↓

Server Validation

↓

MySQL

↓

ACK

↓

Delete Local Queue

↓

Broadcast Result
```

---

# 5. Vote Object

Each vote consists of

```json
{
    "vote_uuid":"UUID",
    "election_id":"UUID",
    "position_id":"UUID",
    "candidate_id":"UUID",
    "node_id":"UUID",
    "election_type":"Regular",
    "house_id":null,
    "created_at":"UTC Timestamp",
    "sync_status":"Pending"
}
```

---

# 6. Vote UUID

Every vote receives

```
UUID4
```

Example

```
7fa2a6b4-c3ef-4a43-a4d4-f52b36a8b962
```

UUID never changes.

---

# 7. Local Vote Storage

Immediately after voting

Store vote inside

```
SQLite

(or)

Configured Local MySQL
```

Vote is committed before UI confirmation.

Never rely only on RAM.

---

# 8. FakeRedis Queue

After saving

Push UUID into

```
FakeRedis Queue
```

Purpose

- Very fast queue
- Background processing
- Thread-safe
- No Redis installation

---

# 9. Queue Structure

```
Vote UUID

↓

Pending Queue

↓

Sending Queue

↓

Waiting ACK

↓

Completed

↓

Remove Queue
```

---

# 10. Queue States

Possible states

```
Pending

Uploading

Acknowledged

Retrying

Completed

Failed
```

---

# 11. Background Synchronizer

Runs continuously.

Loop

```
Check Queue

↓

Pending?

↓

Upload

↓

Receive ACK

↓

Delete Queue

↓

Sleep 200 ms

↓

Repeat
```

---

# 12. Batch Upload

Votes uploaded in batches.

Example

```
20 Votes

↓

1 REST Request

↓

Server

↓

ACK
```

Reduces bandwidth.

---

# 13. Synchronization API

Desktop calls

```
POST

/api/v1/sync/votes
```

Payload

```json
{
    "node_id":"UUID",
    "config_version":5,
    "votes":[ ... ]
}
```

---

# 14. Server Validation

Every vote is validated.

Checks

✓ JWT

✓ Node

✓ Election

✓ Candidate

✓ Position

✓ Configuration Version

✓ Vote UUID

✓ Timestamp

---

# 15. Duplicate Prevention

Server checks

```
vote_uuid
```

Exists?

YES

↓

Return Duplicate

NO

↓

Insert Vote

Duplicates are ignored safely.

---

# 16. ACK Response

```json
{
    "success":true,
    "accepted":[
        "UUID1",
        "UUID2"
    ],
    "duplicates":[

    ],
    "failed":[

    ]
}
```

Desktop deletes only accepted votes.

---

# 17. Retry Logic

Upload failure

↓

Keep Queue

↓

Retry Automatically

↓

Until ACK

Teacher continues voting.

---

# 18. Retry Schedule

```
5 Seconds

↓

10 Seconds

↓

20 Seconds

↓

40 Seconds

↓

60 Seconds

↓

60 Seconds Forever
```

---

# 19. Offline Mode

Internet Lost

↓

Continue Voting

↓

SQLite

↓

Queue Grows

↓

Reconnect

↓

Upload Everything

↓

Website Updated

---

# 20. Crash Recovery

Application crashes

↓

Restart

↓

Read SQLite Queue

↓

Restore FakeRedis Queue

↓

Resume Upload

No votes lost.

---

# 21. Power Failure

Power Failure

↓

SQLite Still Contains Votes

↓

Restart

↓

Recover Queue

↓

Synchronize

---

# 22. Synchronization Thread

Separate thread/process.

Never block UI.

Teacher never waits for upload.

---

# 23. Queue Manager

Responsibilities

- Add Votes
- Remove Votes
- Retry Failed
- Restore Queue
- Monitor Queue Size

---

# 24. Synchronization Manager

Responsibilities

- API Calls
- Batch Creation
- ACK Handling
- Retry
- Logging

---

# 25. Queue Limits

Maximum Queue

```
Unlimited
```

Practical expectation

```
50,000+ Votes
```

No data loss.

---

# 26. Live Broadcast

After successful insert

Backend broadcasts

```
Updated Candidate

Updated Count

Updated Ranking

Updated Percentage
```

Desktop does not use WebSocket for uploads.

---

# 27. Queue Monitoring

Desktop Status Bar

Displays

```
Pending

Uploading

Online

Offline

Synced

Queue Count
```

Example

```
Online

Queue

0

Synced
```

---

# 28. Conflict Handling

Wrong Configuration Version

↓

Reject Upload

↓

Notify Desktop

↓

Download Latest Configuration

↓

Retry

---

# 29. Invalid Candidate

Candidate deleted

↓

Reject Vote

↓

Log Error

↓

Administrator Notification

---

# 30. Logging

Synchronization Log

```
Vote Created

Queue Added

Upload Started

Upload Success

Upload Failed

Retry

ACK Received

Queue Removed
```

---

# 31. Synchronization Database Tables

Desktop

```
local_votes

queue

settings
```

Website

```
votes

vote_queue

sync_logs
```

---

# 32. Queue Recovery Algorithm

Startup

↓

Read SQLite

↓

Find Pending

↓

Push Into FakeRedis

↓

Start Synchronizer

↓

Resume

---

# 33. Performance Targets

Vote Save

<10 ms

Queue Insert

<5 ms

Batch Upload

<500 ms

ACK

<100 ms

Queue Recovery

<2 Seconds

---

# 34. Failure Handling

Network Error

↓

Retry

Authentication Error

↓

Re-login Node

Database Error

↓

Retry

Timeout

↓

Retry

Duplicate

↓

Ignore

Checksum Error

↓

Request Configuration

---

# 35. Synchronization Security

Every upload requires

✓ HTTPS

✓ JWT

✓ Node Secret

✓ Configuration Version

✓ Vote UUID

No anonymous uploads.

---

# 36. Scalability

Supports

16 Nodes

↓

32 Nodes

↓

64 Nodes

↓

128 Nodes

Without architecture changes.

---

# 37. Thread Safety

Queue operations must be protected using

```
Python threading.Lock

or

asyncio.Lock
```

No race conditions.

---

# 38. Audit Trail

Every synchronization records

Node

Time

Vote Count

Duration

Failures

Retries

IP Address

---

# 39. Acceptance Criteria

The Vote Synchronization Engine is complete when:

✓ Every vote is stored locally before upload.

✓ FakeRedis manages the in-memory queue.

✓ SQLite (or configured local MySQL) stores the persistent queue.

✓ Desktop recovers after crashes.

✓ Duplicate vote prevention works.

✓ Batch synchronization is implemented.

✓ Automatic retries continue until success.

✓ Offline voting is fully supported.

✓ UI remains responsive during synchronization.

✓ Live website updates occur immediately after successful synchronization.

✓ Synchronization logs are maintained.

---

# 40. Implementation Modules

Recommended modules

```
sync/

├── sync_manager.py

├── queue_manager.py

├── retry_manager.py

├── heartbeat.py

├── api_client.py

├── websocket_client.py

├── vote_serializer.py

├── sync_logger.py
```

---

# 41. Sequence Diagram

```
Teacher
   │
   ▼
Desktop Voting App
   │
   ▼
Save Vote (SQLite)
   │
   ▼
Push UUID → FakeRedis
   │
   ▼
Background Sync Manager
   │
   ▼
REST API (FastAPI)
   │
   ▼
Server Validation
   │
   ▼
MySQL
   │
   ▼
ACK Response
   │
   ▼
Remove Local Queue
   │
   ▼
WebSocket Broadcast
   │
   ├──────────────► Website Dashboard
   ├──────────────► Mobile Viewers
   └──────────────► Admin Dashboard
```

---

# 42. IMPORTANT IMPLEMENTATION REQUIREMENTS

The synchronization engine shall follow these mandatory rules:

- Votes **must always** be written to persistent local storage before being added to the FakeRedis queue.
- FakeRedis is used **only** as a high-speed in-memory queue and must never be treated as permanent storage.
- Vote uploads occur **only** through authenticated REST APIs.
- Live result updates are sent **only** through WebSocket broadcasts after successful database commits.
- Queue processing must run in the background and never block the voting interface.
- Every synchronization request must be idempotent using `vote_uuid`.
- Queue recovery must occur automatically after application restart.
- A vote is removed from local storage **only after** the backend acknowledges successful insertion.
- The engine must support uninterrupted voting even during extended internet outages.

---

# Architecture Summary

```
Teacher
    │
    ▼
Vote Screen
    │
    ▼
SQLite / Local MySQL
(Persistent Storage)
    │
    ▼
FakeRedis Queue
(Fast In-Memory Queue)
    │
    ▼
Background Sync Manager
    │
    ▼
REST API (FastAPI)
    │
    ▼
MySQL (Master Database)
    │
    ▼
WebSocket Broadcast
    │
    ├── NiceGUI Admin Website
    ├── Mobile Live View
    └── Dashboard Analytics
```

---

End of Part 05B – Vote Synchronization Engine

# Election Management Platform SRS
# Part 05C – Heartbeat, Health Monitoring & Recovery

Version: 1.0

---

# 1. Overview

This document defines the complete health monitoring, heartbeat protocol,
fault recovery mechanisms and automatic recovery procedures for the
Election Management Platform.

This module ensures that administrators always know the health of every
voting node while allowing every desktop voting application to recover
automatically from failures without losing votes.

The monitoring system is designed for uninterrupted election operations.

---

# 2. Objectives

The system shall provide

- Real-time node monitoring
- Automatic heartbeat transmission
- Online/Offline detection
- Automatic recovery after failures
- Network recovery
- Synchronization recovery
- Database recovery
- Configuration validation
- Live dashboard updates

---

# 3. System Architecture

```
Desktop Voting App

↓

Heartbeat Manager

↓

REST API

↓

FastAPI Server

↓

Node Monitor Service

↓

MySQL

↓

WebSocket

↓

Administrator Dashboard
```

---

# 4. Heartbeat Philosophy

Every voting node continuously reports its health to the server.

A heartbeat is **not** a vote.

It only informs the website that the node is alive.

---

# 5. Heartbeat Interval

Every node sends a heartbeat

```
Every 10 Seconds
```

The interval shall be configurable from the website.

Default

```
10 Seconds
```

Minimum

```
5 Seconds
```

Maximum

```
60 Seconds
```

---

# 6. Heartbeat Payload

Example

```json
{
    "node_id":"UUID",
    "node_name":"Regular-03",
    "election_type":"Regular",
    "assigned_house":null,
    "config_version":5,
    "queue_size":0,
    "last_vote_time":"2027-03-12T10:35:18",
    "app_version":"2.0.0",
    "os":"Windows 10",
    "status":"Healthy"
}
```

---

# 7. Heartbeat Flow

```
Desktop Node

↓

Collect Status

↓

Generate Payload

↓

POST /nodes/heartbeat

↓

Server Validation

↓

Database Update

↓

WebSocket Broadcast

↓

Dashboard Refresh
```

---

# 8. Heartbeat States

Possible node states

```
Healthy

Synchronizing

Offline

Warning

Configuration Outdated

Authentication Failed

Maintenance
```

---

# 9. Healthy State

Conditions

✓ Heartbeat received

✓ Queue empty

✓ Configuration current

✓ Database connected

✓ Synchronization working

Dashboard Color

```
Green
```

---

# 10. Warning State

Examples

Queue growing

↓

Slow internet

Database latency

↓

Configuration outdated

Dashboard Color

```
Yellow
```

---

# 11. Offline State

A node becomes Offline when

No heartbeat received for

```
30 Seconds
```

Dashboard Color

```
Red
```

---

# 12. Node Information Display

The website Node Monitor displays

- Node Name
- Election Type
- Assigned House
- Online Status
- Last Heartbeat
- Configuration Version
- Queue Size
- Pending Votes
- Last Vote Time
- Synchronization Status
- Local Database Status
- Application Version
- Operating System
- IP Address

---

# 13. Live Dashboard Updates

Whenever a heartbeat is received

↓

Update Node

↓

Broadcast

↓

Refresh Dashboard

No page refresh required.

---

# 14. Queue Monitoring

Each heartbeat includes

```
Pending Queue

Retry Queue

Failed Queue
```

Administrator immediately knows

- Which node has pending votes
- Which node has synchronization issues

---

# 15. Configuration Monitoring

Server compares

```
Node Version

Website Version
```

If mismatch

↓

Node marked

```
Configuration Outdated
```

Administrator can request update.

---

# 16. Recovery Philosophy

Failures should recover automatically whenever possible.

Teachers should never need technical intervention during voting.

---

# 17. Network Recovery

Internet Lost

↓

Continue Voting

↓

Store Votes Locally

↓

Retry Heartbeat

↓

Reconnect

↓

Resume Synchronization

---

# 18. Database Recovery

If local database connection fails

↓

Attempt Reconnect

↓

Retry

↓

Display Warning

↓

Continue when restored

Votes already saved remain intact.

---

# 19. Website Recovery

If website temporarily unavailable

↓

Continue Voting

↓

Queue Votes

↓

Retry API

↓

Reconnect Automatically

---

# 20. Synchronization Recovery

Upload fails

↓

Keep Queue

↓

Retry

↓

Receive ACK

↓

Delete Queue

---

# 21. Application Crash Recovery

Application crashes

↓

Restart

↓

Load Configuration

↓

Recover Local Queue

↓

Restart Heartbeat

↓

Resume Synchronization

No administrator action required.

---

# 22. Power Failure Recovery

Power Loss

↓

Restart Computer

↓

Launch Voting App

↓

Recover SQLite Queue

↓

Reconnect

↓

Continue

No votes lost.

---

# 23. Configuration Recovery

Configuration corrupted

↓

Detect SHA-256 mismatch

↓

Restore Backup

↓

Download Latest Package

---

# 24. Authentication Recovery

JWT Expired

↓

Automatic Node Login

↓

Receive New Token

↓

Continue

Teachers never log in.

---

# 25. Heartbeat Failure

If heartbeat cannot be sent

↓

Retry

↓

Retry

↓

Retry

↓

Mark Offline

Voting continues locally.

---

# 26. Retry Schedule

```
5 Seconds

10 Seconds

20 Seconds

40 Seconds

60 Seconds

Repeat
```

---

# 27. Node Health Indicators

Health Score

100%

↓

Excellent

75%

↓

Good

50%

↓

Warning

Below 25%

↓

Critical

Health score is calculated using

- Connectivity
- Queue Size
- Synchronization
- Database Status
- Configuration Status

---

# 28. Dashboard Colors

```
Green

Healthy

Yellow

Warning

Orange

Synchronizing

Red

Offline

Blue

Maintenance
```

---

# 29. Notifications

Administrator receives notifications for

- Node Offline
- Queue Growing
- Configuration Outdated
- Synchronization Failure
- Database Error
- Authentication Failure
- Recovery Successful

---

# 30. Website Monitoring Screen

Displays

```
Regular Election Nodes

House Election Nodes

↓

Expandable Details

↓

Live Status

↓

Statistics
```

---

# 31. Statistics

Dashboard displays

- Total Nodes
- Online Nodes
- Offline Nodes
- Synchronizing Nodes
- Pending Votes
- Failed Uploads
- Average Heartbeat Time
- Server Uptime

---

# 32. Logging

Heartbeat Log

```
Node Online

Node Offline

Heartbeat Received

Configuration Updated

Queue Increased

Queue Cleared

Recovery Started

Recovery Completed
```

---

# 33. Recovery Manager

Responsibilities

- Detect Failures
- Restart Synchronization
- Recover Queue
- Refresh JWT
- Restore Configuration
- Reconnect Database

Runs automatically.

---

# 34. Health APIs

The monitoring system uses

```
GET /health

GET /health/database

GET /health/node/{id}

POST /nodes/heartbeat
```

---

# 35. Performance Targets

Heartbeat Response

<100 ms

Dashboard Refresh

<250 ms

Offline Detection

<30 Seconds

Queue Recovery

<2 Seconds

Node Recovery

<10 Seconds

---

# 36. Security

Heartbeats require

✓ JWT Authentication

✓ Node Secret

✓ HTTPS

✓ TLS Encryption

✓ Node UUID

Unauthorized heartbeats are rejected.

---

# 37. Fault Tolerance

The monitoring system shall tolerate

- Internet interruptions
- Temporary server downtime
- Desktop application crashes
- Power failures
- Database reconnections
- Token expiration

without losing votes.

---

# 38. Acceptance Criteria

The Heartbeat & Recovery module is complete when

✓ Every node sends heartbeats automatically.

✓ Dashboard reflects node status in real time.

✓ Offline nodes are detected within 30 seconds.

✓ Configuration mismatches are detected.

✓ Queue status is visible.

✓ Database health is monitored.

✓ Automatic recovery works after crashes.

✓ Automatic recovery works after power failures.

✓ Synchronization resumes automatically.

✓ JWT renewal is automatic.

✓ Notifications appear instantly.

✓ Recovery events are logged.

---

# 39. Recommended Modules

```
health/

├── heartbeat_manager.py

├── health_monitor.py

├── recovery_manager.py

├── node_monitor.py

├── notification_manager.py

├── watchdog.py

├── reconnect_manager.py

├── diagnostics.py
```

---

# 40. Sequence Diagram

```
Desktop Voting App
        │
        ▼
Heartbeat Manager
        │
        ▼
POST /nodes/heartbeat
        │
        ▼
FastAPI Backend
        │
        ▼
Health Service
        │
        ▼
MySQL
        │
        ▼
WebSocket Broadcast
        │
        ├────────► Admin Dashboard
        ├────────► Node Monitor
        └────────► Mobile Live View
```

---

# 41. IMPORTANT IMPLEMENTATION REQUIREMENTS

- Every desktop node must start the Heartbeat Manager automatically during application startup.
- Heartbeats must continue independently of vote synchronization.
- A failed heartbeat must never interrupt voting.
- The monitoring system must distinguish between temporary network issues and permanent node failures.
- All recovery procedures must be automatic whenever possible.
- The dashboard must update immediately using WebSockets without requiring manual refresh.
- Every recovery event must be recorded in the audit log.
- Health monitoring must have minimal CPU and network overhead so that even older Windows systems perform reliably.

---

# Architecture Summary

```
Desktop Voting Node
        │
        ├── Heartbeat Manager
        ├── Health Monitor
        ├── Recovery Manager
        ├── Queue Monitor
        └── Diagnostics
                │
                ▼
        FastAPI Backend
                │
                ▼
             MySQL
                │
                ▼
        WebSocket Broadcast
                │
      ┌─────────┴─────────┐
      │                   │
Admin Dashboard      Mobile Viewers
      │
Node Monitoring
```

---

End of Part 05C – Heartbeat, Health Monitoring & Recovery
