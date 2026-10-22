'use strict';
const $ = id => document.getElementById(id);
const fmt = (n,d=1) => n == null ? '—' : Number(n).toLocaleString('es-MX',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct = n => n == null ? '—' : fmt(n*100,1)+' %';
const date = s => s.slice(8,10)+' oct · '+s.slice(11,16)+' UTC';
function el(tag, text, cls){const e=document.createElement(tag);if(text!=null)e.textContent=text;if(cls)e.className=cls;return e;}
function clear(id){const e=$(id);e.replaceChildren();return e;}
function row(cells){const r=el('tr');cells.forEach(c=>r.append(el('td',c)));return r;}
let report=null, selected=null, page=0, request=null;
const filters=['site','start','end','split','method'];
function query(){return new URLSearchParams(Object.fromEntries(filters.map(k=>[k,$(k).value]))).toString();}
function activate(tab){
 document.querySelectorAll('.view').forEach(e=>e.hidden=e.id!==tab);
 document.querySelectorAll('.nav').forEach(e=>{const on=e.dataset.tab===tab;e.classList.toggle('active',on);if(on)e.setAttribute('aria-current','page');else e.removeAttribute('aria-current');});
 const titles={cyber:['Cyber con contexto operacional.','Eventos OT y señales numéricas del mismo sitio.'],overview:['Cada gota, con evidencia.','Identifica intervalos sospechosos y decide qué revisar.'],evaluation:['La evidencia detrás de la alerta.','Compara aciertos, errores y tiempo de inferencia.'],method:['Entender antes de concluir.','Origen, fórmulas y límites de esta demostración.']};
 $('page-title').textContent=titles[tab][0];$('page-subtitle').textContent=titles[tab][1];
}
document.querySelectorAll('.nav').forEach(b=>b.addEventListener('click',()=>activate(b.dataset.tab)));
async function load(){
 if(request)request.abort();request=new AbortController();const local=request;
 $('status').className='';$('status').textContent='Actualizando análisis…';$('content').hidden=true;
 try{
  const response=await fetch('/api/dashboard?'+query(),{signal:local.signal});const data=await response.json();
  if(!response.ok)throw new Error(data.error||'No se pudo leer el análisis.');
  if(local!==request)return;
  report=data;page=0;selected=data.alerts[0]?.id||null;render();
  $('content').hidden=false;
  $('status').textContent=data.metrics.rows ? `${data.metrics.rows} registros · ${data.timeline.length} intervalos horarios · UTC · datos simulados` : 'Sin registros para estos filtros. Ajusta el sitio, periodo o fechas.';
 }catch(e){if(e.name==='AbortError')return;report=null;$('status').className='error';$('status').textContent=e.message+' Comprueba que el servidor siga abierto.';}
}
filters.forEach(k=>$(k).addEventListener('change',load));
$('reset').addEventListener('click',()=>{const defaults={site:'all',start:'2026-10-12',end:'2026-10-18',split:'all',method:'rules'};filters.forEach(k=>$(k).value=defaults[k]);load();});
function render(){
 const m=report.metrics,k=clear('kpis');
 [['Agua captada',fmt(m.water_l,0)+' L','Captación local simulada'],['Energía total',fmt(m.energy_total_kwh,0)+' kWh','IT + auxiliares del perímetro'],['PUE del periodo',fmt(m.pue,3),'Cociente de sumas'],['Intensidad hídrica',fmt(m.water_intensity,3),'L / kWh IT · cociente de sumas']].forEach(([label,value,foot])=>{const card=el('div',null,'kpi');card.append(el('div',label,'kpi-label'),el('div',value,'kpi-value'),el('div',foot,'kpi-foot'));k.append(card);});
 const sites=clear('sites');
 report.sites.forEach(s=>{const b=el('button',null,'site-card'+($('site').value===s.site?' selected':''));const head=el('div',null,'site-head');head.append(el('b',s.site+' · '+({aire:'Aire',evaporativa:'Evaporativa',liquida:'Líquida'}[s.cooling])),el('span',!s.rows?'Sin registros':s.alerts?s.alerts+' alertas':'Sin alertas','badge'+(s.alerts?' warn':'')));const vals=el('div',null,'site-values');[['Agua (L)',fmt(s.water_l,0)],['PUE',fmt(s.pue,2)],['L/kWh IT',fmt(s.water_intensity,2)]].forEach(([a,v])=>{const d=el('div',a);d.append(el('strong',v));vals.append(d);});b.append(head,vals);b.addEventListener('click',()=>{$('site').value=s.site;load();});sites.append(b);});
 $('alert-count').textContent=report.alerts.length;
 $('export-csv').href='/api/alerts.csv?'+query();$('export-json').href='/api/export.json?'+query();
 renderChart();renderAlerts();renderEvidence();renderEvaluation();renderCyber();
 const gaps=report.quality.missing_internal_intervals;
 $('quality').textContent=gaps.length?'Huecos internos en la selección: '+gaps.map(x=>x.site+': '+x.missing_intervals).join(', ')+'. No se rellenaron.':'Selección validada: sin duplicados ni valores inválidos; sin huecos horarios internos detectados. Esto no verifica que existan datos fuera de sus límites.';
}
function svg(tag,attrs,text){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs||{}).forEach(([k,v])=>e.setAttribute(k,v));if(text!=null)e.textContent=text;return e;}
function renderChart(){
 if(!report)return;const host=clear('chart'),rows=report.timeline,key=$('chart-metric').value;
 $('chart-caption').textContent=$('site').value==='all'?'Agua y energía sumadas entre sitios; PUE ponderado por energía IT.':'Intervalos horarios del sitio seleccionado. Fechas en UTC.';
 const body=clear('timeline-table');rows.forEach(r=>body.append(row([date(r.timestamp),fmt(r.water_l),fmt(r.energy_total_kwh),fmt(r.pue,3),r.alerts])));
 if(!rows.length){host.append(el('p','No hay datos para graficar.','empty'));return;}
 const w=1000,h=245,left=62,right=16,top=20,bottom=35,iw=w-left-right,ih=h-top-bottom;
 const max=Math.max(...rows.map(r=>r[key]||0),.001)*1.12;
 const x=i=>left+(rows.length===1?iw/2:i/(rows.length-1)*iw),y=v=>top+ih-(v||0)/max*ih;
 const chart=svg('svg',{viewBox:`0 0 ${w} ${h}`,role:'img','aria-label':`${$('chart-metric').selectedOptions[0].textContent}. ${rows.length} intervalos. Consulta los valores en la tabla.`});
 for(let i=0;i<=4;i++){let v=max*i/4;chart.append(svg('line',{x1:left,x2:w-right,y1:y(v),y2:y(v),stroke:'#e4ece8','stroke-dasharray':'3 4'}));chart.append(svg('text',{x:left-10,y:y(v)+4,'text-anchor':'end',fill:'#59716e','font-size':11},fmt(v,key==='pue'?2:0)));}
 const points=rows.map((r,i)=>`${x(i)},${y(r[key])}`).join(' ');
 chart.append(svg('polygon',{points:`${x(0)},${y(0)} ${points} ${x(rows.length-1)},${y(0)}`,fill:'#edf6f1'}));
 chart.append(svg('polyline',{points,fill:'none',stroke:'#007f76','stroke-width':2.5,'stroke-linejoin':'round'}));
 rows.forEach((r,i)=>{if(r.alerts||rows.length===1){const dot=svg('circle',{cx:x(i),cy:y(r[key]),r:3.7,fill:r.alerts?'#c77a21':'#007f76',stroke:'white','stroke-width':1});dot.append(svg('title',{},date(r.timestamp)+' · '+fmt(r[key],2)+' · '+r.alerts+' alertas'));chart.append(dot);}});
 [...new Set([0,Math.floor((rows.length-1)/3),Math.floor((rows.length-1)*2/3),rows.length-1])].forEach(i=>chart.append(svg('text',{x:x(i),y:h-7,'text-anchor':i===0?'start':i===rows.length-1?'end':'middle',fill:'#59716e','font-size':11},rows[i].timestamp.slice(8,10)+' oct '+rows[i].timestamp.slice(11,16))));host.append(chart);
}
$('chart-metric').addEventListener('change',renderChart);
function renderAlerts(){
 const host=clear('alerts'),all=report.alerts,total=Math.max(1,Math.ceil(all.length/8));
 if(!all.length){const d=el('div',null,'empty');d.append(el('strong','Sin alertas en esta selección.'),el('span','Esto no certifica que no existan anomalías.'));host.append(d);}
 all.slice(page*8,page*8+8).forEach(a=>{const b=el('button',null,'alert-row'+(a.id===selected?' selected':''));b.setAttribute('aria-pressed',String(a.id===selected));const head=el('div',null,'alert-top');head.append(el('b',a.site),el('span',date(a.timestamp),'muted'));b.append(head,el('div',a.reasons.join(' · '),'alert-reason'),el('div',[a.numeric_alert?'Señal numérica':null,a.ot_alert?'Evento OT':null].filter(Boolean).join(' + '),'alert-type'));b.addEventListener('click',()=>{selected=a.id;renderAlerts();renderEvidence();});host.append(b);});
 $('page-info').textContent=`${page+1} / ${total}`;$('prev').disabled=page===0;$('next').disabled=page>=total-1;
}
$('prev').addEventListener('click',()=>{page--;renderAlerts();});$('next').addEventListener('click',()=>{page++;renderAlerts();});
function renderEvidence(){
 const host=clear('evidence'),a=report.alerts.find(x=>x.id===selected);
 if(!a){host.append(el('div','Selecciona una alerta para revisar la evidencia.','empty'));return;}
 host.append(el('span','FICHA DE REVISIÓN · '+a.site,'eyebrow'),el('h2','Qué sabemos de este intervalo'),el('p',date(a.timestamp)+' · '+(a.split==='referencia'?'Referencia':'Evaluación'),'muted'));
 const notice=el('div',a.reasons.join('. ')+'.','notice');host.append(notice);
 const t=el('table'),thead=el('thead'),tr=el('tr');['Indicador','Observado','Mediana de referencia'].forEach(v=>tr.append(el('th',v)));thead.append(tr);const tb=el('tbody');[['PUE',a.pue,a.reference_medians[0]],['L/kWh IT',a.water_intensity,a.reference_medians[1]],['Entrada °C',a.inlet_temp_c,a.reference_medians[2]]].forEach(([n,v,b])=>tb.append(row([n,fmt(v,3),fmt(b,3)])));t.append(thead,tb);host.append(t,el('p',`Carga: ${fmt(a.load_pct)} % · Exterior: ${fmt(a.outdoor_temp_c)} °C · Agua: ${fmt(a.water_l)} L`,'footnote'));
 if(report.method==='forest')host.append(el('p',`Aislamiento: ${fmt(a.score,4)} · Umbral: ${fmt(a.threshold,4)}. No es probabilidad ni diagnóstico causal.`,'footnote'));
 host.append(el('h3','Siguiente comprobación humana'));const ul=el('ul');a.checks.forEach(c=>ul.append(el('li',c)));host.append(ul,el('p','Referencia: primeras 72 horas originales del mismo sitio. Sus medianas son contexto descriptivo. No se afirma una causa ni un ahorro.','footnote'));
}
function renderEvaluation(){
 const s=clear('eval-summary');[['Filas evaluadas',report.comparison.rules.n],['Anomalías numéricas',report.numeric_positives],['Eventos OT aparte',report.ot_events]].forEach(([n,v])=>{const span=el('span',n+': ');span.append(el('b',v));s.append(span);});
 const tb=clear('scores');Object.entries(report.comparison).forEach(([k,v])=>tb.append(row([k==='rules'?'Reglas numéricas':'Isolation Forest',v.tp,v.fp,v.fn,v.tn,pct(v.precision),pct(v.recall),fmt(v.f1,3)])));
 const errors=clear('errors');report.errors.slice(0,20).forEach(e=>errors.append(row([e.site,date(e.timestamp),e.result,e.scenario])));
 $('errors-caption').textContent=report.errors.length?`${report.errors.length} discrepancias con el detector seleccionado. Se muestran las primeras ${Math.min(20,report.errors.length)}; el informe JSON incluye todas.`:report.comparison.rules.n?'No hay discrepancias con las etiquetas numéricas en esta selección.':'No hay filas de evaluación en la selección.';
}
$('demo').addEventListener('click',async()=>{$('site').value='SIM-B';$('split').value='evaluacion';$('start').value='2026-10-12';$('end').value='2026-10-18';$('method').value='rules';activate('overview');await load();if(report)$('evidence').scrollIntoView({behavior:'instant',block:'center'});});
$('benchmark').addEventListener('click',async()=>{const b=$('benchmark'),host=clear('benchmark-result');b.disabled=true;host.textContent='Midiendo tres repeticiones en el servidor local…';try{const res=await fetch('/api/benchmark',{method:'POST'});const d=await res.json();if(!res.ok)throw new Error(d.error);host.replaceChildren();const t=el('table'),th=el('thead'),tr=el('tr');['Método','Mediana (ms)','Mínimo (ms)','Máximo (ms)'].forEach(x=>tr.append(el('th',x)));th.append(tr);const tb=el('tbody');Object.entries(d.results).forEach(([k,v])=>tb.append(row([k==='rules'?'Reglas':'Isolation Forest',fmt(v.wall_median*1000,3),fmt(v.wall_min*1000,3),fmt(v.wall_max*1000,3)])));t.append(th,tb);const wrap=el('div',null,'table-scroll');wrap.append(t);host.append(wrap,el('p',`Python ${d.python} · ${d.platform} · ${d.rows} filas · Entrenamiento inicial: ${fmt(d.training_seconds*1000,1)} ms.`, 'footnote'),el('p',d.scope+' '+d.limits,'footnote'));const save=el('button','Descargar medición JSON','button secondary');save.addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='aquaguard-medicion.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});host.append(save);}catch(e){host.textContent='No se pudo medir: '+e.message;}finally{b.disabled=false;}});
load();

function renderCyber(){
 const c=report.cyber, summary=clear('cyber-summary'), body=clear('cyber-events');
 [['Revisión conjunta',c.combined],['OT sin coincidencia',c.ot_only],['Numéricas sin OT cercano',c.operational_only_ids.length]].forEach(([label,n])=>summary.append(el('span',label+': '+n)));
 c.events.forEach(e=>body.append(row([e.site+' · '+date(e.timestamp),e.status==='combined_review'?'Revisar conjuntamente':'Evento OT sin coincidencia',e.reasons.filter(r=>r.includes('OT')).join('; '),e.related_ids.map(id=>id.split('|')[1]).join('; ')||'Ninguna en esta selección'])));
 $('cyber-empty').textContent=c.events.length?c.limitation:'No hay eventos OT en esta selección. No se generan coincidencias artificiales.';
}
