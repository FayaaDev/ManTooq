const $ = (id) => document.getElementById(id);
const DEFAULT_SEED = 2752657480;
const STORAGE = { key: 'mantooq:key', voice: 'mantooq:voice', seeds: 'mantooq:seeds' };
const settings = { stability: 0.7, similarity_boost: 0.9, use_speaker_boost: true, style: 0, speed: 0.95 };
let playerUrl;
let recordingUrls = [];
let demoMode = false;

function message(id, text, error = false) {
  const element = $(id);
  element.textContent = text;
  element.classList.toggle('error', error);
  element.hidden = !text;
}

function apiKey() { return localStorage.getItem(STORAGE.key) || ''; }
function voiceId() { return localStorage.getItem(STORAGE.voice) || ''; }

function seeds() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE.seeds) || '[]');
    return [DEFAULT_SEED, ...stored.filter((seed) => Number.isInteger(seed) && seed >= 0 && seed <= 4294967295)]
      .filter((seed, index, values) => values.indexOf(seed) === index);
  } catch { return [DEFAULT_SEED]; }
}

function saveSeed(seed) {
  localStorage.setItem(STORAGE.seeds, JSON.stringify([seed, ...seeds().filter((item) => item !== seed)].slice(0, 20)));
  renderSeeds();
}

function renderSeeds() {
  const select = $('saved-seeds');
  select.replaceChildren(...seeds().map((seed) => new Option(String(seed), String(seed))));
  select.value = $('seed').value;
}

function renderVoice() {
  const saved = voiceId();
  const source = document.querySelector('input[name="voice-source"]:checked').value;
  const text = $('speech-text');
  if (demoMode) text.maxLength = 250;
  else text.removeAttribute('maxlength');
  $('demo-text-count').hidden = !demoMode;
  $('demo-text-count').textContent = `${text.value.length} / 250 حرفًا`;
  $('library-fields').hidden = source !== 'library';
  $('selected-fields').hidden = source !== 'selected';
  $('saved-voice-hint').hidden = source !== 'saved' || !!saved;
  $('cloned-id').textContent = saved;
  $('cloned-id').hidden = !saved;
  document.querySelector('.seed-settings').hidden = demoMode;
  $('speech-note').textContent = demoMode
    ? 'التجربة: 250 حرفًا كحد أقصى، بصوت مختار واحد كل 24 ساعة لكل متصفح وشبكة.'
    : !apiKey()
    ? 'أضف مفتاح API من أعلى الصفحة قبل التوليد.'
    : source === 'saved' && !saved
      ? 'استنسخ صوتك أو اختر صوتًا من المكتبة.'
      : 'يُرسل النص إلى ElevenLabs عند التوليد، وقد تُحتسب تكلفة الاستخدام.';
}

function openRecordings() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('mantooq-recordings', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('recordings', { keyPath: 'id' });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function recordingsRequest(mode, operation) {
  const db = await openRecordings();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction('recordings', mode);
      const request = operation(tx.objectStore('recordings'));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
      tx.onerror = () => reject(tx.error);
    });
  } finally { db.close(); }
}

async function renderHistory() {
  recordingUrls.forEach(URL.revokeObjectURL);
  recordingUrls = [];
  const list = $('recordings');
  list.replaceChildren();
  try {
    const recordings = await recordingsRequest('readonly', (store) => store.getAll());
    recordings.sort((a, b) => b.created - a.created);
    $('history-empty').hidden = recordings.length > 0;
    for (const [index, recording] of recordings.entries()) {
      const row = document.createElement('article');
      row.className = 'recording';
      const heading = document.createElement('strong');
      heading.textContent = `تسجيل ${index + 1}`;
      const info = document.createElement('p');
      info.className = 'muted';
      info.textContent = `${new Date(recording.created).toLocaleString('ar-SA')} · رقم النبرة: ${recording.seed}`;
      const top = document.createElement('div');
      top.append(heading, info);
      const audio = document.createElement('audio');
      audio.controls = true;
      audio.setAttribute('aria-label', `تشغيل ${heading.textContent}`);
      const url = URL.createObjectURL(recording.audio);
      recordingUrls.push(url);
      audio.src = url;
      const download = document.createElement('a');
      download.href = url;
      download.download = `speech-${recording.seed}.mp3`;
      download.textContent = 'حمّل ملف MP3';
      row.append(top, audio, download);
      list.append(row);
    }
  } catch {
    $('history-empty').hidden = false;
    $('history-empty').textContent = 'تعذّر فتح التسجيلات المحفوظة في هذا المتصفح.';
  }
}

