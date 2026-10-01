// Cloudflare Worker: forwards food-photo analysis requests to the Anthropic
// API so the API key never ships inside the app.
//
// Deploy:  npx wrangler deploy backend/worker.js --name sura-ai
// Secret:  npx wrangler secret put ANTHROPIC_API_KEY
// Then build the app with --dart-define=AI_PROXY_URL=https://sura-ai.<you>.workers.dev

const ALLOWED_MODELS = new Set(['claude-sonnet-5-5', 'claude-haiku-4-5-20251001']);
const MAX_BODY = 6 * 1024 * 1024;

export default {
  async fetch(req, env) {
    if (req.method !== 'POST') return new Response('Method not allowed', { status: 405 });
    const raw = await req.text();
    if (raw.length > MAX_BODY) return new Response('Too large', { status: 413 });

    let body;
    try { body = JSON.parse(raw); } catch { return new Response('Bad JSON', { status: 400 }); }
    if (!ALLOWED_MODELS.has(body.model)) return new Response('Model not allowed', { status: 400 });
    body.max_tokens = Math.min(body.max_tokens ?? 2048, 2048);

    // Optional: add per-device rate limiting with KV / Durable Objects here.
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify(body),
    });
    return new Response(res.body, { status: res.status, headers: { 'content-type': 'application/json' } });
  },
};
