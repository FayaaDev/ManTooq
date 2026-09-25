const VOICES = new Set(['cFUFIbKkO2iZFwS8cRnY', 't9akNmCDhz230CEXOYmn', 'T9KaXxyeFWyP8DFgs9bx', 'ckaeRWMtCV0u0pUT3wX1', 'kr4VZw8MSZMHE0y2m40n']);
const DAY = 86400;

async function signature(secret, value) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return [...new Uint8Array(await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(value)))].map((byte) => byte.toString(16).padStart(2, '0')).join('');
}

function error(status, message) {
  return Response.json({ error: message }, { status, headers: { 'Cache-Control': 'no-store' } });
}

export async function onRequestPost({ request, env }) {
  if (!env.DEMO_DB || !env.DEMO_SECRET || !env.DEMO_ELEVENLABS_API_KEY) return error(503, 'التجربة غير متاحة الآن.');
  if (request.headers.get('Origin') !== new URL(request.url).origin || request.headers.get('Content-Type')?.split(';')[0] !== 'application/json') {
    return error(403, 'طلب غير مسموح.');
  }
  const ip = request.headers.get('CF-Connecting-IP');
  if (!ip) return error(403, 'تعذّر التحقق من الطلب.');
  const now = Math.floor(Date.now() / 1000);
  const cookie = request.headers.get('Cookie')?.match(/(?:^|;\s*)mantooq_demo=(\d+)\.([a-f0-9]{64})(?:;|$)/);
  if (cookie && Number(cookie[1]) + DAY > now && cookie[2] === await signature(env.DEMO_SECRET, `cookie:${cookie[1]}`)) {
    return error(429, 'استخدمت التجربة. جرّب مجددًا بعد 24 ساعة أو أضف مفتاحك.');
  }

  if (Number(request.headers.get('Content-Length')) > 4096) return error(400, 'النص طويل جدًا.');
  let input;
  try {
    const body = await request.text();
    if (body.length > 4096) return error(400, 'النص طويل جدًا.');
    input = JSON.parse(body);
  } catch { return error(400, 'طلب غير صالح.'); }
  const text = typeof input?.text === 'string' ? input.text.trim() : '';
  if (!text || text.length > 250 || !VOICES.has(input.voice)) return error(400, 'أدخل نصًا لا يتجاوز 250 حرفًا واختر صوتًا متاحًا.');

  const ipHash = await signature(env.DEMO_SECRET, `ip:${ip}`);
  const claim = crypto.randomUUID();
  const reservation = await env.DEMO_DB.prepare(
    'INSERT INTO demo_uses (ip_hash, expires, claim) VALUES (?, ?, ?) ON CONFLICT(ip_hash) DO UPDATE SET expires = excluded.expires, claim = excluded.claim WHERE demo_uses.expires <= ?'
  ).bind(ipHash, now + DAY, claim, now).run();
  if (reservation.meta.changes !== 1) return error(429, 'استخدمت التجربة من هذه الشبكة. جرّب مجددًا بعد 24 ساعة أو أضف مفتاحك.');

  try {
    const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${input.voice}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: { 'xi-api-key': env.DEMO_ELEVENLABS_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, model_id: 'eleven_v3', voice_settings: { stability: 0.7, similarity_boost: 0.9, use_speaker_boost: true, style: 0, speed: 0.95 }, seed: 2752657480 }),
    });
    if (!response.ok) throw new Error('ElevenLabs request failed');
    const audio = await response.arrayBuffer();
    if (!audio.byteLength) throw new Error('Empty audio');
    const stamp = String(now);
    return new Response(audio, { headers: {
      'Content-Type': 'audio/mpeg',
      'Cache-Control': 'no-store',
      'Set-Cookie': `mantooq_demo=${stamp}.${await signature(env.DEMO_SECRET, `cookie:${stamp}`)}; Max-Age=${DAY}; Path=/api/demo; HttpOnly; Secure; SameSite=Lax`,
    } });
  } catch {
    await env.DEMO_DB.prepare('DELETE FROM demo_uses WHERE ip_hash = ? AND claim = ?').bind(ipHash, claim).run();
    return error(502, 'تعذّر توليد الصوت التجريبي. حاول مجددًا لاحقًا.');
  }
}
