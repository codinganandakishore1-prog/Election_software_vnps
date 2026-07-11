# Election Management Platform SRS
# Part 3A – Website Architecture, Authentication, Dashboard & Navigation

Version: 1.0

---

# 1. Overview

The website serves as the **Central Control Unit (CCU)** for the Election Management Platform.

It is the **single source of truth** for the entire election system.

All election configuration, candidate management, synchronization, monitoring, analytics, reporting and administration originate from the website.

Voting nodes are clients that download the published election configuration and synchronize votes back to the website.

The website must be implemented entirely in Python using:

- FastAPI
- NiceGUI
- SQLAlchemy
- MySQL
- WebSockets
- JWT Authentication

No PHP, JavaScript frameworks (React, Vue, Angular) or Node.js backend should be used unless absolutely required by NiceGUI.

---

# 2. Website Objectives

The website has four major responsibilities.

## 2.1 Election Management

The website creates and publishes elections.

No desktop voting node is allowed to create or modify election data.

---

## 2.2 Monitoring

The website continuously monitors:

- Voting nodes
- Live vote counts
- Synchronization status
- Node health
- Connected administrators

---

## 2.3 Administration

The website manages:

- Candidates
- Positions
- Houses
- Elections
- Users
- Database configuration
- Node assignments
- Reports

---

## 2.4 Live Results

The website displays live results through WebSockets.

Results should update instantly without refreshing the page.

---

# 3. Website Architecture

```
                    Internet

                        │

             Cloudflare Tunnel
              (or equivalent)

                        │

                 FastAPI Backend

                        │

         ┌──────────────┴───────────────┐
         │                              │

     NiceGUI Website              WebSocket Server

         │                              │

         └──────────────┬───────────────┘

                    SQLAlchemy

                        │

                     MySQL

                        │

            Voting Nodes (16 Total)

         8 Regular + 8 House Nodes
```

---

# 4. Website Design Principles

The website should follow these principles.

## Simple

Administrators should never require technical knowledge.

Every operation should require the minimum number of clicks.

---

## Responsive

Desktop

Laptop

Tablet

Mobile

must all function correctly.

---

## Fast

No page should feel slow.

Use lazy loading where appropriate.

---

## Modern

The UI should resemble modern SaaS dashboards.

Examples of inspiration:

- GitHub
- Vercel
- Supabase
- Linear
- Cloudflare Dashboard

NOT old Bootstrap admin panels.

---

## Clean

Use consistent:

- spacing
- typography
- colors
- icons
- animations

---

# 5. Authentication

Every administrator must log in.

No anonymous administration.

---

## Login Screen

Display:

School Logo

Election System Logo

Title

Username

Password

Remember Me

Login Button

Forgot Password (optional)

Version Number

---

## Login Validation

Validate:

Username

↓

Password

↓

Role

↓

JWT Generation

↓

Dashboard

---

## Failed Login

Display friendly messages.

Never reveal whether:

Username exists

OR

Password is wrong.

Simply display:

"Invalid username or password."

---

## Session Timeout

Automatically logout after configurable inactivity.

Default:

30 minutes.

---

## Password Storage

Passwords must NEVER be stored in plain text.

Use:

bcrypt

or

Argon2

---

# 6. User Roles

## Super Administrator

Complete access.

Can:

- Everything

---

## Administrator

Can:

- Create elections
- Edit elections
- Publish elections
- Candidate management
- Reports
- Monitoring

Cannot create Super Administrators.

---

## Viewer

Read-only.

Can:

- Dashboard
- Live results
- Reports

Cannot edit anything.

---

# 7. Dashboard Overview

After login the administrator sees the Dashboard.

This page summarizes the entire election.

It should feel like a professional control center.

---

Display cards.

Example:

```
Election

School Election 2026

-----------------------

Status

LIVE

-----------------------

Votes

1864

-----------------------

Nodes Online

16 / 16

-----------------------

Pending Queue

3

-----------------------

Last Vote

2 Seconds Ago
```

---

# 8. Dashboard Layout

Desktop Layout

```
---------------------------------------------------------

 Sidebar

 Dashboard

---------------------------------------------------------

 Statistics Cards

---------------------------------------------------------

 Live Charts

---------------------------------------------------------

 Node Health

---------------------------------------------------------

 Recent Activity

---------------------------------------------------------
```

---

Tablet Layout

```
Statistics

↓

Charts

↓

Nodes

↓

Activity
```

---

Mobile Layout

```
Statistics

↓

Charts

↓

Nodes
```

No editing.

Read only.

---

# 9. Sidebar Navigation

The sidebar should remain visible on desktop.

Sections:

Dashboard

Regular Election

House Election

Candidates

Positions

Election Management

Node Monitor

Reports

Analytics

Audit Logs

Settings

Logout

Icons should accompany every menu item.

---

# 10. Top Navigation Bar

Contains:

School Logo

Election Name

Search

Notifications

Dark Mode Toggle

Current User

Logout

---

# 11. Dashboard Cards

Display:

Current Election

Election Status

Votes Cast

Online Nodes

Offline Nodes

Pending Queue

Synchronization Errors

Connected Users

Database Status

Website Status

---

Cards should update live.

No refresh.

---

# 12. Live Charts

Display:

Votes Per Minute

Votes Per Position

Node Activity

Vote Distribution

House Activity

Charts update automatically.

---

# 13. Recent Activity

Timeline style.

Example:

```
09:21

Node 05 Connected

----------------

09:24

Vote Received

----------------

09:25

Candidate Updated

----------------

09:30

Report Downloaded
```

---

# 14. Notifications

Notifications should appear for:

Election Published

Node Offline

Node Online

Database Error

Synchronization Error

Election Started

Election Ended

Download Completed

Administrator Login

---

# 15. Search

Global search.

Can search:

Candidates

Positions

Nodes

Reports

Users

---

# 16. Dark Mode

Support:

Light Theme

Dark Theme

Preference remembered.

---

# 17. Dashboard Refresh

Do NOT poll every second.

Use:

WebSockets

Dashboard updates instantly.

---

# 18. Mobile Restrictions

Mobile users may:

Login

View Dashboard

View Results

View Charts

View Reports

Logout

Mobile users may NOT:

Create Candidates

Edit Candidates

Delete Candidates

Publish Elections

Configure Database

Configure Nodes

Modify Settings

---

# 19. Desktop Requirements

Desktop users receive:

Full Administration Portal

Complete Candidate Manager

Complete Image Editor

Election Configuration

Node Management

Reports

Analytics

Settings

---

# 20. Performance Goals

Dashboard Load

< 2 Seconds

Live Update Delay