async function generate() {
  const text = $('speech-text').value.trim();
  const source = document.querySelector('input[name="voice-source"]:checked').value;
  const voice = (source === 'library' ? $('voice-id').value : source === 'selected' ? $('selected-voice').value : voiceId()).trim();
  const key = apiKey();
  const seed = Number($('seed').value);
  if (!key && !demoMode) return message('speech-message', 'أدخل مفتاح ElevenLabs API.', true);
  if (!text) return message('speech-message', 'أدخل النص المراد تحويله إلى صوت.', true);
  if (demoMode && (source !== 'selected' || text.length > 250)) {
    return message('speech-message', 'اختر صوتًا من الأصوات المختارة واكتب نصًا لا يتجاوز 250 حرفًا.', true);
  }
  if (!voice) return message('speech-message', 'استنسخ صوتًا أو أدخل معرّف صوت من المكتبة.', true);
  if (!demoMode && (!$('seed').value || !Number.isInteger(seed) || seed < 0 || seed > 4294967295)) {
    return message('speech-message', 'يجب أن تكون قيمة النبرة بين 0 و4294967295.', true);
  }
  const button = $('generate');
  button.disabled = true;
  button.textContent = 'جارٍ توليد الصوت…';
  message('speech-message', 'جارٍ توليد الصوت…');
  try {
    if (!demoMode) saveSeed(seed);
    const response = await fetch(demoMode ? '/api/demo' : `https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voice)}?output_format=mp3_44100_128`, {
      method: 'POST',
      headers: demoMode ? { 'Content-Type': 'application/json' } : { 'xi-api-key': key, 'Content-Type': 'application/json' },
      body: demoMode ? JSON.stringify({ text, voice }) : JSON.stringify({ text, model_id: 'eleven_v3', voice_settings: settings, seed }),
    });
    if (!response.ok) {
      if (demoMode) {
        const result = await response.json().catch(() => ({}));
        return message('speech-message', result.error || 'تعذّر توليد الصوت التجريبي.', true);
      }
      throw new Error(String(response.status));
    }
    const audio = await response.blob();
    if (!audio.size) throw new Error('empty audio');
    if (playerUrl) URL.revokeObjectURL(playerUrl);
    playerUrl = URL.createObjectURL(audio);
    $('player').src = playerUrl;
    $('download').href = playerUrl;
    $('player-empty').hidden = true;
    $('player-ready').hidden = false;
    message('speech-message', 'صوتك جاهز للاستماع والتحميل.');
    try {
      await recordingsRequest('readwrite', (store) => store.put({ id: crypto.randomUUID(), created: Date.now(), seed: demoMode ? DEFAULT_SEED : seed, audio }));
    } catch { message('speech-message', 'صوتك جاهز للتحميل، لكن تعذّر حفظه في هذا المتصفح.', true); }
  } catch {
    message('speech-message', demoMode ? 'تعذّر توليد الصوت التجريبي. حاول مجددًا لاحقًا.' : 'تعذّر توليد الصوت. تحقق من اتصالك بالإنترنت ومفتاح API ومعرّف الصوت، ثم أعد المحاولة.', true);
  } finally {
    button.disabled = false;
    button.textContent = 'ولّد الصوت';
  }
}

