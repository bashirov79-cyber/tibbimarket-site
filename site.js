(function(){
var root=document.documentElement;root.classList.add('js');
function $(id){return document.getElementById(id)}

/* A freshly opened page starts at its top; back/forward keeps the browser's own position.
   Inside an embedding frame (a preview window) the host may keep its old scroll offset, so there the page
   also asks to be brought to its top again while it loads, until the visitor starts scrolling. */
(function(){
  var framed=false;try{framed=window.self!==window.top}catch(e){framed=true}
  var nav=null;try{nav=performance.getEntriesByType('navigation')[0]}catch(e){}
  var fresh=!location.hash&&(!nav||nav.type==='navigate'||framed&&nav.type!=='back_forward');
  function up(){try{window.scrollTo(0,0)}catch(e){}
    try{document.documentElement.scrollTop=0;if(document.body)document.body.scrollTop=0}catch(e){}
    var h=document.querySelector('.util');if(framed&&h&&h.scrollIntoView){try{h.scrollIntoView({block:'start',behavior:'instant'})}catch(e){h.scrollIntoView(true)}}}
  if(!fresh)return;
  up();
  if(!framed)return;
  try{history.scrollRestoration='manual'}catch(e){}
  var stop=false,timers=[0,60,200,500,1000,1800].map(function(ms){return setTimeout(function(){if(!stop)up()},ms)});
  function quit(){stop=true;timers.forEach(clearTimeout)}
  ['wheel','touchstart','keydown','pointerdown'].forEach(function(t){window.addEventListener(t,quit,{passive:true,once:true})});
  window.addEventListener('load',function(){if(!stop)up()});
  /* leaving for another page of the site: bring this one to its top first, in case the frame's host keeps the offset */
  document.addEventListener('click',function(ev){
    if(ev.defaultPrevented||ev.button||ev.metaKey||ev.ctrlKey||ev.shiftKey||ev.altKey)return;
    var a=ev.target.closest&&ev.target.closest('a[href]');if(!a||a.target==='_blank')return;
    var href=a.getAttribute('href');if(!href||href.charAt(0)==='#'||/^(https?:|mailto:|tel:)/.test(href))return;
    stop=true;window.scrollTo(0,0);var h=document.querySelector('.util');if(h&&h.scrollIntoView)h.scrollIntoView(true)},true);
})();

/* back-to-top button */
var tt=$('totop');
if(tt){var seen=false,tick=function(){var on=(window.pageYOffset||root.scrollTop)>window.innerHeight*1.5;if(on!==seen){seen=on;tt.hidden=!on}};
  window.addEventListener('scroll',tick,{passive:true});window.addEventListener('resize',tick);tick();
  tt.addEventListener('click',function(){window.scrollTo(0,0);var b=document.querySelector('.brand');if(b)b.focus({preventScroll:true})})}

/* catalogue menu on phones and tablets */
var mb=$('mbtn');
function menu(o){root.classList.toggle('m-open',o);if(mb)mb.setAttribute('aria-expanded',o?'true':'false')}
if(mb)mb.addEventListener('click',function(){menu(!root.classList.contains('m-open'))});

/* search: the index is fetched the first time the field is used */
var f=$('q'),box=$('qres'),form=$('qform');
if(f&&box&&form){
  var D=null,wait=null,base=form.getAttribute('data-base')||'';
  var fold=function(s){s=s.toLowerCase().replace(/̇/g,'');var m={'ə':'e','ı':'i','ö':'o','ü':'u','ş':'s','ç':'c','ğ':'g','ё':'е'};return s.replace(/[əıöüşçğё]/g,function(c){return m[c]})};
  var load=function(){return wait||(wait=fetch(form.getAttribute('data-src')).then(function(r){return r.json()}).then(function(d){D=d;run()}).catch(function(){wait=null}))};
  var close=function(){box.hidden=true;box.innerHTML=''};
  var run=function(){
    var q=fold(f.value.trim());if(q.length<2){close();return}
    if(!D){load();return}
    var t=q.split(/\s+/),r=[];
    D.forEach(function(p){if(t.every(function(x){return p.h.indexOf(x)>-1})){var s=p.n.indexOf(t[0]);r.push([s===0?0:s>0?1:2,p])}});
    r.sort(function(a,b){return a[0]-b[0]});
    box.innerHTML=r.length?r.slice(0,10).map(function(x){var p=x[1];return '<li><a href="'+base+p.u+'">'+(p.i?'<img src="'+base+p.i+'" alt="" width="44" height="44">':'')+'<span><b>'+p.t+'</b><small>'+p.k+'</small></span></a></li>'}).join(''):'<li class="none">'+form.getAttribute('data-none')+'</li>';
    box.hidden=false};
  f.addEventListener('input',run);f.addEventListener('focus',function(){load();run()});
  form.addEventListener('submit',function(ev){ev.preventDefault();var a=box.querySelector('a');if(a)location.href=a.href;else{load();run()}});
  form.addEventListener('keydown',function(ev){
    var links=[].slice.call(box.querySelectorAll('a')),i=links.indexOf(document.activeElement);
    if(ev.key==='ArrowDown'&&links.length){ev.preventDefault();links[Math.min(i+1,links.length-1)].focus()}
    else if(ev.key==='ArrowUp'&&links.length){ev.preventDefault();if(i<=0)f.focus();else links[i-1].focus()}
    else if(ev.key==='Escape'){close();f.blur()}});
  document.addEventListener('click',function(ev){if(!form.contains(ev.target))close()});
}

/* request list: kept in this browser; falls back to memory when storage is unavailable */
var dlg=$('ldlg');if(!dlg)return;
var KEY='tm-list',mem=null,T=dlg.dataset;
function read(){if(mem)return mem;try{var v=JSON.parse(localStorage.getItem(KEY)||'[]');mem=Array.isArray(v)?v:[]}catch(e){mem=[]}return mem}
function write(v){mem=v;try{localStorage.setItem(KEY,JSON.stringify(v))}catch(e){}paint()}
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function text(v){return T.hello+'\n'+v.map(function(x,i){return (i+1)+'. '+x.n+(x.q>1?' × '+x.q:'')}).join('\n')+'\n\n'+T.end}
var items=$('litems'),empty=$('lempty'),foot=$('lfoot'),count=$('lcount'),wa=$('lwa'),mail=$('lmail');
function paint(){
  var v=read(),ids={};v.forEach(function(x){ids[x.id]=1});
  [].forEach.call(document.querySelectorAll('[data-add]'),function(b){
    var on=!!ids[b.getAttribute('data-add')];b.setAttribute('aria-pressed',on?'true':'false');
    var l=b.querySelector('.t');if(l)l.textContent=on?(b.getAttribute('data-on')||T.ladded):(b.getAttribute('data-off')||T.ladd)});
  var n=v.reduce(function(s,x){return s+x.q},0);
  count.textContent=n;count.hidden=!n;
  empty.hidden=!!v.length;foot.hidden=!v.length;
  items.innerHTML=v.map(function(x){return '<li data-id="'+esc(x.id)+'"><span class="nm">'+esc(x.n)+'</span>'+
    '<span class="qty"><button type="button" data-q="-1" aria-label="'+esc(T.less)+'">−</button><output>'+x.q+'</output><button type="button" data-q="1" aria-label="'+esc(T.more)+'">+</button></span>'+
    '<button type="button" class="link rm" data-rm>'+esc(T.remove)+'</button></li>'}).join('');
  if(v.length){var m=text(v);wa.href='https://wa.me/'+T.wa+'?text='+encodeURIComponent(m);
    mail.href='mailto:'+T.mail+'?subject='+encodeURIComponent(T.subject)+'&body='+encodeURIComponent(m)}
}
document.addEventListener('click',function(ev){
  var b=ev.target.closest('[data-add]');
  if(b){var id=b.getAttribute('data-add'),v=read().slice(),i=v.findIndex(function(x){return x.id===id});
    if(i>-1)v.splice(i,1);else v.push({id:id,n:b.getAttribute('data-name'),q:1});write(v);return}
  var li=ev.target.closest('#litems li');
  if(li){var id2=li.getAttribute('data-id'),v2=read().slice(),j=v2.findIndex(function(x){return x.id===id2});if(j<0)return;
    var q=ev.target.closest('[data-q]');
    if(q){v2[j]={id:v2[j].id,n:v2[j].n,q:Math.max(1,Math.min(999,v2[j].q+Number(q.getAttribute('data-q'))))};write(v2)}
    else if(ev.target.closest('[data-rm]')){v2.splice(j,1);write(v2)}}
});
$('lbtn').addEventListener('click',function(){paint();if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','')});
$('lclose').addEventListener('click',function(){dlg.close?dlg.close():dlg.removeAttribute('open')});
$('lclear').addEventListener('click',function(){write([])});
dlg.addEventListener('click',function(ev){if(ev.target===dlg)dlg.close()});
window.addEventListener('storage',function(ev){if(ev.key===KEY){mem=null;paint()}});
paint();
})();
