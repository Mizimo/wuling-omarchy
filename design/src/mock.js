// WULING for Omarchy — mockup builder. One page, every screen:
//   mock.html?screen=empty|desk|terminal|comms|power|agents&dir=field|hud&theme=mist|paper   (terminal also takes &media=1)
// The bar always draws Omarchy's default layout (config/omarchy/shell.json, 4.0.6):
//   left  [omarchy.menu, omarchy.workspaces]
//   center[omarchy.indicators, omarchy.clock (anchor), omarchy.keyboard-layout, omarchy.weather, omarchy.system-update]
//   right [omarchy.tray, omarchy.agents, omarchy.bluetooth, omarchy.network, omarchy.audio, omarchy.monitor, omarchy.power]
// plus WULING's own bar widgets: wuling.window, wuling.terminal, wuling.power.
// WULING draws the menu cell, workspaces, window title, clock face, Terminal and power cells. Everything else is Omarchy's own widget,
// so it looks like one: a 27 px icon slot, no labels. Keyboard layout and update only show when they have something to say.
// Demo data is neutral: no real names, addresses or hosts.
const Q = new URLSearchParams(location.search);
const DIR = Q.get('dir') || 'field', THEME = Q.get('theme') || 'mist', SCREEN = Q.get('screen') || 'desk';
document.documentElement.classList.add(DIR);
if (THEME === 'paper') document.documentElement.classList.add('paper');

const GLYPH = (c = 'currentColor', s = 30) => `<svg viewBox="0 0 30 30" width="${s}" height="${s}" style="display:block;color:${c}">
  <defs><clipPath id="tri${s}"><path d="M6.2 9.6H23.8L15 25Z"/></clipPath></defs>
  <g fill="none" stroke="currentColor"><path d="M6.2 9.6H23.8L15 25Z" stroke-width="1.6"/>
  <g clip-path="url(#tri${s})" stroke-width=".9"><path d="M5 13.2C9 11.8 11.5 14.6 15 13.4S21 11.6 25 13"/>
  <path d="M5 16.4C8.6 15.2 11.8 17.8 15.4 16.6S21.4 15 25 16.2"/><path d="M5 19.6C9.4 18.4 12 20.8 15.6 19.8S21 18.6 25 19.6"/></g>
  <path d="M6.2 6.6H12.6M17.4 6.6H23.8" stroke-width="1.2"/></g><rect x="13.2" y="5.4" width="3.6" height="2.4" fill="currentColor"/></svg>`;
// icons: Material Symbols ligatures; a packed page maps names to codepoints (window.ICONS) so its font can be subset
const ms = (n, st = '') => `<span class="msym" style="${st}">${(window.ICONS && window.ICONS[n]) || n}</span>`;
const stack = (l, v, cls = '') => `<div class="stack ${cls}"><span class="lbl">${l}</span><span class="val">${v}</span></div>`;
const S = (h) => (document.querySelector('.stage') || document.body).insertAdjacentHTML('beforeend', h);

// ------------------------------------------------------------------ bar
function bar(o = {}) {
  const hudp = DIR === 'hud';
  const menu = hudp ? `<div class="menu">${GLYPH('#0E1211', 30)}<b>EF</b></div>` : `<div class="menu">${GLYPH('#0E1211', 30)}</div>`;
  const ws = (o.ws || ['active', 'occ', 'occ', '', '']).map((s, i) =>
    `<span class="cell ${s}">${String(i + 1).padStart(2, '0')}</span>`).join('');
  const left = `${menu}${stack('Wuling · 武陵', 'KJR-01', 'ident')}<i class="sep opt"></i><div class="ws">${ws}</div>
    ${o.title === false ? '' : `<i class="sep opt"></i>${stack(o.app || 'Terminal · 終端', o.title || '~/projects/field-notes', 'focus')}`}`;
  // center: indicators | clock (anchor) | keyboard · weather · update
  const ind = o.ind === false ? '' : `<div class="w native">${ms('bedtime')}</div>`;
  // the clock: a larger face drawn over Omarchy's own widget (its clicks and calendar still work)
  const clock = `<span class="clock">14:03</span>${stack('Sun 週日', '11.01', 'date')}`;
  const wx = `<div class="w native">${ms('partly_cloudy_day')}</div>`;
  const upd = o.upd === false ? '' : `<div class="w native">${ms('sync')}</div>`;
  // right: Omarchy's widgets in Omarchy's order
  const tray = `<div class="w native">${ms('chevron_left', 'font-size:15px;color:var(--mist-5)')}</div>`;
  const agent = `<div class="w native">${ms('smart_toy')}</div>`;
  const bt = `<div class="w native">${ms('bluetooth')}</div>`;
  const net = `<div class="w native">${ms('wifi')}</div>`;
  const aud = `<div class="w native">${ms('volume_up')}</div>`;
  const mon = `<div class="w native">${ms('desktop_windows')}</div>`;
  const pw = `<div class="w native"><span class="bat"><span class="cell"><i></i><i></i><i></i><i></i><i class="off"></i></span></span></div>`;
  const trm = `<div class="trm ${o.trmOn ? 'on' : ''}">${ms('side_navigation')}${stack('Terminal', '終端')}</div>`;
  const pwr = `<div class="pwr">${ms('power_settings_new')}</div>`;
  S(`<div class="bar">
    <div class="sec left">${left}</div>
    <div class="sec center"><div class="flank-l">${ind}</div><div class="anchor">${clock}</div><div class="flank-r">${wx}${upd}</div></div>
    <div class="sec right">${tray}${agent}${bt}${net}${aud}${mon}${pw}${trm}${pwr}</div></div>`);
}