async function clone() {
  const key = apiKey();
  const sample = $('sample').files[0];
  const name = $('clone-name').value.trim();
  if (!key) return message('clone-message', 'أدخل مفتاح ElevenLabs API.', true);
  if (!sample || !sample.size) return message('clone-message', 'ارفع تسجيلًا صوتيًا غير فارغ.', true);
  if (!/\.(wav|mp3|m4a)$/i.test(sample.name) || sample.size > 200 * 1024 * 1024) {
    return message('clone-message', 'اختر ملف WAV أو MP3 أو M4A بحجم لا يتجاوز 200 ميجابايت.', true);
  }
  if (!name) return message('clone-message', 'أدخل اسمًا للصوت.', true);
  const button = $('clone');
  button.disabled = true;
  button.textContent = 'جارٍ استنساخ الصوت…';
  message('clone-message', 'جارٍ استنساخ الصوت…');
  try {
    const body = new FormData();
    body.append('name', name);
    body.append('files', sample);
    body.append('labels', '{}');
    const response = await fetch('https://api.elevenlabs.io/v1/voices/add', {
      method: 'POST', headers: { 'xi-api-key': key }, body,
    });
    if (!response.ok) throw new Error(String(response.status));
    const result = await response.json();
    if (typeof result.voice_id !== 'string' || !result.voice_id) throw new Error('missing voice');
    localStorage.setItem(STORAGE.voice, result.voice_id);
    document.querySelector('input[name="voice-source"][value="saved"]').checked = true;
    renderVoice();
    message('clone-message', 'استنسخت صوتك وحفظته للاستخدام تلقائيًا.');
  } catch {
    message('clone-message', 'تعذّر استنساخ الصوت. تحقق من اتصالك بالإنترنت ومفتاح API والتسجيل، ثم أعد المحاولة.', true);
  } finally {
    button.disabled = false;
    button.textContent = 'استنسخ الصوت';
  }
}

const tabs = [...document.querySelectorAll('[role="tab"]')];
function activateTab(tab) {
  for (const item of tabs) {
    const active = item === tab;
    item.setAttribute('aria-selected', String(active));
    item.tabIndex = active ? 0 : -1;
    $(item.getAttribute('aria-controls')).hidden = !active;
  }
  if (tab.id === 'tab-history') renderHistory();
}
for (const tab of tabs) {
  tab.addEventListener('click', () => activateTab(tab));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const index = tabs.indexOf(tab);
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1
      : (index + (event.key === 'ArrowLeft' ? 1 : -1) + tabs.length) % tabs.length;
    activateTab(tabs[next]);
    tabs[next].focus();
  });
}

$('year').textContent = new Date().getFullYear();
$('speech-text').addEventListener('input', () => {
  if (demoMode) $('demo-text-count').textContent = `${$('speech-text').value.length} / 250 حرفًا`;
});
$('api-key').value = apiKey();
$('key-dot').classList.toggle('active', !!apiKey());
$('api-key').addEventListener('input', (event) => {
  const value = event.target.value.trim();
  if (value) demoMode = false;
  if (value) localStorage.setItem(STORAGE.key, value);
  else localStorage.removeItem(STORAGE.key);
  $('key-dot').classList.toggle('active', !!value);
  renderVoice();
});
$('try-demo').addEventListener('click', () => {
  demoMode = true;
  document.querySelector('input[name="voice-source"][value="selected"]').checked = true;
  renderVoice();
  $('key-menu').open = false;
  document.querySelector('#tab-speech').click();
  $('speech-text').focus();
});
$('clear-key').addEventListener('click', () => {
  localStorage.removeItem(STORAGE.key);
  $('api-key').value = '';
  $('key-dot').classList.remove('active');
  renderVoice();
  $('key-menu').open = false;
});
for (const input of document.querySelectorAll('input[name="voice-source"]')) input.addEventListener('change', renderVoice);
$('new-seed').addEventListener('click', () => {
  $('seed').value = String(crypto.getRandomValues(new Uint32Array(1))[0]);
  saveSeed(Number($('seed').value));
});
$('saved-seeds').addEventListener('change', (event) => { $('seed').value = event.target.value; });
$('generate').addEventListener('click', generate);
$('clone').addEventListener('click', clone);
if (!voiceId()) document.querySelector('input[name="voice-source"][value="library"]').checked = true;
renderSeeds();
renderVoice();
