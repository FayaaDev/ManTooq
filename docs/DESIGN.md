---
name: منطوق
description: Arabic-first local voice workbench
colors:
  accent: "#2254b4"
  canvas: "#eaf0f3"
  sheet: "#ffffff"
  editor: "#f7f9fa"
  ink: "#172c3a"
  muted-ink: "#536977"
  rule: "#dce5ea"
typography:
  title:
    fontFamily: "Thmanyah, sans-serif"
    fontSize: "1.65rem"
    fontWeight: 700
    lineHeight: 1.45
  body:
    fontFamily: "Thmanyah, sans-serif"
    fontWeight: 700
rounded:
  sheet: "12px"
---

# Design System: منطوق

## Overview

**Creative North Star: "Arabic type studio"**

A cool, quiet writing space puts Arabic text at the center of voice generation. The writing sheet separates the task from the surrounding canvas; the playback area belongs to the same surface. Controls stay familiar and secondary settings recede into popovers.

## Colors

The cool canvas and white sheet establish the workspace. Dark ink carries text; mineral-blue rules separate regions; the accent colors links, focus, and selection. Shadcn V2 primary actions retain their dark native treatment.

## Typography

Bundled Thmanyah is the Arabic interface face, including labels and headings. The compact title and small section headings keep the writing field as the dominant area. API keys and voice identifiers read left-to-right.

## Layout

The main content is capped at 1200px. A compact brand/key row leads into workflow tabs, then a single sheet. On desktop the editor sits to the right of playback; at 640px and below the regions stack with writing first. Voice and action stay close to the editor, while seed controls open on demand.

## Elevation & Depth

The sheet has one soft ambient shadow (`0 16px 45px rgba(28, 53, 70, .08)`). Its playback area is separated by a fine rule, not a second card.

## Shapes

The sheet uses a gently curved 12px edge. Inputs and V2 controls keep their native corner language.

## Components

The text editor uses native Streamlit for a reliable tall multiline writing area. Shadcn V2 supplies workflow tabs, voice selection, and actions; native Streamlit supplies the key field, popovers, uploads, audio playback, and download. The result shows a short empty-state line until generated audio replaces it.

## Do's and Don'ts

- **Do** preserve Arabic RTL and the Thmanyah font throughout the workspace.
- **Do** keep generation, listening, and downloading within one visible task surface.
- **Don't** spread seed controls or explanatory paragraphs across the main workflow.