// ------------------------------------------------------------------ Hyprland: two tiled windows
function windows() {
  // Omarchy's default Hyprland geometry: gaps_out 10, gaps_in 5, border 2, no rounding
  const top = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--bar-h')) + 10;
  const h = 768 - top - 10, wl = 668, xr = 688;
  const prompt = (p, t = '') => `<span class="k">▌</span><span class="w">${p}</span> <span class="f">${'─'.repeat(52)}</span> <span class="m">${t}</span>`;
  S(`<div class="win focus" style="left:10px;top:${top}px;width:${wl}px;height:${h}px">
<div class="term">${prompt('~', '14:02:51')}
<span class="k">❯</span> <span class="w">fastfetch</span>
</div><div style="display:flex;gap:18px;padding:0 12px 4px">
<img class="fflogo" src="../assets/fastfetch-logo.png" width="132" height="268" style="display:block;flex:none;border-right:1px solid var(--t-faint);padding-right:12px;box-sizing:content-box">
<div class="term" style="padding:0"><span class="m">ENDFIELD INDUSTRIES — FIELD TERMINAL</span>
<span class="w" style="font-weight:600">operator</span><span class="m">@</span><span class="k" style="font-weight:600">field-terminal</span>
<span class="f">──────────────────────────────────────</span>
<span class="kk">SYS</span>  <span class="m">系統</span>  Omarchy 4.0.6 · Arch Linux
<span class="kk">KRN</span>  <span class="m">核心</span>  Linux 7.2.8-omarchy
<span class="kk">WM </span>  <span class="m">視窗</span>  Hyprland 0.56 · wayland
<span class="kk">SHL</span>  <span class="m">殼層</span>  omarchy-shell · WULING
<span class="kk">TRM</span>  <span class="m">終端</span>  Foot
<span class="kk">CPU</span>  <span class="m">處理</span>  4 threads @ 3.0 GHz
<span class="kk">MEM</span>  <span class="m">記憶</span>  3.1 / 7.0 GiB  <span class="k">■■■■</span><span class="f">■■■■■■</span> <span class="m">44%</span>
<span class="kk">DSK</span>  <span class="m">儲存</span>  32 / 237 GiB   <span class="k">■</span><span class="f">■■■■■■■■■</span> <span class="m">14%</span>
<span class="kk">BAT</span>  <span class="m">電源</span>  <span class="g">87%</span> · AC
<span class="kk">UP </span>  <span class="m">運轉</span>  2h 18m

<span style="display:inline-flex"><i style="display:inline-block;width:18px;height:11px;background:#151B1A"></i><i style="display:inline-block;width:18px;height:11px;background:#E3432F"></i><i style="display:inline-block;width:18px;height:11px;background:#62D9A6"></i><i style="display:inline-block;width:18px;height:11px;background:#FEF700"></i><i style="display:inline-block;width:18px;height:11px;background:#4C93C6"></i><i style="display:inline-block;width:18px;height:11px;background:#C65D7B"></i><i style="display:inline-block;width:18px;height:11px;background:#49B9C2"></i><i style="display:inline-block;width:18px;height:11px;background:#C9D2CD"></i></span></div></div>
<div class="term" style="padding-top:2px">${prompt('~', '14:03:07')}
<span class="k">❯</span> <span class="cursor"> </span></div></div>`);
  const L = (n, html, cur) => `<span class="${cur ? 'cur' : ''}"><span class="ln">${n}</span>${html}</span>`;
  const code = [
    `<span class="kw">import</span> <span class="id">QtQuick</span>`,
    `<span class="kw">import</span> <span class="str">"../kit"</span> <span class="kw">as</span> <span class="ty">Kit</span>`,
    ``,
    `<span class="cm">// wuling.terminal — one tile per quick toggle; data from \`wuling status --json\`</span>`,
    `<span class="ty">Kit.Panel</span> {`,
    `    <span class="pr">id</span>: <span class="id">root</span>`,
    `    <span class="pr">title</span>: <span class="str">"TERMINAL · 終端"</span>`,
    `    <span class="pr">width</span>: <span class="ty">Kit.Tokens</span>.<span class="id">panelWidth</span>`,
    ``,
    `    <span class="kw">property</span> <span class="ty">var</span> <span class="id">status</span>: <span class="ty">Kit.Status</span>.<span class="id">latest</span>`,
    ``,
    `    <span class="ty">Kit.Section</span> {`,
    `        <span class="pr">index</span>: <span class="num">3</span>`,
    `        <span class="pr">label</span>: <span class="str">"LINK · 連線"</span>`,
    `        <span class="ty">Grid</span> {`,
    `            <span class="pr">columns</span>: <span class="num">3</span>`,
    `            <span class="ty">Repeater</span> {`,
    `                <span class="pr">model</span>: <span class="id">root</span>.<span class="id">status</span>.<span class="id">links</span>`,
    `                <span class="ty">Kit.Tile</span> {`,
    `                    <span class="pr">icon</span>: <span class="id">modelData</span>.<span class="id">icon</span>`,
    `                    <span class="pr">on</span>: <span class="id">modelData</span>.<span class="id">active</span>`,
    `                    <span class="pr">onClicked</span>: <span class="ty">Kit.Run</span>.<span class="id">omarchy</span>(<span class="id">modelData</span>.<span class="id">toggle</span>)`,
    `                }`,
    `            }`,
    `        }`,
    `    }`,
    `}`,
  ];
  S(`<div class="win" style="left:${xr}px;top:${top}px;width:${wl}px;height:${h}px"><div class="nv">
    <div class="tabs"><span class="on">Terminal.qml</span><span>Tile.qml</span><span>tokens.toml</span></div>
    <div class="code">${code.map((c, i) => L(i + 1, c, i === 21)).join('\n')}</div>
    <div class="st"><span class="mode">NORMAL</span><span>⎇ main</span><span style="margin-left:auto">qml</span><span>22:44</span></div></div></div>`);
}