< 200 ms

Login

< 1 Second

Navigation

Instant

Charts

Smooth

---

# 21. Error Handling

If database disconnects:

Show warning banner.

Attempt automatic reconnect.

Do not crash.

If WebSocket disconnects:

Reconnect automatically.

Notify administrator.

---

# 22. Accessibility

Minimum font size:

14px equivalent

Keyboard navigation supported.

High contrast mode friendly.

Buttons must have sufficient spacing for touch devices.

---

# 23. Acceptance Criteria

The Website Dashboard is considered complete when:

✓ Login is secure.

✓ JWT authentication works.

✓ Responsive layout functions on desktop, tablet and mobile.

✓ Dashboard updates live using WebSockets.

✓ Sidebar navigation works.

✓ Top navigation works.

✓ Statistics update instantly.

✓ Recent activity updates live.

✓ Mobile is read-only.

✓ Desktop receives full administration.

✓ Modern, aesthetic and professional UI comparable to commercial SaaS platforms.

---

End of Part 3A

# Election Management Platform SRS
# Part 3B-1 – Candidate Management System

Version: 1.0

---

# 1. Overview

The Candidate Management System is one of the most important components of the Election Management Platform.

Unlike the existing desktop application, all candidate creation and management will now be performed exclusively through the Website Administration Portal.

The desktop voting application will never create, edit or delete candidates.

Instead, it downloads the published election configuration from the website.

The objective is to preserve the complete functionality and user experience of the current desktop application's Candidate Management interface while relocating it to the website.

---

# 2. Design Goals

The Candidate Manager must:

- Be simple for teachers and election administrators.
- Preserve the existing workflow from the desktop application.
- Require minimal training.
- Support both Regular and House Elections.
- Prevent invalid candidate configurations.
- Provide instant previews.
- Support responsive layouts.
- Integrate seamlessly with the publishing system.

---

# 3. Candidate Manager Dashboard

Navigation

Website

↓

Candidates

↓

Candidate Dashboard

The dashboard displays every candidate grouped by election type and position.

Example:

```

Candidates

Total Candidates : 42

Regular Election : 30

House Election : 12

──────────────────────────────────────────

Regular Election

School Pupil Leader

[ Candidate Card ]

[ Candidate Card ]

[ Candidate Card ]

──────────────────────────────────────────

Sports Captain

[ Candidate Card ]

[ Candidate Card ]

──────────────────────────────────────────

House Election

Pallava

House Captain

[ Candidate Card ]

[ Candidate Card ]

──────────────────────────────────────────

Pandya

House Captain

[ Candidate Card ]

...

```

---

# 4. Candidate Card

Each candidate is displayed as a professional card.

Display:

Candidate Photo

Candidate Name

Position

Election Type

House (if applicable)

Candidate Status

Quick Actions

Example

```

+--------------------------------+

PHOTO

-----------------------

John Doe

School Pupil Leader

Regular Election

Active

-----------------------

Edit

Delete

Preview

+--------------------------------+

```

Cards should resize automatically.

---

# 5. Candidate Status

Possible statuses:

Active

Inactive

Draft

Published

Only Active candidates appear during voting.

---

# 6. Candidate Information

Every candidate record stores:

Candidate Name

Candidate ID

Election Type

Position

House

Photo

Display Order

Status

Creation Date

Last Modified

Created By

Modified By

---

# 7. Election Type Selection

Every candidate belongs to exactly one election.

Options

Regular Election

House Election

---

# 8. House Selection

Visible only when

Election Type

=

House Election

Available options:

Pallava

Pandya

Chera

Chola

The field remains hidden for Regular Election candidates.

---

# 9. Position Selection

Position list is populated dynamically.

Examples:

School Pupil Leader

Assistant School Pupil Leader

Sports Captain

House Captain

Vice Captain

Discipline Leader

Administrators may create custom positions.

---

# 10. Add Candidate

Administrator clicks

Add Candidate

↓

Candidate Form

↓

Upload Image

↓

Crop Image

↓

Preview

↓

Save

↓

Candidate Created

---

# 11. Edit Candidate

Administrator selects

Edit

↓

Existing information loads

↓

Modify

↓

Save

↓

Changes reflected immediately

Voting nodes receive the update only after

Publish Election.

---

# 12. Delete Candidate

Delete operation requires confirmation.

Example

Delete Candidate?

John Doe

This action cannot be undone.

Cancel

Delete

Deletion is prevented if:

Election is currently Live.

---

# 13. Duplicate Prevention

Prevent duplicate:

Candidate Name

within the same Position

and Election.

Different positions may contain identical names if required.

---

# 14. Candidate Validation

Required fields:

Candidate Name

Position

Election Type

Photo

Validation examples:

Name cannot be empty.

Photo required.

Position required.

House required for House Election.

---

# 15. Candidate Ordering

Candidates should support drag-and-drop ordering.

The displayed order becomes the voting order.

Manual order numbers are also supported.

---

# 16. Bulk Operations

Support:

Delete Multiple

Enable Multiple

Disable Multiple

Move Multiple

Export Selected

---

# 17. Search

Instant search.

Search by:

Candidate Name

Position

House

Election Type

Status

---

# 18. Filters

Available filters:

Regular Election

House Election

Pallava

Pandya

Chera

Chola

Published

Draft

Active

Inactive

---

# 19. Sorting

Allow sorting by:

Name

Position

House

Creation Date

Last Modified

Display Order

---

# 20. Candidate Preview

Administrator may preview exactly how the candidate appears inside the desktop voting application.

Display:

Photo

Name

Position

Theme

Background

Vote Button

This preview is read-only.

---

# 21. Publishing Behaviour

Editing candidates does NOT immediately affect voting.

Workflow:

Edit Candidate

↓

Save

↓

Draft Updated

↓

Publish Election

↓

Nodes Detect New Version

↓

Administrator Downloads Configuration

↓

Voting Updated

---

# 22. Candidate Synchronization

Voting nodes never edit candidates.

Workflow:

Website

↓

Published Election

↓

Desktop Downloads

↓

Local Storage

↓

Read Only

---

# 23. Audit Logging

Every candidate action is logged.

Record:

User

Action

Timestamp

Candidate

IP Address

Browser

Examples:

Candidate Created

Candidate Updated

Candidate Deleted

Candidate Published

---

# 24. Responsive Layout

Desktop

Four cards per row.

Laptop

Three cards.

Tablet

Two cards.

Mobile

Single column.

Mobile remains read-only.

---

# 25. Permissions

Super Administrator

Full access.

Administrator

Full Candidate Management.

Viewer

Read only.

No editing.

---

