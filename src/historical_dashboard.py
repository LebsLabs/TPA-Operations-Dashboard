from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)
DB = Path(__file__).resolve().parent / 'TPA_Operations.db'
KEYS = {
    'Insurance Company A': 'Remaining Balance',
    'Insurance Company B': 'Insurance Company B Remaining Balance',
    'Insurance Company C': 'Insurance Company C Remaining Balance',
}
PAGE = '''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TPA Operations Dashboard</title><style>
*{box-sizing:border-box}body{margin:0 auto;max-width:1120px;padding:32px;background:#0b1220;color:#f8fafc;font-family:Segoe UI,Arial}h1{font-size:26px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card,.panel{background:#19243b;border-radius:12px;padding:22px}.card small{color:#aebcd0}.amount{font-size:clamp(18px,3vw,29px);font-weight:700;margin-top:8px}.panel{margin-top:18px}h2{margin-top:0}.tools{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}.tabs{display:flex;gap:5px}button{background:none;border:0;color:#9daac0;font-size:16px;font-weight:700;padding:10px 15px;border-radius:30px;cursor:pointer}button.active{background:#30384a;color:white}svg{width:100%;height:auto;display:block}.note{color:#9daac0;font-size:13px}@media(max-width:600px){body{padding:16px}.cards{grid-template-columns:1fr}}
</style></head><body><h1>TPA Operations Dashboard — Historical Balances</h1><div class="cards"><div class="card"><small>Insurance Company A</small><div class="amount" id="Insurance Company A">—</div></div><div class="card"><small>Insurance Company B</small><div class="amount" id="Insurance Company B">—</div></div><div class="card"><small>Insurance Company C</small><div class="amount" id="Insurance Company C">—</div></div></div><div class="panel"><h2>Balance history</h2><div class="tools"><div class="tabs" id="companies"><button class="active" data-c="Insurance Company A">Insurance Company A</button><button data-c="Insurance Company B">Insurance Company B</button><button data-c="Insurance Company C">Insurance Company C</button></div><div class="tabs" id="periods"><button data-d="7">7D</button><button class="active" data-d="30">30D</button><button data-d="90">90D</button></div></div><svg id="chart" viewBox="0 0 900 380" aria-label="Historical balance chart"></svg><p class="note" id="note">Historical values will appear as changes are recorded.</p></div><p class="note" id="status">Connecting…</p><script>
let company='Insurance Company A',days=30;const ns='http://www.w3.org/2000/svg';function node(tag,a,t){let e=document.createElementNS(ns,tag);for(let k in a)e.setAttribute(k,a[k]);if(t!==undefined)e.textContent=t;return e}function fmt(n){return n==null?'—':Number(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}function draw(data){let s=document.getElementById('chart');s.replaceChildren();for(let i=0;i<5;i++){let y=30+i*72;s.append(node('line',{x1:70,y1:y,x2:875,y2:y,stroke:'#35445b','stroke-dasharray':'6 9'}))}if(!data.length){s.append(node('text',{x:450,y:175,fill:'#9daac0','text-anchor':'middle','font-size':20},'No history recorded yet'));return}let vals=data.map(p=>p.value),lo=Math.min(...vals),hi=Math.max(...vals),pad=Math.max((hi-lo)*.15,Math.abs(hi)*.005,1);lo-=pad;hi+=pad;let times=data.map(p=>new Date(p.recorded_at).getTime()),first=Math.min(...times),last=Math.max(...times);let xy=data.map((p,i)=>[first===last?475:70+(times[i]-first)/(last-first)*805,318-(p.value-lo)/(hi-lo)*288]);for(let i=0;i<5;i++)s.append(node('text',{x:60,y:35+i*72,fill:'#9daac0','text-anchor':'end','font-size':13},Math.round(hi-(hi-lo)*i/4).toLocaleString('en-US')));s.append(node('polyline',{points:xy.map(p=>p.join(',')).join(' '),fill:'none',stroke:'#60a5fa','stroke-width':4,'stroke-linejoin':'round'}));xy.forEach((p,i)=>{let c=node('circle',{cx:p[0],cy:p[1],r:5,fill:'#93c5fd'});c.append(node('title',{},data[i].recorded_at+' — '+fmt(data[i].value)));s.append(c)});s.append(node('text',{x:70,y:365,fill:'#9daac0'},'Earlier'));s.append(node('text',{x:875,y:365,fill:'#9daac0','text-anchor':'end'},'Latest'))}async function update(){try{let r=await fetch('/api/history?company='+company+'&days='+days,{cache:'no-store'});if(!r.ok)throw Error('Database unavailable');let d=await r.json();for(let c of ['Insurance Company A','Insurance Company B','Insurance Company C'])document.getElementById(c).textContent=fmt(d.balances[c]);draw(d.history);document.getElementById('note').textContent=d.history.length+' recorded reading(s) for '+company+' in the last '+days+' days. History begins when this dashboard is first opened.';document.getElementById('status').textContent='● Connected · Checked '+new Date().toLocaleTimeString()}catch(e){document.getElementById('status').textContent='● '+e.message}}document.querySelectorAll('[data-c]').forEach(b=>b.onclick=()=>{company=b.dataset.c;document.querySelectorAll('[data-c]').forEach(x=>x.classList.toggle('active',x===b));update()});document.querySelectorAll('[data-d]').forEach(b=>b.onclick=()=>{days=+b.dataset.d;document.querySelectorAll('[data-d]').forEach(x=>x.classList.toggle('active',x===b));update()});update();setInterval(update,3000);
</script></body></html>'''

@app.get('/')
def home():
    return render_template_string(PAGE)

@app.get('/api/history')
def history():
    company = request.args.get('company','Insurance Company A')
    if company not in KEYS: return jsonify(error='Invalid company'),400
    try: days=int(request.args.get('days',30))
    except ValueError: return jsonify(error='Invalid period'),400
    if days not in (7,30,90): return jsonify(error='Invalid period'),400
    balances={k:None for k in KEYS}
    readings=[]
    if DB.exists():
        try:
            with sqlite3.connect(DB,timeout=10) as conn:
                conn.execute('CREATE TABLE IF NOT EXISTS TPA_Balance_History (ID INTEGER PRIMARY KEY AUTOINCREMENT, Company TEXT NOT NULL, Balance REAL NOT NULL, Recorded_At TEXT NOT NULL)')
                rows=conn.execute('SELECT KPI_Name,KPI_Value FROM CEO_KPIs WHERE KPI_Name IN (?,?,?)',tuple(KEYS.values())).fetchall()
                reverse={v:k for k,v in KEYS.items()}
                for key,value in rows:
                    name=reverse[key];balances[name]=value
                    last=conn.execute('SELECT Balance FROM TPA_Balance_History WHERE Company=? ORDER BY ID DESC LIMIT 1',(name,)).fetchone()
                    if value is not None and (last is None or abs(float(last[0])-float(value))>0.000001):
                        conn.execute('INSERT INTO TPA_Balance_History (Company,Balance,Recorded_At) VALUES (?,?,?)',(name,float(value),datetime.now().isoformat(timespec='seconds')))
                cutoff=(datetime.now()-timedelta(days=days)).isoformat(timespec='seconds')
                readings=[{'value':v,'recorded_at':t} for v,t in conn.execute('SELECT Balance,Recorded_At FROM TPA_Balance_History WHERE Company=? AND Recorded_At>=? ORDER BY ID',(company,cutoff))]
        except sqlite3.Error:
            return jsonify(error='Database unavailable'),503
    return jsonify(balances=balances,history=readings)

if __name__=='__main__':
    app.run(host='127.0.0.1',port=5001,debug=False)