// ------------------------------------------------------------------ the hud preset's HUD on the background image
// ------------------------------------------------------------------ TERMINAL panel
function terminal(o = {}) {
  const top = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--bar-h')) + 10;
  const sh = (no, en, zh, rt = '') => `<div class="sh"><span class="no">${no}</span><span class="t">${en}<em>${zh}</em></span><span class="rl"></span><span class="rt">${rt}</span></div>`;
  const tile = (ic, lbl, v, on) => `<div class="tile ${on ? 'on' : ''}"><div class="tp">${ms(ic)}<span class="micro">${lbl}</span></div><div class="v">${v}</div></div>`;
  const segs = (n, on, cls = '') => `<div class="segs ${cls}">${Array.from({ length: n }, (_, i) => `<i class="${i < on ? 'on' : ''}"></i>`).join('')}</div>`;
  const spark = (c, pts) => `<svg width="96" height="16" viewBox="0 0 96 16"><polyline fill="none" stroke="${c}" stroke-width="1" points="${pts}"/></svg>`;
  let sec = o.media ? 5 : 4; const n = () => String(++sec).padStart(2, '0');
  S(`<div class="trmp" style="top:${top}px;bottom:10px">
    <div class="hdband">Field Terminal<span class="sp"></span>KJR-01</div>
    <section>${sh('02', 'Terminal', '終端', 'Operator')}
      <div class="clk"><span class="big">14:03</span><span class="sec">:07</span>
        <div class="dt"><div class="micro">2026 · Sun 週日</div><div class="d">11.01 · JST</div><div class="micro" style="margin-top:4px">Uptime 2H 18M</div></div></div></section>
    <section>${sh('03', 'Link', '連線')}
      <div class="tiles">${tile('wifi', 'Wi-Fi', 'field-net', 1)}${tile('bluetooth', 'BT', 'Off 關閉', 0)}${tile('hub', 'Tailnet', 'Connected', 1)}
        ${tile('do_not_disturb_on', 'DND', '勿擾 Off', 0)}${tile('bedtime', 'Night', '夜光 On', 1)}${tile('speed', 'Power', '平衡 Balanced', 0)}</div></section>
    <section>${sh('04', 'Levels', '調節')}
      <div class="lv">${ms('volume_up')}${segs(24, 10)}<span class="n">40</span></div>
      <div class="lv">${ms('brightness_6')}${segs(24, 17, 'paper')}<span class="n">72</span></div></section>
    ${o.media ? `<section>${sh('05', 'Signal', '訊號', '● Playing')}
      <div class="sig"><div class="art">MSR</div><div style="flex:1"><div class="tt">Quiet Survey</div><div class="ar">Field Recordings · Vol. 2</div><div class="pg"><i style="width:34%"></i></div></div></div></section>` : ''}
    <section>${sh(n(), 'Agent', '代理', 'Super+Shift+Ctrl+A')}
      ${[['Claude', 'Max', 37, 58, '1h 12m'], ['Codex', 'Pro', 12, 31, '3h 40m']].map(([nm, t, a, b, r]) => `<div class="agt"><span class="nm">${nm}<small>${t}</small></span><div class="bars">
        <div class="row"><span class="micro">Session</span><span class="m"><i style="width:${a}%"></i></span><span class="p">${a}%</span></div>
        <div class="row"><span class="micro">Week</span><span class="m"><i style="width:${b}%"></i></span><span class="p">${b}%</span></div></div><span class="rs">${r}</span></div>`).join('')}
      <div class="ask">${ms('smart_toy', 'font-size:14px;color:var(--paper-2)')}<span>Open default agent</span><b>Claude</b></div></section>
    <section>${sh(n(), 'Telemetry', '遙測')}
      <div class="tel"><div><div class="micro">CPU 處理</div><div class="v">12%</div>${spark('var(--accent-ink)', '0,12 10,11 20,13 30,9 40,10 50,7 60,9 70,8 80,10 96,6')}</div>
        <div><div class="micro">MEM 記憶</div><div class="v">3.1<small> / 7.0G</small></div>${spark('var(--paper-2)', '0,9 20,9 40,8 60,8 80,8 96,7')}</div>
        <div><div class="micro">Temp 溫度</div><div class="v">48°</div>${spark('var(--jade)', '0,10 16,10 32,9 48,11 64,10 80,9 96,9')}</div></div></section>
    <section style="border-bottom:none">${sh(n(), 'Comms log', '通訊紀錄', '3 則')}
      <div class="log"><div class="it"><span class="a">System</span>Process crashed: firefox<span class="tm">14:01</span></div><div class="it"><span class="a">Update</span>3 packages ready<span class="tm">13:58</span></div>
        <div class="it"><span class="a">Calendar</span>Review at 15:00<span class="tm">13:40</span></div></div></section>
    <div class="foot">${[['lock', 'Lock'], ['bedtime', 'Sleep'], ['logout', 'Exit', 1], ['restart_alt', 'Reboot', 1], ['power_settings_new', 'Off', 1]]
      .map(([i, l, d]) => `<div class="pb ${d ? 'd' : ''}">${ms(i)}<span class="micro">${l}</span></div>`).join('')}</div>
  </div>`);
}