# 26. Performance Requirements

Search

<100 ms

Save Candidate

<500 ms

Page Load

<2 seconds

Preview

Instant

---

# 27. Error Handling

Friendly validation messages.

Examples:

Candidate name already exists.

Please upload a photo.

House must be selected.

Position is required.

No technical error messages shown to users.

---

# 28. Acceptance Criteria

The Candidate Manager is considered complete when:

✓ Existing desktop workflow is preserved.

✓ Candidate CRUD is fully functional.

✓ Candidate cards are responsive.

✓ Search and filters work.

✓ Drag-and-drop ordering works.

✓ Validation prevents invalid data.

✓ Publishing does not immediately affect voting.

✓ Voting nodes receive candidates only through published configurations.

✓ Mobile remains read-only.

✓ The interface is modern, responsive and aesthetically polished.

---

# IMPORTANT IMPLEMENTATION REQUIREMENT

The Candidate Management module MUST preserve the functionality and overall user experience of the existing `app.py` Candidate Manager.

Do NOT redesign or simplify workflows unless they improve usability without removing features.

The image upload workflow, candidate editing experience, previews and overall interaction should feel familiar to existing users of the desktop application.

End of Part 3B-1

# Election Management Platform SRS
# Part 3B-2 – Candidate Image Editor

Version: 1.0

---

# 1. Overview

The Candidate Image Editor is responsible for creating professional, uniform candidate photographs for the election.

This module replaces the image editing functionality currently available in the desktop application.

The objective is **NOT** to redesign the workflow.

Instead, the website should preserve the current image editing experience while improving usability and responsiveness.

Every image displayed in the voting application must originate from this editor.

---

# 2. Design Goals

The Image Editor must:

- Preserve the existing image editing workflow.
- Be simple enough for school administrators.
- Produce uniform candidate photographs.
- Support all modern image formats.
- Provide instant preview.
- Prevent accidental distortion.
- Be responsive.
- Work entirely inside the browser.

---

# 3. Supported Formats

Input Formats

- JPG
- JPEG
- PNG
- WEBP
- BMP

Output Format

PNG (Preferred)

or

JPEG (Configurable)

---

# 4. Image Upload

Administrator clicks

Upload Image

↓

Select Image

↓

Image Opens Inside Editor

Supported upload methods:

- File Browser
- Drag & Drop
- Paste from Clipboard (Optional)

---

# 5. Image Editor Layout

Desktop Layout

```
--------------------------------------------------------

Original Image

--------------------------------------------------------

Toolbar

Rotate Left

Rotate Right

Zoom +

Zoom -

Reset

Crop

Save

--------------------------------------------------------

Live Preview

--------------------------------------------------------

Cancel

Save

--------------------------------------------------------
```

Tablet Layout

Toolbar becomes vertical.

Mobile

Read Only.

No editing.

---

# 6. Image Preview

The administrator should always see:

Original Image

Edited Image

Live Candidate Preview

Changes update instantly.

No page refresh.

---

# 7. Crop Tool

Crop must support:

- Free Crop
- Square Crop
- Portrait Crop
- Landscape Crop

Default:

Portrait

Crop Area should be draggable.

Crop Area should be resizable.

---

# 8. Rotation

Buttons:

Rotate Left

Rotate Right

Each click rotates:

90°

Administrator may continue rotating until correct orientation.

---

# 9. Zoom

Buttons:

Zoom In

Zoom Out

Mouse Wheel

Trackpad Pinch (if supported)

Zoom limits:

25%

↓

400%

---

# 10. Pan

While zoomed,

administrator may drag the image.

The crop frame remains fixed.

---

# 11. Reset

Reset restores:

Rotation

Zoom

Crop

Pan

Original Image

---

# 12. Live Preview

A candidate card should be displayed beside the editor.

Example

```
+----------------------------+

PHOTO

----------------------

John Doe

School Pupil Leader

----------------------

Vote

+----------------------------+
```

Every edit updates the preview immediately.

---

# 13. Image Quality

Do not reduce image quality unnecessarily.

Use high-quality resizing.

Avoid visible compression artifacts.

---

# 14. Automatic Resize

When saving,

generate multiple versions.

Original

↓

Large

↓

Voting Size

↓

Thumbnail

Suggested Sizes

Original

Keep

Large

800 × 1000

Voting

400 × 500

Thumbnail

150 × 180

---

# 15. Aspect Ratio

Maintain aspect ratio.

Prevent image stretching.

Prevent distortion.

---

# 16. Image Background

Support:

Original Background

Transparent Background (PNG)

Future AI Background Removal (Reserved)

No AI implementation required.

---

# 17. Image Validation

Reject:

Corrupted Images

Unsupported Formats

Empty Files

Maximum Upload Size

10 MB

Minimum Resolution

300 × 300

---

# 18. Save Workflow

Administrator

↓

Upload

↓

Crop

↓

Rotate

↓

Zoom

↓

Preview

↓

Save

↓

Image Stored

↓

Candidate Updated

The voting application receives the image only after the election is published.

---

# 19. Image Storage

Store:

Original Image

Processed Image

Thumbnail

Metadata

Metadata includes:

Width

Height

File Type

Upload Date

Uploaded By

---

# 20. Image Naming

Never use candidate names.

Instead use:

Candidate UUID

Example

candidate_9a7fd83f.png

This prevents duplicate filenames.

---

# 21. Editing Existing Images

Administrator selects

Edit Image

↓

Original Image Opens

↓

Previous Crop Restored

↓

Continue Editing

↓

Save

The original image should always remain available.

---

# 22. Image Replacement

Administrator may replace an image.

Confirmation required.

Replace Candidate Image?

Cancel

Replace

---

# 23. Performance

Image Upload

< 2 Seconds

Crop Response

Instant

Rotation

Instant

Zoom

Smooth

Save

< 1 Second

---

# 24. Error Handling

Examples

Unsupported Image Format

Image Too Large

Upload Failed

Image Corrupted

Storage Error

Messages should be friendly.

No technical exceptions shown.

---

# 25. Responsive Behaviour

Desktop

Full Editor

Laptop

Full Editor

Tablet

Simplified Toolbar

Mobile

Read Only

No editing.

---

# 26. Security

Validate MIME Type.

Validate Extension.

Prevent executable uploads.

Prevent path traversal.

Store outside public directory.

Serve through authenticated backend.

---

# 27. Integration with Candidate Manager

The Image Editor is launched directly from:

Candidate Manager

↓

Upload/Edit Photo

↓

Image Editor

↓

Save

↓

Return to Candidate Manager

No separate page required.

---

# 28. Integration with Election Publishing

