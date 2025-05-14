import { serve } from 'https://deno.land/std@0.199.0/http/server.ts'

serve(async (req: Request) => {
  const { text } = await req.json()

  const openaiRes = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
    },
    body: JSON.stringify({
      input: text,
      model: 'text-embedding-3-small'   // or 'text-embedding-ada-002'
    }),
  }).then(r => r.json())

  return new Response(
    JSON.stringify({ embedding: openaiRes.data[0].embedding }),
    { headers: { 'Content-Type': 'application/json' } },
  )
})
