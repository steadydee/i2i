# … earlier imports & helper functions unchanged …

    def get_relevant_documents(self, query: str):
        rows = search(self.table, query, self.k, self.filters)
        return [
            Document(
                page_content=r.get("content") or r.get("text", ""),
                metadata=r
            )
            for r in rows
        ]