Images become active only after:

Save Candidate

↓

Publish Election

↓

Nodes Download Configuration

↓

Voting Updated

This prevents inconsistencies during a live election.

---

# 29. Desktop Voting Application

The desktop application never edits images.

It simply downloads:

- Processed Candidate Image
- Thumbnail
- Metadata

and displays them exactly as configured on the website.

---

# 30. Acceptance Criteria

The Image Editor is considered complete when:

✓ Image upload works.

✓ Crop works.

✓ Rotate works.

✓ Zoom works.

✓ Pan works.

✓ Reset works.

✓ Live preview updates instantly.

✓ Images are resized automatically.

✓ Originals are preserved.

✓ Processed images are generated.

✓ Mobile is read-only.

✓ Images synchronize correctly after publishing.

✓ Existing desktop image editing workflow is preserved.

---

# IMPORTANT IMPLEMENTATION REQUIREMENT

The Image Editor must preserve the functionality and user experience of the existing desktop application's image editing module.

Do NOT replace it with a basic file upload dialog.

The administrator must be able to:

- Upload
- Crop
- Rotate
- Zoom
- Pan
- Preview
- Save

using an intuitive, responsive interface that closely resembles the existing desktop workflow while taking advantage of the website's larger workspace.

End of Part 3B-2

# Election Management Platform SRS
# Part 3B-3 – Position Management System

Version: 1.0

---

# 1. Overview

The Position Management System allows administrators to create, edit, organize, and manage all election positions available in both Regular Elections and House Elections.

Unlike the existing desktop application, all position management shall be performed exclusively through the Website Administration Portal.

The desktop voting application will only download published positions and display them during voting.

---

# 2. Objectives

The Position Management module shall:

- Centralize all position configuration.
- Support unlimited election positions.
- Support Regular Election positions.
- Support House Election positions.
- Support custom positions.
- Prevent duplicate configurations.
- Preserve the workflow of the current desktop application.
- Synchronize positions to all voting nodes.

---

# 3. Position Dashboard

Navigation

Website

↓

Election Management

↓

Positions

↓

Position Dashboard

Example

```

Regular Election

-----------------------------

School Pupil Leader

Assistant School Pupil Leader

Sports Captain

Cultural Secretary

Discipline Captain

-----------------------------

House Election

-----------------------------

House Captain

Vice Captain

Sports Captain

-----------------------------

```

---

# 4. Position Categories

Every position belongs to one election type.

### Regular Election

Examples

- School Pupil Leader
- Assistant School Pupil Leader
- Sports Captain
- Cultural Secretary
- Discipline Captain

### House Election

Examples

- House Captain
- Vice Captain
- Sports Captain
- Discipline Leader

---

# 5. Position Information

Each position stores:

- Position ID (UUID)
- Position Name
- Election Type
- House Assignment (optional)
- Number of Winners
- Display Order
- Status
- Created Date
- Modified Date
- Created By
- Modified By

---

# 6. Position Status

Available statuses

- Active
- Inactive
- Draft
- Published

Only Active positions appear in voting.

---

# 7. Add Position

Administrator clicks

Add Position

↓

Position Form

↓

Enter Position Name

↓

Choose Election Type

↓

Configure Position

↓

Save

↓

Position Created

---

# 8. Edit Position

Administrator selects

Edit

↓

Modify Details

↓

Save

↓

Position Updated

Changes become active only after Publish Election.

---

# 9. Delete Position

Deleting a position requires confirmation.

Example

```
Delete Position?

School Pupil Leader

This action cannot be undone.

Cancel

Delete
```

Deletion is blocked if:

- Election is Live
- Candidates are assigned

---

# 10. Number of Winners

Each position can specify:

Example

```
School Pupil Leader

Number of Winners

1

----------------------

Sports Captain

Number of Winners

2

----------------------

Committee Member

Number of Winners

5
```

Winner calculation uses this value.

---

# 11. Candidate Assignment

Each position maintains its own candidate list.

Example

```
School Pupil Leader

Candidates

John

Sarah

Kevin

------------------------

Sports Captain

Candidates

David

Peter

Mark
```

Candidates may only belong to one position within the same election.

---

# 12. House Position Assignment

House positions are shared across houses.

Example

```
House Captain

↓

Pallava

↓

Candidates

-----------------------

House Captain

↓

Pandya

↓

Candidates

-----------------------

House Captain

↓

Chera

↓

Candidates

-----------------------

House Captain

↓

Chola

↓

Candidates
```

Administrators do not create four separate House Captain positions.

Instead, one position is reused across all houses.

---

# 13. House Configuration

Administrator configures:

House Election

↓

Number of Positions

↓

Examples

House Captain

Vice Captain

Sports Captain

These positions automatically exist for:

- Pallava
- Pandya
- Chera
- Chola

---

# 14. Position Ordering

Support:

Drag & Drop

Move Up

Move Down

Manual Display Order

Voting follows the configured order.

---

# 15. Search

Search by:

- Position Name
- Election Type
- Status

Search updates instantly.

---

# 16. Filters

Available filters

Regular Election

House Election

Published

Draft

Active

Inactive

---

# 17. Bulk Operations

Support

- Delete Multiple
- Activate Multiple
- Deactivate Multiple
- Publish Multiple
- Export Selected

---

# 18. Validation Rules

Position Name

Required

Election Type

Required

Display Order

Required

Duplicate names are allowed only when they belong to different election types.

Duplicate positions within the same election are prohibited.

---

# 19. Position Preview

Administrator may preview voting sequence.

Example

```
Voting Order

1

School Pupil Leader

↓

2

Assistant School Pupil Leader

↓

3

Sports Captain

↓

4

Cultural Secretary
```

---

# 20. Election Publishing

Editing a position does not immediately affect voting.

Workflow

Edit Position

↓

Save Draft

↓

Publish Election

↓

Nodes Detect Version

↓

Administrator Downloads

↓

Voting Updated

---

# 21. Synchronization

Voting nodes never edit positions.

Workflow

Website

↓

Published Position List

↓

Desktop Download

↓

Read Only

---

# 22. Audit Logs

Log every operation

Position Created

Position Updated

Position Deleted

Position Published

Record:

- User
- Timestamp
- IP Address
- Browser
- Previous Value
- New Value

---

# 23. Responsive Layout

Desktop

Table + Cards

Laptop

Cards

Tablet

Cards

Mobile

Read Only

---

# 24. Performance

Load Positions

< 1 Second

Save Position

< 500 ms

Search

< 100 ms

Reordering

Instant

---

# 25. Error Handling

Friendly validation

Examples

Position already exists.