// ------------------------------------------------------------------ COMMS + OSD
function comms() {
  const hudp = DIR === 'hud';
  const top = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--bar-h')) + 10;
  const toast = (cls, app, time, ic, icc, sum, body, acts, life) => `<div class="toast ${cls}" style="right:10px;top:${top + toast.y}px">
    <div class="hd"><span class="micro">Comms · 通訊</span><span class="micro app">${app}</span><span class="micro" style="margin-left:auto">${time}</span>${ms('close', 'font-size:14px;margin-left:6px;color:var(--mist-5)')}</div>
    <div class="bd"><div class="art">${ms(ic, `font-size:20px;color:${icc}`)}</div><div><div class="sum">${sum}</div><div class="body">${body}</div></div></div>
    ${acts ? `<div class="acts">${acts}</div>` : ''}${life ? `<i class="life" style="width:${life}%"></i>` : ''}</div>`;
  toast.y = 0;
  S(toast('imp', 'System update', '14:02', 'system_update_alt', 'var(--accent-ink)', '有 3 個更新 · 3 updates ready', 'omarchy 4.0.7 · hyprland · mesa', `<span class="btn pri">Update 更新</span><span class="btn">Later</span>`, 62));
  toast.y = 128;
  S(toast('', 'Agent', '13:58', 'smart_toy', 'var(--jade)', '任務完成 · Task finished', 'Refactor of the status reader is ready for review.', '', 0));
  const w = hudp ? 380 : 316;
  const segs = (n, on) => `<div class="segs">${Array.from({ length: n }, (_, i) => `<i class="${i < on ? 'on' : ''}"></i>`).join('')}</div>`;
  S(`<div class="osd" style="left:${683 - w / 2}px;bottom:32px">${ms('volume_up', 'font-size:18px;color:var(--paper-1)')}
    <div class="stack" style="gap:5px"><span class="micro" style="font-size:8px">${hudp ? 'Audio out · Speakers' : 'Vol · 音量'}</span>${segs(hudp ? 22 : 20, hudp ? 9 : 8)}</div>
    <span class="num">40</span></div>`);
}

