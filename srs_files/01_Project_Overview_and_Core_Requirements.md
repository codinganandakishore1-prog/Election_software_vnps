# Election Management Platform SRS

## Part 1 -- Project Overview & Core Requirements

### Executive Summary

This SRS defines the redesign of the existing Python election
application into a modular client-server platform while preserving all
existing features.

### Objectives

-   Preserve existing UI and workflow
-   Website as single source of truth
-   Cross-platform desktop app
-   Global live results
-   Offline-capable voting nodes

### High-Level Architecture

Website -\> Publish Election -\> Nodes Download Configuration -\>
Teachers Vote -\> Local Queue -\> Sync -\> MySQL -\> WebSocket -\> Live
Dashboard

### Election Types

-   Regular Election (8 nodes)
-   House Election (8 nodes; 2 each for Pallava, Pandya, Chera, Chola)
    House assignments are preconfigured by the admin.

### Roles

Website Admin: full management. Node Admin: configure node, database,
download configuration. Teacher: voting only.

### Device Responsibilities

Desktop/Laptop: full administration. Mobile/Tablet: login and read-only
live dashboard.

### Website Responsibilities

Candidate management, image editing (crop/rotate/zoom/preview),
positions, election setup, node management, reports, analytics,
monitoring.

### Desktop Responsibilities

Voting, local cache, local MySQL, queue, synchronization, diagnostics,
configuration download.

### Development Phases

Phase 1: analyze project and produce documentation. Stop for approval.
Phase 2: implement after approval while preserving all features.