Position name required.

Cannot delete a position with assigned candidates.

Election is currently Live.

No technical errors shown.

---

# 26. Position Locking

Once voting begins:

- Position Name locked
- Election Type locked
- Winner Count locked
- Display Order locked

Only after the election ends may modifications occur.

---

# 27. Position Templates

Provide optional templates.

Examples

Student Council

↓

Automatically create

- School Pupil Leader
- Assistant School Pupil Leader
- Sports Captain
- Discipline Captain

House Election

↓

Automatically create

- House Captain
- Vice Captain
- Sports Captain

Administrators may edit templates before publishing.

---

# 28. Integration with Candidate Manager

When a new position is created:

It immediately becomes available inside the Candidate Manager Position dropdown.

Deleting a position automatically checks for assigned candidates before allowing deletion.

---

# 29. Integration with Desktop Application

The desktop application downloads:

- Position List
- Display Order
- Winner Count
- Election Type

It does not modify positions.

---

# 30. Acceptance Criteria

The Position Manager is considered complete when:

✓ Unlimited positions supported.

✓ Regular Election positions supported.

✓ House Election positions supported.

✓ Custom positions supported.

✓ Winner count configurable.

✓ Position ordering configurable.

✓ Search and filters functional.

✓ Bulk operations functional.

✓ Validation prevents invalid data.

✓ Changes require Publish Election before reaching voting nodes.

✓ Mobile remains read-only.

✓ UI is modern, responsive and professional.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

The Position Management module must preserve the simplicity of the existing desktop workflow while expanding flexibility.

Key requirements:

- House positions are **defined once** and automatically reused for Pallava, Pandya, Chera and Chola.
- The number and names of house leadership positions are fully configurable by the administrator (e.g., 2 positions one year, 3 the next).
- Position changes never affect an active election until the administrator explicitly publishes a new election version.
- The desktop voting application always treats downloaded positions as **read-only**.
- Position ordering must directly determine the sequence presented during voting.

End of Part 3B-3

# Election Management Platform SRS
# Part 3C-1 – Election Management & Publish Workflow

Version: 1.0

---

# 1. Overview

The Election Management module is the heart of the Election Management Platform.

It is responsible for creating, configuring, publishing and managing elections throughout their complete lifecycle.

Only the Website Administration Portal may create or modify elections.

Voting Nodes are strictly consumers of published election configurations.

No election data may be edited from the desktop application.

---

# 2. Design Philosophy

The Election Management system shall:

- Centralize all election configuration.
- Prevent accidental modifications during live elections.
- Support multiple election types.
- Support election versioning.
- Guarantee consistency across all voting nodes.
- Provide a predictable Publish → Download → Vote workflow.
- Require explicit administrator approval before deployment.

---

# 3. Election Lifecycle

Every election passes through the following stages.

```
Create Election

↓

Configure Election

↓

Add Positions

↓

Add Candidates

↓

Configure Houses

↓

Assign Nodes

↓

Validate Election

↓

Publish Election

↓

Nodes Download Configuration

↓

Voting Begins

↓

Voting Ends

↓

Generate Reports

↓

Clear Results (Optional)

↓

Election Archived
```

---

# 4. Election Types

The system supports two independent election types.

## Regular Election

- Uses 8 voting nodes.
- Unlimited positions.
- Unlimited candidates.
- Entire school participates.

---

## House Election

Uses 8 laptops.

Administrator preassigns every laptop.

Example

```
Node 09 → Pallava

Node 10 → Pallava

Node 11 → Pandya

Node 12 → Pandya

Node 13 → Chera

Node 14 → Chera

Node 15 → Chola

Node 16 → Chola
```

Teachers never choose the house.

Students never choose the house.

The node assignment determines the house automatically.

---

# 5. Election Dashboard

Navigation

```
Website

↓

Election Management
```

Dashboard displays:

```
Election Name

Status

Version

Created Date

Published Date

Election Type

Regular

House

Nodes Assigned

Candidates

Positions
```

---

# 6. Create Election

Administrator clicks

```
Create Election
```

Form

Fields

- Election Name
- Academic Year
- Description
- Start Date
- End Date
- Theme
- Logo
- Notes

Click

Save Draft

Election is created.

---

# 7. Draft Mode

Every election begins as a Draft.

Draft elections may be modified without restriction.

Administrator may:

- Add Candidates
- Remove Candidates
- Edit Positions
- Configure Houses
- Configure Nodes
- Upload Images
- Edit Theme
- Configure Reports

Nothing affects voting until Publish.

---

# 8. Validation

Before Publish the website validates:

✓ Election Name

✓ At least one Position

✓ Every Position has Candidates

✓ Candidate Images exist

✓ House Configuration valid

✓ Node Assignments complete

✓ Database Connected

✓ No duplicate candidates

✓ No duplicate positions

Validation failures prevent publishing.

---

# 9. Publish Workflow

Publishing requires administrator confirmation.

Workflow

```
Administrator

↓

Publish Election

↓

Run Validation

↓

Generate Configuration

↓

Increment Version

↓

Lock Draft

↓

Store Published Version

↓

Notify Nodes

↓

Success
```

Publishing never modifies votes.

Publishing only prepares the configuration.

---

# 10. Election Versioning

Every published election receives a version.

Example

```
Version 1

↓

Version 2

↓

Version 3

↓

Version 4
```

Voting nodes compare versions.

Example

```
Node Version

3

Website Version

4

↓

Download Available
```

---

# 11. Configuration Package

Publishing creates one downloadable configuration package.

Package includes:

Election Metadata

Candidates

Candidate Images

Positions

House Configuration

Display Order

Theme

Backgrounds

Election Settings

Version Information

Checksums

No votes are included.

---

# 12. Node Download Workflow

Administrator opens desktop application.

↓

Administrator Login

↓

Download Configuration

↓

Authenticate

↓

Compare Version

↓

Download

↓

Verify

↓

Replace Local Configuration

↓

Ready

The website always serves the latest published version.

---

# 13. Safe Download

Download must be transactional.

Never partially overwrite configuration.

Workflow

```
Download

↓

Verify

↓

Extract

↓

Validate

↓

Replace Existing Configuration

↓

Delete Temporary Files
```

If validation fails

↓

Rollback

---

# 14. Configuration Locking

Once an election has started:

The following become locked.

Candidates

Positions

Election Type

House Configuration

Node Assignment

Voting Theme

Only non-critical metadata may be edited.

---

# 15. Start Election

Administrator clicks

```
Start Election
```

Confirmation

```
Start Election?

This action enables voting.

Continue?

Cancel

Start
```

Status changes

Draft

↓

