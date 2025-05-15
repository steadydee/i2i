#!/usr/bin/env bash
# test_vector_wrapper.sh
# Verifies that the search_vector_chunks wrapper works end-to-end.

set -euo pipefail

# --- Load Supabase creds (.env must export SUPABASE_URL and SUPABASE_ANON_KEY) ---
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env
fi

: "${SUPABASE_URL:?Need SUPABASE_URL in env}"
: "${SUPABASE_ANON_KEY:?Need SUPABASE_ANON_KEY in env}"

QUERY_TEXT="paid holidays"
K=5
TENANT="default"
DOC_ID=""          # set to your doc_id or leave blank

# --- 1) Get embedding via Edge Function /embed ----------------------------------
EMBED=$(curl -s \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"${QUERY_TEXT}\"}" \
  "${SUPABASE_URL}/functions/v1/embed" | jq -c '.embedding')

# --- 2) Call search_vector_chunks through PostgREST ----------------------------
JSON_PAYLOAD=$(jq -nc \
  --argjson q_vec "$EMBED" \
  --arg     tenant "$TENANT" \
  --argjson k "$K" \
  --arg     p_doc_id "$DOC_ID" \
  '{
      q_vec: $q_vec,
      k: $k,
      tenant: $tenant
    } + ( $p_doc_id | select(. != "") | {p_doc_id: .} )')

echo "Calling search_vector_chunks with payload:"
echo "$JSON_PAYLOAD" | jq

curl -s \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" \
  "${SUPABASE_URL}/rest/v1/rpc/search_vector_chunks" | jq
