---
name: منطوق
description: Arabic-first local voice workbench
colors:
  accent: "#111111"
  canvas: "#ffffff"
  sheet: "#ffffff"
  editor: "#f6f6f4"
  ink: "#171717"
  muted-ink: "#666666"
  rule: "#e2e2de"
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

**Creative North Star: "Arabic type studio in the منفذ visual family"**

A white, quiet writing space puts Arabic text at the center of voice generation. The writing sheet and playback area share one outlined surface. Controls stay familiar and secondary settings recede into popovers. The footer carries the منفذ mark and product attribution.

## Colors

White and warm off-white surfaces establish the workspace. Charcoal ink carries text and primary actions; pale gray rules separate regions. Focus and selection use the same monochrome palette as the Hermes site.

## Typography

Bundled Thmanyah is the Arabic interface face, including labels and headings. The compact title and small section headings keep the writing field as the dominant area. API keys and voice identifiers read left-to-right.

## Layout

The main content is capped at 1100px. A sticky header carries the brand, a short product descriptor, and the API-key control, then workflow tabs lead into a single sheet. On desktop the editor sits to the right of playback; at 640px and below the regions stack with writing first. Voice and action stay close to the editor, while seed controls open on demand. A ruled footer holds the product name, منفذ logo and attribution, and copyright; its columns stack on mobile.

## Elevation & Depth

The sheet uses a fine border without a shadow. Its playback area is separated by a matching rule, not a second card.

## Shapes

The sheet uses a gently curved 10px edge. Inputs and V2 controls keep their native corner language.

## Components

The text editor uses native Streamlit for a reliable tall multiline writing area. Shadcn V2 supplies workflow tabs, voice selection, and actions; native Streamlit supplies the key field, popovers, uploads, audio playback, and download. The result shows a short empty-state line until generated audio replaces it.

## Do's and Don'ts

- **Do** preserve Arabic RTL and the Thmanyah font throughout the workspace.
- **Do** keep generation, listening, and downloading within one visible task surface.
- **Don't** spread seed controls or explanatory paragraphs across the main workflow.