Published

↓

Live

---

# 16. Live Election Behaviour

While Live

Website

- Accept Votes
- Broadcast Results
- Monitor Nodes
- Generate Statistics

Desktop

- Vote
- Queue
- Synchronize

Editing is disabled.

---

# 17. End Election

Administrator clicks

```
End Election
```

Confirmation

```
End Election?

Voting will stop immediately.

Continue?
```

After ending

Nodes reject new votes.

Reports become available.

---

# 18. Clear Results

Only after election has ended.

Workflow

```
Settings

↓

Clear Election Results

↓

Warning Dialog

↓

Administrator Password

↓

Confirmation Checkbox

↓

Clear Results

↓

Success
```

Confirmation

```
WARNING

This permanently deletes all votes.

Type

CLEAR

to continue.
```

This does NOT delete:

Candidates

Images

Positions

Configuration

Only vote data.

---

# 19. Regular Election Configuration

Administrator configures

- Positions
- Candidates
- Voting Order
- Theme
- Election Logo

Unlimited positions supported.

---

# 20. House Election Configuration

Administrator configures

House Positions

Example

```
House Captain

Vice Captain

Sports Captain
```

These positions automatically exist for:

Pallava

Pandya

Chera

Chola

No duplicate configuration required.

---

# 21. Node Assignment

Every node receives

Node Name

Election Type

Assigned House

Authentication Secret

Example

```
Regular-01

Regular

-----

Regular-02

Regular

-----

House-01

Pallava

House-02

Pallava

House-03

Pandya
```

Assignments are downloaded with the configuration.

---

# 22. Publish Notification

After publishing

Website broadcasts

```
New Election Available

Version 5

Published Successfully
```

Desktop applications display

```
New Election Configuration Available.

Download Now?
```

---

# 23. Audit Logging

Log every election action.

Examples

Election Created

Election Updated

Election Published

Election Started

Election Ended

Results Cleared

Store

User

Timestamp

Browser

IP Address

Previous Value

New Value

---

# 24. Error Handling

Examples

Validation Failed

Database Offline

Publishing Failed

Download Failed

Rollback Successful

Messages must be user-friendly.

Technical logs stored separately.

---

# 25. Performance Requirements

Publish Election

< 5 seconds

Configuration Download

< 10 seconds

Validation

< 2 seconds

Version Check

< 200 ms

No noticeable delay for administrators.

---

# 26. Acceptance Criteria

The Election Management module is considered complete when:

✓ Draft mode works.

✓ Validation prevents invalid elections.

✓ Publish creates a versioned configuration package.

✓ Voting nodes detect new versions.

✓ Nodes download safely with rollback protection.

✓ Live elections cannot be modified.

✓ Regular and House elections are independently configurable.

✓ House positions are reusable across all four houses.

✓ Election lifecycle is enforced.

✓ Result clearing requires administrator confirmation and password verification.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

The Election Management module must be the **single source of truth** for the entire platform.

Key requirements:

- All election editing occurs exclusively on the website.
- Desktop voting applications never modify election data.
- Publishing is the only mechanism that distributes election changes.
- Every published configuration must have a unique version number.
- Voting nodes always operate using a fully downloaded local configuration.
- Configuration downloads must be atomic and recoverable.
- Active elections are immutable until voting ends.
- Result clearing only deletes vote data and must never remove election configuration, candidates, images or positions.

End of Part 3C-1

# Election Management Platform SRS
# Part 3C-2 – Reports & Analytics

Version: 1.0

---

# 1. Overview

The Reports & Analytics module provides administrators with comprehensive insight into the election process before, during, and after voting.

Its primary objectives are:

- Display live election statistics
- Generate official election reports
- Export reports in multiple formats
- Monitor voting trends
- Provide historical analytics
- Support election verification

Reports must always be generated from the central website database.

Voting nodes never generate official reports.

---

# 2. Design Goals

The module shall:

- Generate reports instantly
- Require no manual calculations
- Export professional documents
- Support Excel, CSV and PDF
- Display interactive charts
- Work on desktop and mobile (view-only)
- Update live while voting is in progress

---

# 3. Navigation

Website

↓

Reports & Analytics

↓

Dashboard

---

# 4. Reports Dashboard

The dashboard should present summary cards.

Example

```
--------------------------------------------------

Election

Annual Election 2027

--------------------------------------------------

Election Status

LIVE

--------------------------------------------------

Votes Received

1842

--------------------------------------------------

Turnout

92%

--------------------------------------------------

Regular Election

1260 Votes

--------------------------------------------------

House Election

582 Votes

--------------------------------------------------

Nodes Online

16 / 16

--------------------------------------------------

Pending Queue

2

--------------------------------------------------
```

Cards update automatically.

---

# 5. Report Categories

The system supports:

- Election Summary
- Regular Election Results
- House Election Results
- Position Results
- Candidate Results
- Winner Report
- Vote Distribution
- Node Activity
- Audit Report
- Synchronization Report

---

# 6. Live Analytics

During voting the dashboard displays:

Total Votes

Votes Per Minute

Votes Per Position

Votes Per House

Active Nodes

Offline Nodes

Pending Synchronization

Current Leader

These update via WebSockets.

No page refresh.

---

# 7. Regular Election Analytics

Displays

```
School Pupil Leader

John

521

Sarah

488

Kevin

127

----------------------

Sports Captain

David

612

Peter

580
```

Include:

Vote Count

Percentage

Rank

Winner Indicator

---

# 8. House Election Analytics

Administrator selects:

Pallava

↓

Dashboard

Displays

```
House Captain

Aakash

72

Rahul

64

----------------------

Vice Captain

Kiran

69

Arjun

55
```

Repeat for:

- Pallava
- Pandya
- Chera
- Chola

---

# 9. Live Charts

Interactive charts include:

- Bar Chart
- Pie Chart
- Doughnut Chart
- Line Graph
- Area Chart

Administrator may switch chart type.

Charts animate smoothly.

---

# 10. Statistics

Calculate automatically:

Total Votes

Votes Per Position

Votes Per House

Votes Per Candidate

Leading Candidate

Winning Percentage

Margin of Victory

Vote Distribution

Node Contribution

---

# 11. Node Analytics

Display:

Node Name

Votes Received

Last Vote

Synchronization Status

Average Response Time

Pending Queue

Connection Status

Example

```
Node-01

Online

248 Votes

Queue 0

---------------------

Node-02

Online

252 Votes

Queue 1
```

---

# 12. Timeline Analytics

Display voting activity.

Example

```
09:00

Voting Started

↓

09:12

200 Votes

↓

09:30

500 Votes

↓

10:15

1000 Votes
```

