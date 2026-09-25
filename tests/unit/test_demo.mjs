import assert from 'node:assert/strict';
import { after, test } from 'node:test';
import { onRequestPost } from '../../functions/api/demo.js';

const originalFetch = globalThis.fetch;
after(() => { globalThis.fetch = originalFetch; });

function setup() {
  const uses = new Map();
  const env = {
    DEMO_SECRET: 'test-signing-secret',
    DEMO_ELEVENLABS_API_KEY: 'server-only-test-key',
    DEMO_DB: {
      prepare(sql) {
        return { bind(...values) {
          return { async run() {
            const [ip, expires, claim, now] = values;
            if (sql.startsWith('DELETE')) return { meta: { changes: Number(uses.delete(ip)) } };
            if (uses.has(ip) && uses.get(ip).expires > now) return { meta: { changes: 0 } };
            uses.set(ip, { expires, claim });
            return { meta: { changes: 1 } };
          } };
        } };
      },
    },
  };
  const request = (ip = '192.0.2.1', cookie = '', body = { text: 'مرحبًا', voice: 'cFUFIbKkO2iZFwS8cRnY' }) => onRequestPost({
    env,
    request: new Request('https://example.com/api/demo', {
      method: 'POST',
      headers: { Origin: 'https://example.com', 'CF-Connecting-IP': ip, 'Content-Type': 'application/json', ...(cookie && { Cookie: cookie }) },
      body: JSON.stringify(body),
    }),
  });
  return { request, uses };
}

test('demo key stays server-side; cookie and IP both block repeats for 24 hours', async () => {
  const { request } = setup();
  let calls = 0;
  globalThis.fetch = async (_url, options) => {
    calls++;
    assert.equal(options.headers['xi-api-key'], 'server-only-test-key');
    assert.equal(JSON.parse(options.body).text, 'مرحبًا');
    return new Response(new Uint8Array([73, 68, 51]), { status: 200 });
  };
  const first = await request();
  assert.equal(first.status, 200);
  assert.equal(first.headers.get('Cache-Control'), 'no-store');
  assert.equal(first.headers.get('Content-Type'), 'audio/mpeg');
  const cookie = first.headers.get('Set-Cookie');
  assert.match(cookie, /HttpOnly; Secure; SameSite=Lax/);
  assert.equal((await request('192.0.2.2', cookie.split(';')[0])).status, 429);
  assert.equal((await request()).status, 429);
  assert.equal(calls, 1);
  assert.equal((await request('192.0.2.2')).status, 200);
});

test('rejects invalid inputs before reserving; failed provider call releases claim', async () => {
  const { request, uses } = setup();
  globalThis.fetch = async () => new Response('failure', { status: 500 });
  assert.equal((await request('192.0.2.3', '', { text: 'x', voice: 'arbitrary-voice' })).status, 400);
  assert.equal((await request('192.0.2.3', '', { text: 'x'.repeat(251), voice: 'cFUFIbKkO2iZFwS8cRnY' })).status, 400);
  assert.equal(uses.size, 0);
  assert.equal((await request()).status, 502);
  assert.equal(uses.size, 0);
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  assert.equal((await request()).status, 200);
});

test('logs demo outcomes without text, IP, cookie, or API key', async () => {
  const { request } = setup();
  const originalLog = console.log;
  const logs = [];
  console.log = (line) => logs.push(JSON.parse(line));
  try {
    globalThis.fetch = async () => new Response('failure', { status: 500 });
    assert.equal((await request('192.0.2.9', '', { text: 'private text', voice: 'invalid' })).status, 400);
    assert.equal((await request()).status, 502);
    globalThis.fetch = async () => new Response(new Uint8Array([1]));
    assert.equal((await request()).status, 200);
    assert.equal((await request()).status, 429);
    assert.deepEqual(logs, [
      { event: 'demo', outcome: 'denied', reason: 'invalid_input', status: 400 },
      { event: 'demo', outcome: 'error', reason: 'generation_failed', status: 502 },
      { event: 'demo', outcome: 'success', status: 200 },
      { event: 'demo', outcome: 'denied', reason: 'ip_limit', status: 429 },
    ]);
    assert.doesNotMatch(JSON.stringify(logs), /private text|192\.0\.2|server-only-test-key|mantooq_demo/);
  } finally { console.log = originalLog; }
});

test('simultaneous requests from one IP make one upstream call', async () => {
  const { request } = setup();
  let calls = 0;
  globalThis.fetch = async () => { calls++; return new Response(new Uint8Array([1])); };
  const results = await Promise.all([request(), request()]);
  assert.deepEqual(results.map((result) => result.status).sort(), [200, 429]);
  assert.equal(calls, 1);
});

test('cookie and IP allowance expire after 24 hours', async () => {
  const clock = Date.now;
  const { request } = setup();
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  try {
    Date.now = () => 1_700_000_000_000;
    const first = await request();
    const cookie = first.headers.get('Set-Cookie').split(';')[0];
    assert.equal((await request('192.0.2.1', cookie)).status, 429);
    Date.now = () => 1_700_086_400_000;
    assert.equal((await request('192.0.2.1', cookie)).status, 200);
  } finally { Date.now = clock; }
});
