from langchain_core.runnables import RunnableLambda

# Very simple stub: just echo what came in
docx_render_stub = RunnableLambda(
    lambda inputs: f"(docx_render_stub) fields={inputs}"
)
