---
name: daggerheart-document-workflow
description: End-to-end workflow for converting English Daggerheart documents into translated Markdown and structured JSON.
---

# Daggerheart Document Workflow Skill

You are an orchestration skill for Daggerheart document conversion. Your job is to turn English source documents into two deliverables when applicable: a translated markdown file and structured JSON for supported card and entity types.

This skill coordinates three stages:

1. Source conversion with Marker.
2. Translation with the Daggerheart translator skill.
3. JSON structuring with the Daggerheart JSON formatter skill.

## Input Routing

Detect the source type first:

- For `.pdf`, `.doc`, `.docx`, image files, and other marker-supported document formats, convert the source to markdown with Marker first.
- For `.txt` and `.md`, skip Marker and treat the file as the source markdown directly.

## Marker Stage

When conversion is needed, use Marker through a local uv virtual environment.

## Workspace Environment

In this workspace, prefer the existing virtual environment at `D:\Fish\TRPG\DaggerHeart_Homebrew\.venv` instead of rebuilding it. It is a Windows Python 3.12.12 environment and already includes the Marker command-line tools, including `marker.exe`, `marker_extract.exe`, `marker_gui.exe`, and `marker_server.exe`.

If that environment needs to be refreshed, it can be copied from `D:\Fish\TRPG\DaggerHeart_CN\.venv` as long as both environments remain on Python 3.12.x. Validate the copied environment by running `D:\Fish\TRPG\DaggerHeart_Homebrew\.venv\Scripts\marker.exe --help` before using it for document conversion.

Required setup:

1. Create an isolated venv with `uv`.
2. Install `marker-pdf[full]` in that venv.
3. Prefer Python 3.10 to 3.13 on Windows.
4. Avoid Python 3.14 for this workflow, because Pillow 10.4.0 can fail to build from source and Marker may fail before conversion starts.

Recommended recovery path if Pillow build fails:

1. Recreate the venv with Python 3.13 or 3.12.
2. Reinstall `marker-pdf[full]`.
3. Retry the conversion.

Marker output should be saved as intermediate markdown, preserving images, tables, headings, equations, and lists as much as possible.

## Translation Stage

After Marker or direct markdown input, hand the content to the Daggerheart translator skill.

Mandatory translation behavior:

- Preserve the original markdown structure.
- Translate faithfully into Chinese.
- Keep official Daggerheart terminology consistent.
- For long documents, split into explicit sequential chunks before translation.
- Never rely on a single pass when the text is large enough to risk truncation.
- Reassemble the translated chunks in source order.

After translation, run `../daggerheart-translator/scripts/makeup.py` on the translated markdown to normalize formatting and term presentation.

## JSON Stage

If the translated content contains supported structured entities such as enemies, environments, domain cards, weapons, armor, communities, ancestries, classes, or subclasses, pass the translated markdown to the Daggerheart JSON formatter skill.

Formatting rules:

- Use the exact template for the detected entity type.
- Preserve source order when multiple entities appear.
- Output one JSON object for a single entity, or a JSON array for multiple entities.
- Do not invent fields for unsupported content.
- If the source is mostly rules, lore, setting text, or other non-card prose, keep it as translated markdown and do not force it into a card schema.

## Extensibility

This workflow is intentionally open-ended. It should work well for structured card-like content today, but it must also leave room for future templates covering rules, background lore, equipment, or other Daggerheart resource types.

The key principle is:

- Translate first, structure second, and only structure when a fitting template exists.