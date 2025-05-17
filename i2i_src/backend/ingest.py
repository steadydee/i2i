# (keep file header the same)

# inside _upsert_chunks
        rows.append(
            {
                "chunk_id":  f"{doc_id}_{idx}",
                "tenant_id": TENANT_ID,
                "doc_id":    doc_id,
                "content":   txt,          # <-- fixed key
                "embedding": _embed(txt),
                "metadata":  json.dumps({}),
            }
        )

# rest of file unchanged
