# استوديو الصوت العربي

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Individual creators making Arabic voiceovers locally with their own ElevenLabs API key. They generate speech from Arabic text and may clone a voice they have permission to use.

## Product Purpose

Turn Arabic text into playable, downloadable MP3 audio using a saved clone or an ElevenLabs library voice. Optionally clone a voice from an uploaded recording.

## Positioning

A focused Arabic-first local workflow combines voice cloning, speech generation, and saved outputs in one place.

## Operating Context

Creators run the Streamlit app on their own computer or use its CLI. They supply an ElevenLabs API key, choose a saved clone or a library voice ID, enter Arabic text, then listen to or download the resulting MP3. They can save generated recordings and reuse speech seeds locally. Internet access and an ElevenLabs account are required; ElevenLabs usage may incur charges.

## Capabilities and Constraints

The app runs in Streamlit, with a Python CLI. Users may enter their own API key or supply it through a local `.env` file. A cloned voice ID, seeds, and generated audio are saved on the local machine; local voice storage is shared across sessions on the same installation, not per-user accounts. Voice cloning requires a recording the user has the right to clone.

## Brand Commitments

Keep the name «استوديو الصوت العربي» and the bundled Thmanyah Arabic font. Use Arabic and RTL for the interface; keep API keys and voice IDs readable left-to-right.

## Evidence on Hand

The working Streamlit app and CLI are in `app/`; setup and workflows are documented in `docs/README.md`. Automated tests in `tests/` use a fake ElevenLabs client. No customer testimonials or usage metrics are documented.

## Product Principles

- Let creators reach text-to-audio generation quickly, with cloning available when needed.
- Keep output immediately playable, downloadable, and available in local history.
- Make local storage and user-supplied ElevenLabs access clear.

## Accessibility & Inclusion

The interface is Arabic and right-to-left; API keys and voice IDs read left-to-right.