Timeline updates live.

---

# 13. Candidate Performance

Each candidate page displays:

Photo

Name

Position

Votes

Percentage

Rank

Leading/Trailing Status

Trend Graph

---

# 14. Position Report

Display every position.

Example

```
School Pupil Leader

Candidates

Votes

Winner

-----------------------

Sports Captain

Candidates

Votes

Winner
```

---

# 15. Winner Calculation

Automatically calculate winners.

Rules:

Highest Vote Count

↓

Winner

If multiple winners configured

↓

Top N Candidates

Tie handling:

Display tie.

Administrator resolves manually if required.

---

# 16. Report Filters

Administrator may filter by:

Election

Election Type

House

Position

Candidate

Date

Status

---

# 17. Search

Search:

Candidate

Position

Election

Node

Report

Instant filtering.

---

# 18. Export Formats

Support:

Excel (.xlsx)

CSV (.csv)

PDF (.pdf)

All exports generated directly from the website.

---

# 19. Excel Export

Excel workbook contains:

Sheet 1

Election Summary

Sheet 2

Regular Election

Sheet 3

House Election

Sheet 4

Node Statistics

Sheet 5

Audit Summary

Formatting includes:

- School Logo
- Election Name
- Date
- Auto-sized columns
- Bold headers
- Winner highlighting

---

# 20. CSV Export

CSV contains:

Election

Position

Candidate

Votes

Percentage

Winner

Timestamp

UTF-8 encoding.

---

# 21. PDF Export

Professional printable report.

Include:

Cover Page

Election Information

Results

Charts

Winners

Statistics

Signature Section

Generated Timestamp

School Logo

Suitable for official records.

---

# 22. Automatic Report Header

Every exported report displays:

School Name

Election Name

Academic Year

Generated By

Generated Date

Report Version

---

# 23. Winner Highlighting

Winners should be clearly marked.

Example

```
🥇 John

521 Votes

Winner

-------------------

Sarah

488 Votes

Runner Up
```

---

# 24. Live Refresh

While election is LIVE:

Charts update automatically.

Statistics update automatically.

Leaderboards update automatically.

No refresh button required.

---

# 25. Mobile Behaviour

Mobile users may:

View reports

View charts

View winners

Download reports (optional)

Cannot:

Delete reports

Modify reports

Change analytics settings

---

# 26. Report Permissions

Super Administrator

Full Access

Administrator

Generate Reports

Viewer

View Only

---

# 27. Report History

Maintain a history of generated reports.

Display:

Report Name

Generated By

Generated Date

Export Format

Download Again

---

# 28. Error Handling

Examples

No Data Available

Export Failed

Database Offline

PDF Generation Failed

Friendly messages only.

---

# 29. Performance Requirements

Dashboard Load

<2 Seconds

Chart Refresh

<200 ms

Excel Export

<5 Seconds

PDF Export

<8 Seconds

CSV Export

<2 Seconds

---

# 30. Future Analytics (Reserved)

Architecture should allow future addition of:

- Turnout Percentage
- Hourly Voting Trends
- AI Insights
- Predictive Graphs
- Historical Comparisons
- Multi-year Reports

These are reserved and not required for Version 1.

---

# 31. Acceptance Criteria

The Reports & Analytics module is complete when:

✓ Live statistics update automatically.

✓ Regular Election reports work.

✓ House Election reports work.

✓ Winners calculated automatically.

✓ Interactive charts available.

✓ Excel export works.

✓ CSV export works.

✓ PDF export works.

✓ Mobile supports read-only viewing.

✓ Reports include branding and timestamps.

✓ Reports generate without affecting live voting.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

The Reports & Analytics module shall be treated as the official reporting system of the Election Management Platform.

Key requirements:

- Reports are generated only from the website database.
- Voting nodes never create official reports.
- Live analytics use WebSockets for real-time updates.
- Exports must be professionally formatted for school administration.
- Excel exports shall preserve formulas where appropriate.
- PDF reports must be printable on A4 paper without layout issues.
- Report generation must never interrupt voting or synchronization.
- The module should scale to support future analytical features without redesign.

End of Part 3C-2

# Election Management Platform SRS
# Part 3C-3 – Node Monitoring & Website Settings

Version: 1.0

---

# 1. Overview

The Node Monitoring & Website Settings module is responsible for monitoring every voting node, maintaining synchronization status, managing website-wide settings, configuring database connectivity, and controlling the operational state of the Election Management Platform.

This module acts as the operational control center of the entire system.

Only authenticated administrators may access this module.

---

# 2. Objectives

The module shall:

- Monitor every voting node in real time.
- Detect offline nodes automatically.
- Display synchronization status.
- Monitor local queue sizes.
- Display latest heartbeat.
- Configure website settings.
- Configure MySQL connection.
- Manage administrator accounts.
- Configure node assignments.
- Maintain audit logs.
- Support safe maintenance operations.

---

# 3. Navigation

```
Website

↓

Settings

↓

Node Monitor
```

---

# 4. Dashboard Layout

Desktop

```
-------------------------------------------------------

Sidebar

-------------------------------------------------------

System Status Cards

-------------------------------------------------------

Node Health Table

-------------------------------------------------------

Queue Status

-------------------------------------------------------

Synchronization Timeline

-------------------------------------------------------

System Logs

-------------------------------------------------------
```

Tablet

Cards

↓

Node Table

↓

Logs

Mobile

Read Only

Cards

↓

Node List

---

# 5. System Status Cards

Display

```
Website Status

ONLINE

----------------------------

Database

CONNECTED

----------------------------

WebSocket

CONNECTED

----------------------------

Voting Nodes

16 / 16

----------------------------

Pending Votes

3

----------------------------

Election Status

LIVE
```

Cards update automatically.

---

# 6. Node Registration

Every node must have a unique identity.

Fields

- Node ID (UUID)
- Node Name
- Election Type
- Assigned House
- Secret Key
- Last Sync
- Last Heartbeat
- Status
- Software Version

---

# 7. Node Assignment

Administrator assigns each node.

Example

```
Regular-01

Regular Election

---------------------

Regular-02

Regular Election

---------------------

House-01

Pallava

---------------------

House-02

Pallava

---------------------

House-03

Pandya

---------------------

House-04

Pandya

---------------------

House-05

Chera

---------------------

House-06

Chera

---------------------

House-07

Chola

---------------------

House-08

Chola
```

This assignment is downloaded by the desktop application.

Teachers never modify this.

---

# 8. Node Health

Display

