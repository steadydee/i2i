from backend.helpers.echo import repeat as echo_repeat
from backend.helpers.policy_qna import run as policy_qna_run
from backend.helpers.sow_draft import generate as sow_draft_generate

helpers_registry = {
    "echo_chain": echo_repeat,
    "policy_qna_chain": policy_qna_run,
    "doc_draft_chain": sow_draft_generate,
}
