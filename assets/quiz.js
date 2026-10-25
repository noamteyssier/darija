// A drill card: prompt, choose-or-type answer, feedback, and a table after answering.
// Missed items get heavier and come back more often; weights are saved per drill.
// A drill can pass traits(item) (e.g. pronoun, tense, verb type): then misses weigh the traits (weight = sqrt of their product), not the item.
import { $, prefs, disp, norm, shuffle, load, bindSeg, scriptSeg, esc } from './common.js';

const STATS = '<div class="stats" aria-live="polite"><span>Today <b data-s="right">0</b>/<b data-s="total">0</b></span><span>Streak <b data-s="streak">0</b></span><span>Best <b data-s="best">0</b></span><span>Weak <b data-s="weak">0</b></span><span data-s="pool"></span></div>';

export function quiz(root, { name, pool, render, onSettings, traits }) {
  const saved = load(name, { weights: {}, traits: {}, best: 0 });
  const sess = { right: 0, total: 0, streak: 0 };
  let item = null, view = null, answered = false, ok = false, lastKey = '', tab = null;

  root.innerHTML = STATS
    + '<div class="settings"><div class="seg" role="group" aria-label="Answer style" data-group="mode"><button type="button" data-val="choose">Choose</button><button type="button" data-val="type">Type</button></div>'
    + scriptSeg() + '</div>'
    + '<section class="card" aria-live="polite">'
    + '<p class="note" data-q="empty" hidden>Nothing in this set yet. Pick at least one group above.</p><div data-q="main" style="display:contents">'
    + '<div class="chips"><span class="chip" data-q="chip"></span><span class="gloss" data-q="gloss"></span></div>'
    + '<div class="word" data-q="word"></div><p class="ask" data-q="ask"></p>'
    + '<div class="opts" data-q="opts"></div>'
    + '<form class="type" data-q="form" autocomplete="off" hidden><label>Type it in arabizi or Arabic script</label>'
    + '<input type="text" data-q="answer" inputmode="text" autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="done">'
    + '<button class="btn" type="submit" data-q="check">Check</button></form>'
    + '<div class="fb" data-q="fb" hidden></div><div data-q="after" hidden></div>'
    + '<button class="btn" type="button" data-q="next" hidden>Next</button></div></section>'
    + '<div class="foot"><p class="note">Missed answers come back more often. Progress is saved in this browser only. Typed answers ignore schwa (e), doubled letters and spaces, and accept the book letters š x ġ ع н.</p>'
    + '<button class="btn ghost" type="button" data-q="reset">Reset progress for this drill</button></div>';

  const q = k => root.querySelector('[data-q="' + k + '"]');
  const s = k => root.querySelector('[data-s="' + k + '"]');
  const w1 = (m, k) => (typeof m[k] === 'number' ? m[k] : 1);
  // With traits, "Weak" counts weak traits (pronouns, tenses, verb types) in the set, not items.
  const weight = c => (traits ? Math.sqrt(traits(c).reduce((a, t) => a * w1(saved.traits, t), 1)) : w1(saved.weights, c.key));

  // A trait is weak when it is high and clearly above the rest of its kind (the first letter of its name),
  // so a weak pronoun that drags every tense up with it does not flag all the tenses too.
  function weakTraits(p) {
    const byKind = {};
    for (const t of new Set(p.flatMap(traits))) (byKind[t[0]] = byKind[t[0]] || []).push(w1(saved.traits, t));
    return Object.values(byKind).reduce((n, ws) => {
      const mean = ws.reduce((a, b) => a + b, 0) / ws.length;
      return n + ws.filter(w => w > 1.5 && w > 1.5 * mean).length;
    }, 0);
  }

  function stats() {
    const p = pool();
    s('right').textContent = sess.right;
    s('total').textContent = sess.total;
    s('streak').textContent = sess.streak;
    s('best').textContent = saved.best;
    s('weak').textContent = traits
      ? weakTraits(p)
      : p.filter(c => weight(c) > 1.5).length;
    s('pool').textContent = p.length + ' in this set';
  }

  function pick() {
    const cs = pool().filter(c => c.key !== lastKey);
    if (!cs.length) return pool()[0] || null;
    let total = 0;
    cs.forEach(c => { total += weight(c); });
    let r = Math.random() * total;
    for (const c of cs) { r -= weight(c); if (r <= 0) return c; }
    return cs[cs.length - 1];
  }

  function draw() {
    q('main').hidden = !item;
    q('empty').hidden = !!item;
    if (!item) { stats(); return; }
    view = render(item);
    q('chip').innerHTML = view.chip || '';
    q('gloss').textContent = view.gloss || '';
    q('word').className = 'word' + (view.small ? ' small' : '');
    q('word').innerHTML = view.word ? disp(view.word.lat, view.word.ar) : '';
    const who = !view.ask.ar || prefs.script === 'latin' ? view.ask.lat : prefs.script === 'arabic' ? view.ask.ar : view.ask.lat + ' · ' + view.ask.ar;
    q('ask').innerHTML = '<span class="who"></span>' + (view.ask.en ? '<span class="en">(' + esc(view.ask.en) + ')</span>' : '');
    q('ask').querySelector('.who').textContent = who || '';
  }

  function next(forced) {
    item = forced || pick();
    answered = false;
    tab = null;
    lastKey = item ? item.key : '';
    q('fb').hidden = true; q('after').hidden = true; q('next').hidden = true;
    draw();
    if (!item) return;
    const opts = q('opts'), form = q('form');
    opts.innerHTML = '';
    if (prefs.mode === 'choose' || view.chooseOnly) {
      form.hidden = true; opts.hidden = false;
      const seen = new Set([view.answer.lat]);
      const items = [{ ...view.answer, ok: true }];
      for (const d of view.options) { // render() orders these: likeliest mix-ups first
        if (items.length >= (view.max || 4)) break;
        if (seen.has(d.lat)) continue;
        seen.add(d.lat);
        items.push({ ...d, ok: false });
      }
      (view.keepOrder ? items.sort((a, b) => view.order.indexOf(a.lat) - view.order.indexOf(b.lat)) : shuffle(items)).forEach(it => {
        const b = document.createElement('button');
        b.type = 'button'; b.className = 'opt';
        b.innerHTML = disp(it.lat, it.ar);
        b.dataset.ok = it.ok ? '1' : '0'; b.dataset.lat = it.lat; b.dataset.ar = it.ar;
        b.addEventListener('click', () => choose(b, it.ok));
        opts.appendChild(b);
      });
    } else {
      opts.hidden = true; form.hidden = false;
      const inp = q('answer');
      inp.value = ''; inp.disabled = false; q('check').hidden = false;
    }
    stats();
  }

  function grade(good) {
    if (traits) {
      for (const t of traits(item)) { const w = w1(saved.traits, t); saved.traits[t] = good ? Math.max(0.3, w * 0.9) : Math.min(8, w + 1); }
    } else {
      const k = item.key, w = w1(saved.weights, k);
      saved.weights[k] = good ? Math.max(0.3, w * 0.6) : Math.min(12, w + 3);
    }
    sess.total++;
    if (good) { sess.right++; sess.streak++; if (sess.streak > saved.best) saved.best = sess.streak; }
    else sess.streak = 0;
    saved.save();
    stats();
  }

  function result(good) {
    ok = good;
    const fb = q('fb');
    fb.className = 'fb ' + (good ? 'good' : 'bad');
    fb.innerHTML = '<strong>' + (good ? 'Correct' : 'Not quite. It is:') + '</strong><span class="ans">' + disp(view.answer.lat, view.answer.ar) + '</span>'
      + (view.why ? '<span class="why">' + esc(view.why) + '</span>' : '');
    fb.hidden = false;
    // after(good) returns html, or tabs [{ label, html, open }] where open marks the default tab.
    const after = view.after ? view.after(good) : '';
    const box = q('after');
    if (Array.isArray(after)) {
      const cur = tab ?? Math.max(0, after.findIndex(t => t.open));
      box.innerHTML = '<div class="seg" role="group" aria-label="Show">' + after.map((t, i) =>
        '<button type="button" data-tab="' + i + '" aria-pressed="' + (i === cur) + '">' + esc(t.label) + '</button>').join('') + '</div>'
        + after.map((t, i) => '<div data-panel="' + i + '"' + (i === cur ? '' : ' hidden') + '>' + t.html + '</div>').join('');
      box.querySelectorAll('[data-tab]').forEach(b => b.addEventListener('click', () => {
        tab = Number(b.dataset.tab);
        box.querySelectorAll('[data-tab]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
        box.querySelectorAll('[data-panel]').forEach(x => { x.hidden = x.dataset.panel !== b.dataset.tab; });
      }));
    } else box.innerHTML = after;
    box.hidden = !after.length;
    const nb = q('next');
    nb.hidden = false;
    setTimeout(() => { try { nb.focus({ preventScroll: true }); } catch (e) { /* ignore */ } }, 0);
  }

  function choose(btn, good) {
    if (answered) return;
    answered = true;
    root.querySelectorAll('.opt').forEach(b => {
      b.disabled = true;
      if (b.dataset.ok === '1') b.classList.add('right');
    });
    if (!good) btn.classList.add('wrong');
    grade(good); result(good);
  }

  q('form').addEventListener('submit', e => {
    e.preventDefault();
    if (answered) return;
    const val = norm(q('answer').value);
    if (!val) return;
    answered = true;
    const good = [view.answer.lat, view.answer.ar, ...(view.accept || [])].some(c => norm(c) === val);
    q('answer').disabled = true; q('check').hidden = true;
    grade(good); result(good);
  });
  q('next').addEventListener('click', () => {
    next();
    if (prefs.mode === 'type') { try { q('answer').focus({ preventScroll: true }); } catch (e) { /* ignore */ } }
  });

  const settingsBox = root.querySelector('.settings');
  bindSeg(settingsBox, prefs, k => {
    prefs.save();
    document.body.dataset.script = prefs.script;
    if (k === 'script' && item) {
      if (!answered) return next(item);
      draw();
      root.querySelectorAll('.opt').forEach(b => { b.innerHTML = disp(b.dataset.lat, b.dataset.ar); });
      result(ok);
    } else next();
    if (onSettings) onSettings(k);
  });
  document.body.dataset.script = prefs.script;

  let armed = null;
  q('reset').addEventListener('click', () => {
    const b = q('reset');
    if (!armed) {
      b.textContent = 'Tap again to erase this drill’s history';
      armed = setTimeout(() => { armed = null; b.textContent = 'Reset progress for this drill'; }, 4000);
      return;
    }
    clearTimeout(armed); armed = null;
    b.textContent = 'Reset progress for this drill';
    saved.weights = {}; saved.traits = {}; saved.best = 0; sess.right = sess.total = sess.streak = 0;
    saved.save(); next();
  });

  return { next, weight };
}

// Table of forms shown after an answer.
export function formTable(title, labels, lat, ar, asked) {
  let h = '<div class="table"><h2>' + esc(title) + '</h2>';
  labels.forEach((p, i) => {
    h += '<div class="row' + (i === asked ? ' asked' : '') + '"><span class="p">' + esc(p) + '</span><span class="f">' + disp(lat[i], ar[i]) + '</span></div>';
  });
  return h + '</div>';
}
