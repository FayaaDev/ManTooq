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

test('demo key stays server-side; cookie and IP allow one success then block', async () => {
  const { request } = setup();
  let calls = 0;
  globalThis.fetch = async (_url, options) => {
    calls++;
    assert.equal(options.headers['xi-api-key'], 'server-only-test-key');
    assert.equal(JSON.parse(options.body).text, 'مرحبًا');
    assert.equal(JSON.parse(options.body).model_id, 'eleven_v4_turbo');
    assert.deepEqual(JSON.parse(options.body).voice_settings, { stability: 0.7, similarity_boost: 0.9 });
    return new Response(new Uint8Array([73, 68, 51]), { status: 200 });
  };
  const first = await request();
  assert.equal(first.status, 200);
  assert.equal(first.headers.get('Cache-Control'), 'no-store');
  assert.equal(first.headers.get('Content-Type'), 'audio/mpeg');
  const cookie = first.headers.get('Set-Cookie');
  assert.match(cookie, /HttpOnly; Secure; SameSite=Lax/);
  const denied = await request('192.0.2.2', cookie.split(';')[0]);
  assert.equal(denied.status, 429);
  assert.match((await denied.json()).error, /محاولتك التجريبية/);
  assert.equal((await request()).status, 429);
  assert.equal(calls, 1);
  assert.equal((await request('192.0.2.2')).status, 200);
});

test('Moteb uses v4 turbo with its approved voice settings', async () => {
  const { request } = setup();
  let payload;
  globalThis.fetch = async (url, options) => {
    assert.equal(url, 'https://api.elevenlabs.io/v1/text-to-speech/s8AtpE08HrPmTUNmxgfQ?output_format=mp3_44100_128');
    payload = JSON.parse(options.body);
    return new Response(new Uint8Array([1]));
  };
  assert.equal((await request('192.0.2.1', '', { text: 'test', voice: 's8AtpE08HrPmTUNmxgfQ' })).status, 200);
  assert.equal(payload.model_id, 'eleven_v4_turbo');
  assert.deepEqual(payload.voice_settings, { stability: 0.5, similarity_boost: 0.75 });
  assert.equal(payload.seed, 2752657480);
});

test('rejects invalid inputs before reserving; failed provider call releases claim', async () => {
  const { request, uses } = setup();
  globalThis.fetch = async () => new Response('failure', { status: 500 });
  assert.equal((await request('192.0.2.3', '', { text: 'x', voice: 'arbitrary-voice' })).status, 400);
  assert.equal((await request('192.0.2.3', '', { text: 'x'.repeat(51), voice: 'cFUFIbKkO2iZFwS8cRnY' })).status, 400);
  assert.equal(uses.size, 0);
  assert.equal((await request()).status, 502);
  assert.equal(uses.size, 0);
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  assert.equal((await request()).status, 200);
});

test('accepts 50 characters and rejects 51', async () => {
  const { request } = setup();
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  const voice = 'cFUFIbKkO2iZFwS8cRnY';
  assert.equal((await request('192.0.2.4', '', { text: 'x'.repeat(51), voice })).status, 400);
  assert.equal((await request('192.0.2.4', '', { text: 'x'.repeat(50), voice })).status, 200);
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

test('a failed attempt releases its slot', async () => {
  const { request, uses } = setup();
  globalThis.fetch = async () => new Response('failure', { status: 500 });
  assert.equal((await request()).status, 502);
  assert.equal(uses.size, 0);
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  assert.equal((await request()).status, 200);
  assert.equal((await request()).status, 429);
});

test('legacy one-use cookies are blocked', async () => {
  const { request } = setup();
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  const first = await request();
  const stamp = first.headers.get('Set-Cookie').split('=')[1].split('.')[0];
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode('test-signing-secret'), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const signed = [...new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(`cookie:${stamp}`)))].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  const cookie = `mantooq_demo=${stamp}.${signed}`;
  assert.equal((await request('192.0.2.2', cookie)).status, 429);
});

test('simultaneous requests from one IP make at most one upstream call', async () => {
  const { request } = setup();
  let calls = 0;
  globalThis.fetch = async () => { calls++; return new Response(new Uint8Array([1])); };
  const results = await Promise.all([request(), request(), request(), request(), request()]);
  assert.deepEqual(results.map((result) => result.status).sort(), [200, 429, 429, 429, 429]);
  assert.equal(calls, 1);
});

test('cookie and IP allowance expire after 24 hours', async () => {
  const clock = Date.now;
  const { request } = setup();
  globalThis.fetch = async () => new Response(new Uint8Array([1]));
  try {
    Date.now = () => 1_700_000_000_000;
    const response = await request('192.0.2.1');
    assert.equal(response.status, 200);
    const cookie = response.headers.get('Set-Cookie').split(';')[0];
    assert.equal((await request('192.0.2.1', cookie)).status, 429);
    Date.now = () => 1_700_086_400_000;
    assert.equal((await request('192.0.2.1', cookie)).status, 200);
  } finally { Date.now = clock; }
});