// ------------------------------------------------------------------ agents: Omarchy's own crash notification, drawn as a WULING toast
function crash(right) {
  const top = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--bar-h')) + 10;
  S(`<div class="toast crit" style="right:${right}px;top:${top}px">
    <div class="hd"><span class="micro">Comms · 通訊</span><span class="micro app">System</span><span class="micro" style="margin-left:auto">14:01</span>${ms('close', 'font-size:14px;margin-left:6px;color:var(--mist-5)')}</div>
    <div class="bd"><div class="art">${ms('bug_report', 'font-size:20px;color:var(--vermilion)')}</div><div><div class="sum">Process crashed: firefox</div><div class="body">Click to diagnose with AI</div></div></div></div>`);
}

// ------------------------------------------------------------------ TERMINATION (Omarchy's System menu entries)
function power() {
  const items = [['01', 'S', 'monitor', 'Screensaver', '螢幕保護'], ['02', 'L', 'lock', 'Lock', '鎖定'], ['03', 'U', 'bedtime', 'Suspend', '睡眠'],
    ['04', 'H', 'downloading', 'Hibernate', '休眠'], ['05', 'E', 'logout', 'Logout', '登出', 1], ['06', 'R', 'restart_alt', 'Reboot', '重新啟動 · 長按確認', 1, 1],
    ['07', 'P', 'power_settings_new', 'Shutdown', '關機', 1]];
  S(`<div class="term-p"><div class="kick"><span class="no">04</span><span class="micro">Termination protocol</span></div>
    <div class="ttl">終止協議</div>
    <div class="cards">${items.map(([n, k, ic, en, zh, d, sel]) => `<div class="card ${d ? 'd' : ''} ${sel ? 'sel' : ''}">
      <span class="n">${n}</span><span class="key">${k}</span><span class="ic">${ms(ic, 'font-size:24px;color:inherit')}</span><span class="en">${en.toUpperCase()}</span><span class="zh">${zh}</span>
      ${sel ? `<i class="hold" style="width:58%"></i>` : ''}</div>`).join('')}</div>
    <div class="hints micro"><span>←→ Select</span><span><b>Hold ↵</b> Confirm 0.8s</span><span><b>Esc</b> Abort</span><span class="rt">Same entries as Omarchy · System</span></div></div>`);
}

// ------------------------------------------------------------------ compose
document.addEventListener('DOMContentLoaded', () => {
  const dimmed = SCREEN === 'power' || SCREEN === 'proto';
  S(`<div class="screen ${dimmed ? 'dim' : ''}"></div>`);
  if (SCREEN === 'empty') bar({ title: false, ws: ['active', '', '', '', ''] });
  if (SCREEN === 'desk' || SCREEN === 'comms') { bar(); windows(); }
  if (SCREEN === 'comms') comms();
  if (SCREEN === 'terminal' || SCREEN === 'agents') { bar({ title: false, ws: ['active', 'occ', '', '', ''], trmOn: true }); terminal({ media: Q.get('media') === '1' }); }
  if (SCREEN === 'agents') crash(392);
  if (SCREEN === 'power') { bar({ title: false, ind: false, upd: false }); power(); }
  if (SCREEN === 'proto') bar({ title: false, ind: false, upd: false });
  // Omarchy's centerAnchor: the clock sits at the exact centre and the rest of the centre section flanks it
  const a = document.querySelector('.bar .anchor');
  if (a) document.querySelector('.bar').style.setProperty('--anchor-half', (a.offsetWidth / 2 + 12) + 'px');
  document.body.dataset.ready = '1';
});
