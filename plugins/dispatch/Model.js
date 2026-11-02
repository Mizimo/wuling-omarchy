.pragma library

function escaped(value) {
    return String(value).replace(/[&<>\"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
}
function score(value, query) {
    const v=String(value).toLowerCase(), q=query.toLowerCase();
    if(!q)return 1;
    if(v===q)return 100;
    if(v.indexOf(q)===0)return 80;
    if(v.split(/[\s\-·]+/).some(w=>w.indexOf(q)===0))return 60;
    if(v.indexOf(q)>=0)return 40;
    let at=0;for(const c of v)if(c===q[at])at++;
    return at===q.length?10:0;
}
function highlight(value, query, color) {
    const chars=Array.from(String(value)), q=Array.from(query.toLowerCase());let at=0,out="";
    for(const c of chars) {
        if(at<q.length && c.toLowerCase()===q[at]) { out+='<font color="'+color+'"><u>'+escaped(c)+'</u></font>';at++; }
        else out+=escaped(c);
    }
    return at===q.length?out:escaped(value);
}
function rows(data, mode, query) {
    if(mode==="apps")return (data.apps || []).map(a=>Object.assign({},a,{score:Math.max(score(a.name,query),score(a.detail,query),score(a.id,query))}))
        .filter(a=>a.score>0).sort((a,b)=>b.score-a.score || b.frecency-a.frecency || a.name.localeCompare(b.name));
    if(mode==="clip")return (data.clip || []).filter(a=>score(a.name,query)>0);
    if(mode==="run" || mode==="ask") {
        const recent=(data[mode] || []).filter(s=>s!==query && score(s,query)>0).map(s=>({id:s,name:s,recent:true}));
        return query.trim()?[{id:query,name:query,recent:false}].concat(recent):recent;
    }
    return [];
}

// Bounded arithmetic grammar; never eval/Function or a command interpreter.
function calculate(source) {
    const input=source.replace(/×/g,"*").replace(/÷/g,"/").replace(/\^/g,"**").trim();
    if(!input || input.length>512)return null;
    const tokens=input.match(/(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?|\*\*|[()+\-*/%]|\s+|./gi) || [];
    const values=tokens.filter(t=>!/^\s+$/.test(t));let at=0,depth=0;
    function primary() {
        if(++depth>32)throw Error("depth");
        let n,token=values[at++];
        if(token==="(") { n=add();if(values[at++]!==")")throw Error("parenthesis"); }
        else if(token && /^(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(token))n=Number(token);
        else throw Error("number");
        depth--;return n;
    }
    function unary() {
        if(values[at]==="+" || values[at]==="-") { const sign=values[at++];if(++depth>32)throw Error("depth");const n=unary();depth--;return sign==="-"?-n:n; }
        let n=primary();if(values[at]==="**") { at++;if(++depth>32)throw Error("depth");n=Math.pow(n,unary());depth--; }return n;
    }
    function product() { let n=unary();while(["*","/","%"].indexOf(values[at])>=0) { const op=values[at++],r=unary();n=op==="*"?n*r:op==="/"?n/r:n%r; }return n; }
    function add() { let n=product();while(values[at]==="+" || values[at]==="-") { const op=values[at++],r=product();n=op==="+"?n+r:n-r; }return n; }
    try { const n=add();return at===values.length && Number.isFinite(n)?String(Number(n.toPrecision(12))):null; }catch(_) { return null; }
}
