# Election Management Platform SRS
# Part 2 – Desktop Voting Application Specification

Version: 1.0

---

# 1. Overview

The Desktop Voting Application is the official client application used during elections.

Its primary responsibility is to provide a fast, reliable, secure and offline-capable voting experience.

Unlike the existing application, the desktop application is NOT responsible for creating or editing elections.

The website becomes the single source of truth.

The desktop application downloads the published election and performs only voting-related operations.

---

# 2. Core Design Philosophy

The desktop application should remain visually familiar to the current system.

Teachers who already know the application should not require additional training.

Therefore:

- Preserve the existing voting workflow.
- Preserve the overall UI style.
- Preserve all animations.
- Preserve the existing fullscreen workflow.
- Preserve candidate card layouts.
- Preserve navigation wherever practical.

The only major architectural change is that election creation moves to the website.

---

# 3. Platform Requirements

The application must run on:

- Windows 7
- Windows 8
- Windows 10
- Windows 11
- macOS
- Linux

No platform-specific code should be required unless unavoidable.

---

# 4. Technology Stack

Desktop Framework

- Python
- CustomTkinter

Image Processing

- Pillow

Packaging

- PyInstaller

Networking

- Requests
- WebSockets

Database

- MySQL

Queue

- FakeRedis or equivalent lightweight local queue.

---

# 5. Display Requirements

The desktop application must automatically adjust itself to:

- Different monitor resolutions
- Different DPI scaling
- Different operating systems
- Small displays
- Large displays

No controls should overlap.

No controls should become inaccessible.

Images should scale proportionally.

Buttons should resize automatically.

Fonts should scale appropriately.

---

# 6. Window Behaviour

All windows must:

- Open centered.
- Stay above the parent window.
- Never open behind another window.
- Behave modally where appropriate.
- Return focus correctly.

Examples:

Main Window

↓

Admin Login

↓

Database Settings

↓

Back to Admin

NOT

Main Window

↓

Database Window opens behind the Main Window.

---

# 7. Application Modules

The desktop application consists of:

1. Splash Screen
2. Main Menu
3. Voting Screen
4. Administrator Login
5. Administrator Panel
6. Node Configuration
7. Local Database Settings
8. Download Election
9. View Downloaded Election
10. Synchronization Status
11. Diagnostics
12. About

---

# 8. Splash Screen

Display:

- School Logo
- Election Name
- Version
- Loading Animation

During startup:

- Verify local database
- Verify configuration
- Verify downloaded election
- Verify network

Then continue.

---

# 9. Main Menu

The Main Menu should remain visually similar to the existing application.

Buttons:

- Start Voting
- Administrator
- Exit

No unnecessary redesign.

---

# 10. Voting Screen

The Voting Screen should preserve the current workflow.

Requirements:

- Candidate photographs
- Candidate names
- Position title
- Easy navigation
- Fast operation
- Confirmation dialogs
- Vote completion screen

No additional steps should be introduced.

---

# 11. Voting Workflow

Teacher begins voting.

↓

Select Candidate

↓

Confirm Vote

↓

Store Vote

↓

Queue Synchronization

↓

Next Position

↓

Complete

The teacher should never wait for synchronization.

Synchronization occurs in the background.

---

# 12. Administrator Login

Administrator authentication is required before accessing:

- Node settings
- Database settings
- Synchronization
- Diagnostics
- Download election

---

# 13. Administrator Panel

The administrator panel is simplified.

It no longer creates elections.

Functions:

- Download Election
- View Downloaded Election
- Node Configuration
- Local Database Settings
- Synchronization Status
- Diagnostics
- Logout

---

# 14. Download Election

Workflow:

Administrator

↓

Download Election

↓

Connect to Website

↓

Authenticate Node

↓

Check Election Version

↓

If newer version exists

↓

Download Configuration

↓

Store Locally

↓

Ready

Downloaded data includes:

- Election information
- Candidates
- Candidate images
- Positions
- House configuration
- Theme assets
- Backgrounds
- Settings

---

# 15. Election Versioning

Every election has a version number.

Example:

Version 1

↓

Version 2

↓

Version 3

The desktop application compares versions.

If newer:

Display:

Update Available

Version 4

Current Version:

3

Download?

Administrator chooses when to download.

Never auto-update during active voting.

---

# 16. View Downloaded Election

Administrator can inspect downloaded data.

Display:

Election Name

Election Type

Version

Published Date

Candidates

Positions

Images

House Assignment

This page is read-only.

No editing.

---

# 17. Candidate Viewer

Display every downloaded candidate.

Include:

Photo

Name

Position

Election Type

House

Preview only.

No editing.

---

# 18. Node Configuration

Each desktop application stores:

Node Name

Election Type

Assigned House

Secret Key

Website URL

Synchronization Settings

Configuration is permanent until changed.

---

# 19. House Assignment

The administrator configures:

Election Type:

Regular

OR

House

If House:

Choose:

- Pallava
- Pandya
- Chera
- Chola

This assignment is never shown to teachers.

Students never select their house.

---

# 20. Local Database Settings

Administrator can configure:

Host

Port

Database

Username

Password

Buttons:

Test Connection

Save

Reconnect

No restart required.

---

# 21. Local Storage

The application stores locally:

Election

Configuration

Candidates

Images

Votes

Synchronization Queue

Logs

Settings

---

# 22. Vote Storage

Every vote is immediately stored locally.

Only after successful local storage should synchronization begin.

This guarantees no vote loss.

---

# 23. Synchronization

Synchronization occurs in the background.

Workflow:

Vote

↓

Save Local

↓

Queue

↓

Send Website

↓

Confirmation

↓

Remove Queue Entry

Failed transmissions remain queued.

---

# 24. Synchronization Status

Administrator can monitor:

Website Connected

Queue Size

Pending Votes

Successful Syncs

Failed Syncs

Last Synchronization

---

# 25. Diagnostics

Display:

Database Status

Website Status

WebSocket Status

Synchronization Queue

Node Version

Election Version

System Information

---

# 26. Offline Behaviour

The application must continue operating when:

LAN disconnects

Internet disconnects

Website unavailable

Synchronization resumes automatically when connectivity returns.

---

# 27. Security

Node Secret

JWT Authentication

Encrypted Communication

Role Validation

No plaintext credentials in logs.

---

# 28. Error Handling

Provide user-friendly messages.

Never expose stack traces.

Log technical details internally.

Allow retry where appropriate.

---

# 29. Performance Requirements

Voting response:

<100 ms

Synchronization:

Background

Application startup:

<5 seconds

No UI freezing during synchronization.

---

# 30. Migration Requirements

The following features must be removed from the desktop application and migrated to the website while preserving functionality:

- Candidate Creation
- Candidate Editing
- Candidate Deletion
- Image Upload
- Image Crop
- Image Rotate
- Image Zoom
- Position Management
- Election Creation
- Election Publishing

The desktop application retains read-only access to downloaded election data.

---

# 31. Acceptance Criteria

The desktop application is considered complete when:

✓ Existing voting workflow preserved

✓ Existing UI largely preserved

✓ Cross-platform

✓ Responsive

✓ Offline capable

✓ Automatic synchronization

✓ Website configuration download

✓ Read-only election viewer

✓ Secure authentication

✓ Local MySQL configurable

✓ Stable under network interruption

---

End of Part 2