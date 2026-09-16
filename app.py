# app.py - 𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵 OSINT Toolkit (Vercel-Ready)
import os, json, requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, redirect, url_for

app = Flask(__name__)

# ================== VERCEL DETECTION ==================
IS_VERCEL = os.environ.get('VERCEL') == '1'

# On Vercel, the filesystem is read-only. Skip creating local folders.
if not IS_VERCEL:
    UPLOAD_FOLDER = 'static/uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
else:
    UPLOAD_FOLDER = None
    app.config['UPLOAD_FOLDER'] = None

SETTINGS_FILE = 'settings.json'
BASE = "https://ft-osint-api.duckdns.org"

# ================== API KEY (from env on Vercel) ==================
MASTER_KEY = os.environ.get("OSINT_MASTER_KEY", "vx-osint")

# ================== BRAND ==================
BRAND_NAME = "𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵"
RESULT_BRAND = "𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵 × SHAYAN"

# ================== ALL TOOLS ==================
TOOLS = {
    'number':     {'name': '📞 Number Lookup',        'endpoint': '/api/number',     'param': 'num',      'cat': 'Number'},
    'numleak':    {'name': '🔎 Number Leak (HiTeck)', 'endpoint': '/api/numleak',    'param': 'num',      'cat': 'Number'},
    'adv':        {'name': '📱 Truecaller Lookup',    'endpoint': '/api/adv',        'param': 'num',      'cat': 'Number'},
    'calltracer': {'name': '📞 Call Tracer',          'endpoint': '/api/calltracer', 'param': 'num',      'cat': 'Number'},
    'paytm':      {'name': '💳 Paytm Lookup',         'endpoint': '/api/paytm',      'param': 'num',      'cat': 'Number'},
    'name':       {'name': '🪪 Name Lookup',          'endpoint': '/api/name',       'param': 'name',     'cat': 'Number'},
    'pk':         {'name': '🇵🇰 Pakistan SIM Info',   'endpoint': '/api/pk',         'param': 'num',      'cat': 'Number'},
    'aadhar':      {'name': '🪪 Aadhaar Lookup',   'endpoint': '/api/aadhar',      'param': 'num',  'cat': 'Identity'},
    'adharfamily': {'name': '🪪 Aadhaar Family',   'endpoint': '/api/adharfamily', 'param': 'num',  'cat': 'Identity'},
    'pan':         {'name': '🪪 PAN Lookup',       'endpoint': '/api/pan',         'param': 'pan',  'cat': 'Identity'},
    'gst':         {'name': '🪪 GST Lookup',       'endpoint': '/api/gst',         'param': 'gst',  'cat': 'Identity'},
    'upi':      {'name': '💳 UPI Lookup',       'endpoint': '/api/upi',      'param': 'upi',  'cat': 'Finance'},
    'numtoupi': {'name': '💳 Num to UPI',       'endpoint': '/api/numtoupi', 'param': 'num',  'cat': 'Finance'},
    'ifsc':     {'name': '🏦 IFSC Lookup',      'endpoint': '/api/ifsc',     'param': 'ifsc', 'cat': 'Finance'},
    'bank':     {'name': '🏦 Bank Info',        'endpoint': '/api/adv',      'param': 'num',  'cat': 'Finance'},
    'vehicle': {'name': '🚘 Vehicle to Owner',  'endpoint': '/api/vehicle', 'param': 'vehicle', 'cat': 'Vehicle'},
    'veh2num': {'name': '📞 Vehicle to Mobile', 'endpoint': '/api/veh2num', 'param': 'vehicle', 'cat': 'Vehicle'},
    'challan': {'name': '🚨 Challan Lookup',    'endpoint': '/api/challan', 'param': 'vehicle', 'cat': 'Vehicle'},
    'insta': {'name': '📸 Instagram Info',   'endpoint': '/api/insta', 'param': 'username', 'cat': 'Social'},
    'git':   {'name': '🐙 GitHub Info',      'endpoint': '/api/git',   'param': 'username', 'cat': 'Social'},
    'snap':  {'name': '👻 Snapchat Info',    'endpoint': '/api/snap',  'param': 'username', 'cat': 'Social'},
    'tg':    {'name': '✈️ TG to Num',        'endpoint': '/api/tg',    'param': 'info',     'cat': 'Social'},
    'tgidinfo':{'name': '🆔 TG ID to Num',   'endpoint': '/api/tgidinfo','param':'id',      'cat': 'Social'},
    'email': {'name': '📧 Email to Info',    'endpoint': '/api/email', 'param': 'email',    'cat': 'Social'},
    'ff':   {'name': '🎮 Free Fire Info', 'endpoint': '/api/ff',   'param': 'uid', 'cat': 'Gaming'},
    'bgmi': {'name': '🎮 BGMI Info',      'endpoint': '/api/bgmi', 'param': 'uid', 'cat': 'Gaming'},
    'ip':      {'name': '🌐 IP Lookup',   'endpoint': '/api/ip',      'param': 'ip',  'cat': 'Utility'},
    'pincode': {'name': '📍 Pincode',     'endpoint': '/api/pincode', 'param': 'pin', 'cat': 'Utility'},
    'imei':    {'name': '📱 IMEI Lookup', 'endpoint': '/api/imei',    'param': 'imei','cat': 'Utility'},
    'bomber': {'name': '💣 SMS Bomber', 'endpoint': '/api/bomber', 'param': 'number', 'cat': 'Bomber', 'special': True},
}

