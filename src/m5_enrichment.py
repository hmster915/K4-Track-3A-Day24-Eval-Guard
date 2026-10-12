"""Day24 contextual enrichment: prepend source/title/version/section, preserving facts."""
from dataclasses import dataclass


@dataclass
class EnrichedChunk:
    enriched_text: str
    auto_metadata: dict


def enrich_chunks(chunks: list[dict]) -> list[EnrichedChunk]:
    enriched = []
    for chunk in chunks:
        meta = chunk["metadata"]
        context = " | ".join(str(meta[key]) for key in ("source", "title", "version", "section")
                             if meta.get(key))
        # Only corpus metadata is prepended; no generated questions or invented policy facts.
        text = f"Nguồn: {context}\n{chunk['text']}" if context else chunk["text"]
        enriched.append(EnrichedChunk(text, {"enrichment_method": "contextual_metadata"}))
    return enriched