```
Node

Regular-01

----------------------

Online

YES

----------------------

Last Heartbeat

2 Seconds Ago

----------------------

Queue

0

----------------------

Last Vote

10:21 AM

----------------------

Version

1.0.2
```

---

# 9. Heartbeat

Every voting node sends a heartbeat.

Default interval

10 Seconds

Heartbeat contains

- Node ID
- Version
- Queue Size
- Last Vote Time
- Synchronization Status
- Local Database Status

---

# 10. Offline Detection

If heartbeat exceeds

30 Seconds

Status changes

ONLINE

↓

OFFLINE

Administrator receives notification.

---

# 11. Synchronization Status

Every node displays

```
Connected

YES

Pending Queue

0

Successful Sync

152

Failed Sync

0

Last Synchronization

10:23:16
```

---

# 12. Queue Monitoring

Display

Pending Votes

Failed Votes

Retry Attempts

Last Successful Upload

Queue Health

Large queues should be highlighted.

---

# 13. Version Monitoring

Display

Website Version

Desktop Version

Election Version

Configuration Version

Highlight outdated nodes.

---

# 14. Node Diagnostics

Administrator may open diagnostics.

Display

Operating System

Python Version

Application Version

Memory Usage

Disk Space

Network Status

Database Status

WebSocket Status

Queue Status

---

# 15. Remote Actions

Administrator may perform

Reconnect

Ping Node

Refresh Status

Force Sync

Download Logs

Restart Communication

These actions never interrupt voting.

---

# 16. Website Settings

Website Settings include

School Name

School Logo

Election Logo

Theme

Primary Color

Secondary Color

Footer Text

Timezone

Language (future)

---

# 17. Theme Management

Support

Light Theme

Dark Theme

School Branding

Theme updates affect:

Dashboard

Reports

Login Page

Candidate Preview

---

# 18. Database Settings

Administrator may configure

Host

Port

Database

Username

Password

Buttons

Test Connection

Save

Reconnect

Reset

No website restart required.

---

# 19. Desktop Database Configuration

The desktop application also provides its own database configuration.

These settings are completely independent from the website settings.

The website never modifies desktop database credentials.

---

# 20. User Management

Administrator can

Create User

Edit User

Disable User

Reset Password

Assign Role

Available Roles

- Super Administrator
- Administrator
- Viewer

---

# 21. Password Policy

Minimum

8 Characters

Require

Uppercase

Lowercase

Number

Special Character

Passwords stored using bcrypt or Argon2.

---

# 22. Audit Logs

Every administrative action is recorded.

Examples

Login

Logout

Candidate Created

Candidate Deleted

Election Published

Results Cleared

Database Updated

Node Assignment Changed

---

# 23. Audit Log Information

Every entry stores

Timestamp

User

IP Address

Browser

Action

Module

Old Value

New Value

---

# 24. Search Logs

Administrator may search by

User

Node

Action

Date

Election

---

# 25. Website Maintenance

Maintenance Mode

When enabled

Administrators may continue working.

Voting nodes continue synchronizing.

Viewer accounts receive

```
System Maintenance

Please check again later.
```

Voting must never stop because maintenance mode is enabled.

---

# 26. Backup Settings

Administrator may manually create

Database Backup

Configuration Backup

System Backup

Automatic daily backups should be configurable.

---

# 27. Restore

Administrator may restore

Configuration

Database

Theme

Settings

Confirmation required.

---

# 28. Security Settings

Configure

Session Timeout

JWT Expiry

Password Policy

Maximum Login Attempts

Node Authentication Secret

WebSocket Security

---

# 29. Notifications

Administrator receives notifications for

Node Offline

Node Online

Synchronization Failure

Database Failure

Publish Success

Download Success

Election Started

Election Ended

Backup Completed

---

# 30. Clear Election Results

Navigation

Settings

↓

Election Maintenance

↓

Clear Results

Workflow

```
Administrator

↓

Warning

↓

Enter Password

↓

Type

CLEAR

↓

Verify

↓

Delete Vote Data

↓

Complete
```

Only vote data is removed.

Candidates

Images

Positions

Election Configuration

Node Assignments

remain unchanged.

---

# 31. Mobile Behaviour

Mobile devices

Read Only

Can view

Dashboard

Node Health

Election Status

Live Results

Cannot

Edit Settings

Modify Database

Assign Nodes

Create Users

Delete Results

Publish Elections

---

# 32. Performance Requirements

Heartbeat Update

<200 ms

Node Refresh

Instant

Dashboard Load

<2 Seconds

Settings Save

<500 ms

Database Test

<3 Seconds

---

# 33. Error Handling

Examples

Database Connection Failed

Node Timeout

Synchronization Error

Heartbeat Lost

Authentication Failed

Friendly messages only.

Technical information stored in logs.

---

# 34. Acceptance Criteria

The Node Monitoring & Website Settings module is complete when

✓ All 16 voting nodes are monitored.

✓ Heartbeats update automatically.

✓ Offline detection works.

✓ Queue monitoring works.

✓ Synchronization status updates live.

✓ Node assignments are configurable.

✓ Website database settings are editable.

✓ Desktop database settings remain independent.

✓ User management functions correctly.

✓ Audit logs record every administrative action.

✓ Maintenance mode does not interrupt voting.

✓ Result clearing requires password verification.

✓ Mobile devices remain read-only.

---

# IMPORTANT IMPLEMENTATION REQUIREMENTS

This module serves as the operational control center of the Election Management Platform.

The following requirements are mandatory:

- Every voting node must have a persistent UUID and authentication secret.
- Heartbeats must use WebSockets where available and fall back to HTTP if necessary.
- Node status changes (online/offline) must appear on the dashboard within seconds.
- Website and desktop MySQL configurations are completely separate and independently configurable.
- Maintenance mode must never prevent voting nodes from synchronizing votes.
- All destructive operations (clearing results, restoring backups, deleting users) require explicit confirmation and administrator password verification.
- Audit logs are immutable and cannot be edited or deleted through the interface.
- All settings changes take effect immediately where possible without requiring server restarts.

---

# 35. Version 1 Completion Checklist

Before deployment, verify:

✓ Website accessible globally (via free deployment solution such as Cloudflare Tunnel initially)

✓ Administrator login functional

✓ Dashboard responsive on desktop and mobile

✓ All 16 nodes register correctly

✓ Heartbeats received

✓ Live synchronization operational

✓ Election publishing functional

✓ Configuration download functional

✓ Reports export correctly (Excel, CSV, PDF)

✓ Result clearing protected

✓ Audit logging enabled

✓ Cross-platform desktop application tested on Windows, macOS, and Linux

✓ Mobile devices display live results in read-only mode

---

End of Part 3C-3