# ================== DEFAULT SETTINGS ==================
DEFAULT_SETTINGS = {
    "api_key": MASTER_KEY,
    "default_count": 20,
    "owner_name": BRAND_NAME,
    "profile_image": "https://via.placeholder.com/300x300/000000/00ff00?text=CDX",
    "main_bg": "", "sidebar_bg": "", "audio_url": "",
    "phone": "8910747761",
    "telegram": "",  # hidden
    "whatsapp": "918910747761",
}

# ================== SETTINGS HANDLERS (Vercel-safe) ==================
def load_settings():
    if IS_VERCEL:
        # On Vercel, return defaults (no persistence)
        return DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                d = json.load(f)
                for k, v in DEFAULT_SETTINGS.items():
                    if k not in d:
                        d[k] = v
                d['owner_name'] = BRAND_NAME
                d['phone'] = "8910747761"
                d['whatsapp'] = "918910747761"
                return d
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    if IS_VERCEL:
        # Vercel filesystem is read-only. Use a database for persistence.
        print("⚠️ Settings not persisted on Vercel.")
        return
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(s, f, indent=2)

# ----------------------------------------------------------------------
# MAIN HTML
# ----------------------------------------------------------------------
MAIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵 — OSINT Toolkit</title>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Share Tech Mono',monospace}
body{background:#000;color:#0f0;min-height:100vh;display:flex;flex-direction:column;align-items:center;position:relative;overflow-x:hidden;padding:10px}
#bg-video{position:fixed;top:0;left:0;width:100%;height:100%;object-fit:cover;z-index:-2;display:{{ 'block' if main_bg and main_bg.endswith(('.mp4','.webm','.ogg')) else 'none' }}}
#bg-image{position:fixed;top:0;left:0;width:100%;height:100%;background-image:url('{{ main_bg }}');background-size:cover;background-position:center;z-index:-2;display:{{ 'block' if main_bg and not main_bg.endswith(('.mp4','.webm','.ogg')) else 'none' }};opacity:0.3}
#matrix-canvas{position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;opacity:0.15}

.audio-popup{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.95);backdrop-filter:blur(15px);z-index:99999;display:flex;justify-content:center;align-items:center;transition:opacity 0.6s;cursor:pointer}
.audio-popup.hidden{opacity:0;pointer-events:none}
.audio-popup-content{text-align:center;animation:pulse 2s infinite}
.audio-logo{width:160px;height:160px;border-radius:50%;border:4px solid #0f0;box-shadow:0 0 40px #0f0;object-fit:cover;margin-bottom:20px}
.audio-popup-content h2{color:#0f0;text-shadow:0 0 15px #0f0;font-size:1.6rem;margin-bottom:10px;letter-spacing:2px}
.audio-popup-content p{color:#fff;opacity:0.7;font-size:0.85rem}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}

.header{width:100%;max-width:520px;display:flex;align-items:center;justify-content:space-between;padding:12px 18px;border-bottom:1px solid #0f0;margin-bottom:15px;background:rgba(0,0,0,0.75);backdrop-filter:blur(5px);position:sticky;top:0;z-index:10;border-radius:0 0 10px 10px}
.header .left-side{display:flex;align-items:center;gap:12px}
.menu-icon{font-size:24px;cursor:pointer;color:#0f0}
.menu-icon:hover{color:#fff}
.header h1{font-size:1rem;color:#0f0;text-shadow:0 0 10px #0f0;letter-spacing:1px}
.header .free-badge{background:#0f0;color:#000;padding:6px 12px;border-radius:8px;border:none;font-weight:bold;font-size:0.75rem;letter-spacing:1px}

.container{width:100%;max-width:520px;display:flex;flex-direction:column;align-items:center;z-index:1}
.profile-img{width:200px;height:200px;object-fit:cover;border:2px solid #0f0;border-radius:50%;box-shadow:0 0 25px rgba(0,255,0,0.5);margin-bottom:15px}
.subtitle{font-size:1.3rem;font-weight:bold;color:#0f0;text-shadow:0 0 15px #0f0;text-align:center;margin-bottom:20px}

.tool-box{width:100%;background:rgba(0,0,0,0.85);border:1px solid #0f0;border-radius:12px;padding:20px;box-shadow:0 0 15px rgba(0,255,0,0.2);backdrop-filter:blur(5px);margin-bottom:20px}
.tool-box h3{color:#0f0;margin-bottom:12px;font-size:1rem;border-bottom:1px dashed #0f0;padding-bottom:6px}

.cat-tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:15px}
.cat-tab{background:#111;border:1px solid #0f0;color:#0f0;padding:6px 12px;border-radius:20px;font-size:0.75rem;cursor:pointer;transition:all 0.2s;font-family:inherit}
.cat-tab:hover{background:#0f0;color:#000}
.cat-tab.active{background:#0f0;color:#000;box-shadow:0 0 10px #0f0}

.tool-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:15px;max-height:240px;overflow-y:auto;padding:5px;scrollbar-width:thin;scrollbar-color:#0f0 #000}
.tool-grid::-webkit-scrollbar{width:6px}
.tool-grid::-webkit-scrollbar-track{background:#000}
.tool-grid::-webkit-scrollbar-thumb{background:#0f0;border-radius:3px}
.tool-item{background:#111;border:1px solid #0f0;border-radius:8px;padding:10px;cursor:pointer;transition:all 0.2s;text-align:center;font-size:0.75rem;color:#0f0;position:relative;font-family:inherit}
.tool-item:hover{background:rgba(0,255,0,0.15);box-shadow:0 0 10px rgba(0,255,0,0.3)}
.tool-item.selected{background:#0f0;color:#000;box-shadow:0 0 15px #0f0}

.input-group{display:flex;align-items:center;background:#111;border:1px solid #0f0;border-radius:8px;padding:12px 15px;margin-bottom:12px}
.input-group input{background:transparent;border:none;color:#fff;font-size:0.95rem;width:100%;outline:none;font-family:inherit}
.input-group input::placeholder{color:rgba(0,255,0,0.5)}

.btn{width:100%;padding:14px;background:#000;border:2px solid #0f0;color:#0f0;font-size:1rem;font-weight:bold;border-radius:8px;cursor:pointer;transition:all 0.3s;text-shadow:0 0 5px #0f0;font-family:inherit;letter-spacing:1px;margin-bottom:8px}
.btn:hover{background:#0f0;color:#000;box-shadow:0 0 20px #0f0;text-shadow:none}
.btn:disabled{opacity:0.4;cursor:not-allowed;background:#000;color:#0f0}
.btn-stop{border-color:#f00;color:#f00;text-shadow:0 0 5px #f00}
.btn-stop:hover{background:#f00;color:#000;box-shadow:0 0 20px #f00}

.result-box{background:#050505;border:1px solid #0f0;border-radius:8px;padding:15px;margin-top:12px;min-height:100px;max-height:450px;overflow-y:auto;font-size:0.8rem;color:#0f0;white-space:pre-wrap;word-break:break-word;display:none;position:relative}
.result-box.active{display:block}
.result-box .loading{color:#ff0;animation:blink 1s infinite}
@keyframes blink{50%{opacity:0.4}}
.result-box pre{margin:0;font-family:inherit;white-space:pre-wrap}
.result-box .err{color:#f00}

.result-brand{
  margin-top:14px;
  padding-top:10px;
  border-top:1px dashed rgba(0,255,0,0.4);
  text-align:center;
  font-size:0.85rem;
  font-weight:bold;
  letter-spacing:2px;
  color:#0f0;
  text-shadow:0 0 10px #0f0, 0 0 20px rgba(0,255,0,0.5);
  opacity:0.95;
}
.result-brand .sub{
  display:block;
  font-size:0.7rem;
  font-weight:normal;
  letter-spacing:1px;
  color:#0ff;
  text-shadow:0 0 6px #0ff;
  margin-top:4px;
}

.status-box{background:#111;border:1px solid #0f0;border-radius:8px;padding:12px;margin-bottom:12px;font-size:0.85rem;color:#0f0;text-align:center}

.overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:999;display:none;opacity:0;transition:opacity 0.4s}
.overlay.active{display:block;opacity:1}
.sidebar{position:fixed;top:0;left:-320px;width:300px;height:100%;background:#000;border-right:2px solid #0f0;z-index:1000;transition:left 0.4s cubic-bezier(0.175,0.885,0.32,1.275);display:flex;flex-direction:column;padding:20px;overflow-y:auto}
.sidebar.active{left:0}
.sidebar-bg{position:absolute;top:0;left:0;width:100%;height:100%;z-index:-1;opacity:0.2;object-fit:cover}
.sidebar-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:25px;padding-bottom:10px;border-bottom:1px solid #0f0}
.sidebar-header h2{color:#0f0;font-size:1.1rem}
.close-btn{background:none;border:none;color:#0f0;font-size:2rem;cursor:pointer;line-height:1}
.close-btn:hover{color:#fff}
.contact-section h3{color:#0f0;margin-bottom:12px;font-size:0.9rem;border-bottom:1px dashed #0f0;padding-bottom:5px}
.contact-item{display:flex;align-items:center;background:rgba(0,255,0,0.1);border:1px solid #0f0;border-radius:8px;padding:10px;margin-bottom:10px;text-decoration:none;color:#0f0;transition:all 0.3s}
.contact-item:hover{background:#0f0;color:#000;box-shadow:0 0 15px #0f0}
.contact-item .icon{font-size:1.3rem;margin-right:12px}
.contact-item .info{display:flex;flex-direction:column}
.contact-item .info .label{font-size:0.65rem;text-transform:uppercase}
.contact-item .info .value{font-size:0.85rem;font-weight:bold}

.footer{text-align:center;font-size:0.9rem;color:#0f0;text-shadow:0 0 5px #0f0;padding:15px 0;letter-spacing:2px;font-weight:bold}
</style>
</head>
<body>

{% if audio_url %}
<audio id="bg-music" loop preload="auto" src="{{ audio_url }}"></audio>
<div id="audio-popup" class="audio-popup">
  <div class="audio-popup-content">
    <img src="{{ profile_image }}" alt="Logo" class="audio-logo">
    <h2>TAP TO ENABLE MUSIC</h2>
    <p>Click anywhere to start</p>
  </div>
</div>
{% endif %}

{% if main_bg %}
{% if main_bg.endswith(('.mp4','.webm','.ogg')) %}
<video id="bg-video" autoplay loop muted playsinline src="{{ main_bg }}"></video>
{% else %}
<div id="bg-image"></div>
{% endif %}
{% endif %}
<canvas id="matrix-canvas"></canvas>

<div class="overlay" id="overlay"></div>

<div class="sidebar" id="sidebar">
  {% if sidebar_bg %}
    {% if sidebar_bg.endswith(('.mp4','.webm','.ogg')) %}
      <video class="sidebar-bg" autoplay loop muted playsinline src="{{ sidebar_bg }}"></video>
    {% else %}
      <img class="sidebar-bg" src="{{ sidebar_bg }}" alt="">
    {% endif %}
  {% endif %}
  <div class="sidebar-header">
    <h2>MENU</h2>
    <button class="close-btn" id="closeSidebarBtn">&times;</button>
  </div>
  <div style="text-align:center;margin-bottom:20px">
    <img src="{{ profile_image }}" style="width:90px;height:90px;border-radius:50%;border:2px solid #0f0;object-fit:cover">
    <h3 style="color:#fff;margin-top:10px;font-size:0.95rem;letter-spacing:1px">{{ owner_name }}</h3>
    <p style="color:#0f0;font-size:0.75rem">Owner & Developer</p>
  </div>
  <div class="contact-section">
    <h3>CONTACT ME</h3>
    <a href="tel:{{ phone }}" class="contact-item">
      <span class="icon">&#128222;</span>
      <div class="info"><span class="label">Phone</span><span class="value">{{ phone }}</span></div>
    </a>
    {% if telegram %}
    <a href="https://t.me/{{ telegram }}" target="_blank" class="contact-item">
      <span class="icon">&#128172;</span>
      <div class="info"><span class="label">Telegram</span><span class="value">{{ telegram }}</span></div>
    </a>
    {% endif %}
    <a href="https://wa.me/{{ whatsapp }}" target="_blank" class="contact-item">
      <span class="icon">&#128241;</span>
      <div class="info"><span class="label">WhatsApp</span><span class="value">{{ whatsapp }}</span></div>
    </a>
  </div>
</div>

<div class="header">
  <div class="left-side">
    <div class="menu-icon" id="openSidebarBtn">&#9776;</div>
    <h1>{{ owner_name }}</h1>
  </div>
  <div class="free-badge">💎 100% FREE</div>
</div>

<div class="container">
  <img src="{{ profile_image }}" class="profile-img" alt="">
  <div class="subtitle">{{ owner_name }}</div>

  <div class="tool-box">
    <h3>🛠️ Select Tool</h3>
    <div class="cat-tabs" id="catTabs"></div>
    <div class="tool-grid" id="toolGrid"></div>
    <div class="input-group">
      <input type="text" id="toolInput" placeholder="Enter value...">
    </div>
    <div id="bomberCount" style="display:none">
      <div class="input-group">
        <input type="number" id="bomberCounter" placeholder="How many messages?" value="{{ default_count }}" min="1" max="500">
      </div>
    </div>
    <button class="btn" id="runBtn">🚀 RUN TOOL</button>
    <button class="btn btn-stop" id="stopBtn" style="display:none">⛔ STOP BOMBER</button>
    <div class="status-box" id="statusBox">Select a tool and enter value</div>
    <div class="result-box" id="resultBox"></div>
  </div>

  <div class="footer">{{ owner_name }}</div>
</div>

<script>
const TOOLS = {{ tools_json | safe }};
const RESULT_BRAND = "{{ result_brand }}";

let selectedTool = null;
let activeCat = 'All';

// Audio
const bgMusic = document.getElementById('bg-music');
const audioPopup = document.getElementById('audio-popup');
if (bgMusic && audioPopup) {
  bgMusic.volume = 0.5;
  let unlocked = false;
  const unlock = () => {
    if (unlocked) return;
    bgMusic.play().then(()=>{unlocked=true;audioPopup.classList.add('hidden')}).catch(e=>console.log(e));
  };
  audioPopup.addEventListener('click', unlock);
  audioPopup.addEventListener('touchstart', unlock);
  document.addEventListener('click', unlock);
  document.addEventListener('touchstart', unlock);
  audioPopup.addEventListener('click', ()=>setTimeout(()=>audioPopup.classList.add('hidden'),1200));
}

// Sidebar
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');
document.getElementById('openSidebarBtn').onclick = ()=>{sidebar.classList.add('active');overlay.classList.add('active')};
document.getElementById('closeSidebarBtn').onclick = ()=>{sidebar.classList.remove('active');overlay.classList.remove('active')};
overlay.onclick = ()=>{sidebar.classList.remove('active');overlay.classList.remove('active')};

// Matrix rain
const canvas = document.getElementById('matrix-canvas');
const ctx = canvas.getContext('2d');
function resizeCanvas(){canvas.width=window.innerWidth;canvas.height=window.innerHeight}
resizeCanvas();
const letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()';
const fontSize=14;let drops=[];
for(let x=0;x<canvas.width/fontSize;x++)drops[x]=1;
function drawMatrix(){
  ctx.fillStyle='rgba(0,0,0,0.05)';ctx.fillRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle='#00ff00';ctx.font=fontSize+'px monospace';
  for(let i=0;i<drops.length;i++){
    const t=letters.charAt(Math.floor(Math.random()*letters.length));
    ctx.fillText(t,i*fontSize,drops[i]*fontSize);
    if(drops[i]*fontSize>canvas.height && Math.random()>0.975)drops[i]=0;
    drops[i]++;
  }
}
setInterval(drawMatrix,50);
window.addEventListener('resize',resizeCanvas);

// Render
const catTabs = document.getElementById('catTabs');
const toolGrid = document.getElementById('toolGrid');
const categories = ['All',...new Set(Object.values(TOOLS).map(t=>t.cat))];

function renderCats(){
  catTabs.innerHTML='';
  categories.forEach(c=>{
    const el=document.createElement('div');
    el.className='cat-tab'+(c===activeCat?' active':'');
    el.textContent=c; el.onclick=()=>{activeCat=c;renderCats();renderTools()};
    catTabs.appendChild(el);
  });
}
function renderTools(){
  toolGrid.innerHTML='';
  Object.entries(TOOLS).forEach(([key,t])=>{
    if (activeCat!=='All' && t.cat!==activeCat) return;
    const el=document.createElement('div');
    el.className='tool-item'+(selectedTool===key?' selected':'');
    el.innerHTML = t.name;
    el.onclick = ()=>selectTool(key);
    toolGrid.appendChild(el);
  });
}
function selectTool(key){
  selectedTool = key;
  const t = TOOLS[key];
  document.getElementById('toolInput').placeholder = 'Enter '+t.param+'...';
  document.getElementById('bomberCount').style.display = t.special ? 'block' : 'none';
  document.getElementById('stopBtn').style.display = 'none';
  document.getElementById('resultBox').classList.remove('active');
  setStatus('Selected: '+t.name+' — Enter value and click RUN');
  renderTools();
}
function setStatus(msg, err){
  const s=document.getElementById('statusBox');
  s.textContent=msg; s.style.color=err?'#f00':'#0f0'; s.style.borderColor=err?'#f00':'#0f0';
}
function brandFooterHTML(){
  return '<div class="result-brand">⚡ '+RESULT_BRAND+' ⚡<span class="sub">Result Powered By '+RESULT_BRAND+'</span></div>';
}

// Run
let bomberActive=false, bomberTimeout=null;
const runBtn = document.getElementById('runBtn');
const stopBtn = document.getElementById('stopBtn');
const resultBox = document.getElementById('resultBox');

runBtn.onclick = async ()=>{
  if (!selectedTool){ setStatus('Please select a tool first',true); return; }
  const t = TOOLS[selectedTool];
  const val = document.getElementById('toolInput').value.trim();
  if (!val){ setStatus('Please enter a value',true); return; }

  if (t.special && selectedTool==='bomber'){
    runBomber(val); return;
  }

  resultBox.classList.add('active');
  resultBox.innerHTML = '<span class="loading">⏳ Fetching data from API...</span>';
  setStatus('Running '+t.name+'...');

  try{
    const res = await fetch('/api/proxy',{
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({tool:selectedTool, value:val})
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    let out = data.data;
    if (typeof out === 'object') out = JSON.stringify(out, null, 2);
    resultBox.innerHTML = '<pre>'+escapeHtml(out)+'</pre>' + brandFooterHTML();
    setStatus('✅ '+t.name+' completed successfully');
  }catch(e){
    resultBox.innerHTML = '<pre class="err">❌ Error: '+escapeHtml(e.message)+'</pre>' + brandFooterHTML();
    setStatus('❌ Failed: '+e.message, true);
  }
};

function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}

// Bomber
async function runBomber(number){
  const count = parseInt(document.getElementById('bomberCounter').value)||20;
  if (number.length<10){setStatus('Enter valid 10-digit number',true);return}
  bomberActive=true;
  runBtn.disabled=true; stopBtn.style.display='block';
  resultBox.classList.add('active');
  resultBox.innerHTML='';
  let c=1;
  const run=async()=>{
    if(!bomberActive||c>count){
      bomberActive=false;runBtn.disabled=false;stopBtn.style.display='none';
      if(c>count){
        setStatus('✅ Bomber finished '+count+' messages');
        resultBox.insertAdjacentHTML('beforeend', brandFooterHTML());
      }
      return;
    }
    try{
      const res=await fetch('/api/proxy',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({tool:'bomber',value:number,counter:c})});
      const d=await res.json();
      const p=document.createElement('div');
      p.textContent='['+c+'/'+count+'] '+(d.error?'❌ '+d.error:'✅ Message sent');
      p.style.color=d.error?'#f00':'#0f0';
      resultBox.appendChild(p);
      resultBox.scrollTop=resultBox.scrollHeight;
      setStatus('Bomber: '+c+'/'+count+' sent');
    }catch(e){
      const p=document.createElement('div');p.textContent='['+c+'] ❌ '+e.message;p.style.color='#f00';
      resultBox.appendChild(p);
    }
    c++;
    bomberTimeout=setTimeout(run,700);
  };
  run();
}
stopBtn.onclick=()=>{
  bomberActive=false;
  if(bomberTimeout)clearTimeout(bomberTimeout);
  runBtn.disabled=false;stopBtn.style.display='none';
  setStatus('⛔ Bomber stopped by user',true);
  resultBox.insertAdjacentHTML('beforeend', brandFooterHTML());
};

renderCats();
renderTools();
</script>
</body>
</html>
"""

# ----------------------------------------------------------------------
# ADMIN HTML
# ----------------------------------------------------------------------
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Admin — 𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',sans-serif}
body{background:#0f0c29;color:#fff;min-height:100vh;padding:30px 15px;display:flex;justify-content:center}
.admin-card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:35px;width:100%;max-width:700px;box-shadow:0 20px 50px rgba(0,0,0,0.5)}
h1{text-align:center;margin-bottom:25px;color:#0f0;text-shadow:0 0 10px #0f0;letter-spacing:2px}
.warn{background:rgba(0,255,0,0.1);border:1px solid #0f0;color:#0f0;padding:12px;border-radius:8px;font-size:0.85rem;margin-bottom:20px;text-align:center}
.section-title{color:#0f0;margin:25px 0 15px;font-size:1.1rem;border-bottom:1px solid #0f0;padding-bottom:6px;display:inline-block}
.form-group{margin-bottom:15px}
label{display:block;font-size:0.85rem;margin-bottom:6px;color:#ccc}
input[type="text"],input[type="number"],input[type="file"]{width:100%;padding:11px 14px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);border-radius:8px;color:#fff;font-size:0.95rem;outline:none}
input:focus{border-color:#0f0;box-shadow:0 0 10px rgba(0,255,0,0.3)}
.btn-save{width:100%;padding:14px;background:linear-gradient(135deg,#0f0,#0a0);color:#000;border:none;border-radius:8px;font-size:1rem;font-weight:bold;cursor:pointer;margin-top:10px}
.back-link{display:block;text-align:center;margin-top:20px;color:#0f0;text-decoration:none}
.back-link:hover{text-decoration:underline}
</style>
</head>
<body>
<div class="admin-card">
<h1>⚙️ 𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵 — Admin</h1>
<div class="warn">✅ All tools are FREE. On Vercel, settings won't persist — use a database or env vars.</div>

<form action="/admin/settings" method="POST">
<h2 class="section-title">General</h2>
<div class="form-group"><label>Brand Name (Owner)</label><input type="text" name="owner_name" value="{{ owner_name }}" required></div>
<div class="form-group"><label>Master API Key</label><input type="text" name="api_key" value="{{ api_key }}" required></div>
<div class="form-group"><label>Default Bomber Count</label><input type="number" name="default_count" value="{{ default_count }}" required></div>

<h2 class="section-title">Media URLs</h2>
<div class="form-group"><label>Profile Image URL</label><input type="text" name="profile_image" value="{{ profile_image }}"></div>
<div class="form-group"><label>Main Background URL (img/video)</label><input type="text" name="main_bg" value="{{ main_bg }}"></div>
<div class="form-group"><label>Sidebar Background URL (img/video)</label><input type="text" name="sidebar_bg" value="{{ sidebar_bg }}"></div>
<div class="form-group"><label>Background Music URL (mp3)</label><input type="text" name="audio_url" value="{{ audio_url }}"></div>

<h2 class="section-title">Contact</h2>
<div class="form-group"><label>Phone</label><input type="text" name="phone" value="{{ phone }}"></div>
<div class="form-group"><label>Telegram (leave empty to hide)</label><input type="text" name="telegram" value="{{ telegram }}"></div>
<div class="form-group"><label>WhatsApp (with country code)</label><input type="text" name="whatsapp" value="{{ whatsapp }}"></div>

<button type="submit" class="btn-save">💾 Save All Settings</button>
</form>

<a href="/" class="back-link">← Back to Main Site</a>
</div>
</body>
</html>
"""

# ----------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------
@app.route('/')
def index():
    s = load_settings()
    return render_template_string(MAIN_HTML,
        owner_name=s['owner_name'], profile_image=s['profile_image'],
        main_bg=s['main_bg'], sidebar_bg=s['sidebar_bg'], audio_url=s['audio_url'],
        phone=s['phone'], telegram=s['telegram'], whatsapp=s['whatsapp'],
        default_count=s['default_count'],
        result_brand=RESULT_BRAND,
        tools_json=json.dumps({k:{'name':v['name'],'param':v['param'],'cat':v['cat'],'special':v.get('special',False)} for k,v in TOOLS.items()}),
    )

@app.route('/admin')
def admin():
    s = load_settings()
    return render_template_string(ADMIN_HTML,
        owner_name=s['owner_name'], api_key=s['api_key'], default_count=s['default_count'],
        profile_image=s['profile_image'], main_bg=s['main_bg'], sidebar_bg=s['sidebar_bg'],
        audio_url=s['audio_url'], phone=s['phone'], telegram=s['telegram'],
        whatsapp=s['whatsapp'])

@app.route('/admin/settings', methods=['POST'])
def save_admin():
    s = load_settings()
    for f in ['owner_name','api_key','profile_image','main_bg','sidebar_bg','audio_url','phone','telegram','whatsapp']:
        if f in request.form: s[f] = request.form[f]
    try: s['default_count'] = int(request.form.get('default_count',s['default_count']))
    except: pass
    if not s.get('owner_name'): s['owner_name'] = BRAND_NAME
    save_settings(s)
    return redirect('/admin')

@app.route('/api/proxy', methods=['POST'])
def proxy():
    data = request.get_json() or {}
    tool = data.get('tool')
    value = data.get('value')
    counter = data.get('counter')
    s = load_settings()
    key = s.get('api_key', MASTER_KEY)

    if tool not in TOOLS:
        return jsonify({'error':'Unknown tool'}), 400

    t = TOOLS[tool]
    if tool == 'bomber':
        url = f"{BASE}{t['endpoint']}?key={key}&number={value}&counter={counter}"
    else:
        url = f"{BASE}{t['endpoint']}?key={key}&{t['param']}={value}"

    try:
        r = requests.get(url, timeout=20)
        try: return jsonify({'data': r.json()}), r.status_code
        except: return jsonify({'data': r.text}), r.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 502

# ================== VERCEL ENTRY POINT ==================
# Vercel's Python runtime expects a variable called `app` in the entry file.
# This works both locally (via `python app.py`) and on Vercel (via `api/index.py`).

if __name__ == '__main__':
    print("Starting 𝐂𝚯𝐃𝚵𝚾 𝚨𝐏𝐏𝐋𝚵 OSINT Toolkit (ALL FREE)...")
    print("Main:  http://127.0.0.1:4887")
    print("Admin: http://127.0.0.1:4887/admin")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 4887)), debug=True)
