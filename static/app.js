// ShockBook Frontend Controller: Shader, Interactive SVG Fan/Sankey/Waterfall/Lens, and Live API/MCP Calls

const canvas = document.getElementById('stressShaderCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;
let shockIntensity = 15;
let activeScenarioId = 'btc_crash_15';
let phase = 0;
let canvasVisible = true;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

function drawStressField() {
  if (!ctx || !canvas) return;
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  const baseStroke = isLight ? 'rgba(0, 56, 255, ' : 'rgba(77, 115, 255, ';
  const breachStroke = isLight ? 'rgba(217, 30, 54, ' : 'rgba(255, 42, 75, ';

  const lines = 11;
  const amp = 8 + (shockIntensity * 1.15);
  const freq = 0.0045 + (shockIntensity * 0.00012);

  for (let i = 0; i < lines; i++) {
    ctx.beginPath();
    const yBase = 24 + i * ((h - 40) / (lines - 1));
    const isTail = i < 3 && shockIntensity >= 13;
    const alpha = isTail ? 0.28 : (0.09 + (i / lines) * 0.14);
    ctx.strokeStyle = (isTail ? breachStroke : baseStroke) + alpha.toFixed(2) + ')';
    ctx.lineWidth = isTail ? 1.5 : 1;

    for (let x = 0; x <= w; x += 18) {
      const wave1 = Math.sin(x * freq + phase + i * 0.42) * amp;
      const wave2 = Math.cos(x * (freq * 1.9) - phase * 0.6 + i * 0.7) * (amp * 0.38);
      const y = yBase + wave1 + wave2;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
}

function tickShader() {
  if (!reducedMotion.matches && canvasVisible) {
    phase += 0.018 + (shockIntensity * 0.0006);
    drawStressField();
  }
  requestAnimationFrame(tickShader);
}

if (canvas) {
  drawStressField();
  if (!reducedMotion.matches) {
    requestAnimationFrame(tickShader);
  }
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => { canvasVisible = e.isIntersecting; });
  });
  io.observe(canvas);
}

// Theme Polarity Switcher (Carbon Void <-> Alabaster Paper)
function applyStoredTheme() {
  const saved = localStorage.getItem('shockbook_theme');
  const btn = document.getElementById('themeToggleBtn');
  if (saved === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    if (btn) btn.textContent = 'THEME: ALABASTER PAPER';
  } else {
    document.documentElement.removeAttribute('data-theme');
    if (btn) btn.textContent = 'THEME: CARBON VOID';
  }
  drawStressField();
}

function flipTheme() {
  const html = document.documentElement;
  if (html.getAttribute('data-theme') === 'light') {
    localStorage.setItem('shockbook_theme', 'dark');
  } else {
    localStorage.setItem('shockbook_theme', 'light');
  }
  applyStoredTheme();
}
applyStoredTheme();

// DecryptScramble Helper (Trickle UI Kit)
const HEX_CHARS = '0123456789ABCDEF#%';
function scrambleText(el, finalStr, durationMs = 240) {
  if (!el) return;
  if (reducedMotion.matches) {
    el.textContent = finalStr;
    return;
  }
  const start = performance.now();
  function step(now) {
    const p = Math.min(1, (now - start) / durationMs);
    const revealCount = Math.floor(p * finalStr.length);
    let out = '';
    for (let i = 0; i < finalStr.length; i++) {
      if (i < revealCount || finalStr[i] === ' ' || finalStr[i] === '$' || finalStr[i] === '-' || finalStr[i] === '+') {
        out += finalStr[i];
      } else {
        out += HEX_CHARS[Math.floor(Math.random() * HEX_CHARS.length)];
      }
    }
    el.textContent = out;
    if (p < 1) requestAnimationFrame(step);
    else el.textContent = finalStr;
  }
  requestAnimationFrame(step);
}

// Interactive Shock Scrubber
function applyPreset(val, scenarioId, label, btn) {
  activeScenarioId = scenarioId;
  const slider = document.getElementById('shockRange');
  if (slider) slider.value = val;
  document.querySelectorAll('.stress-stage .preset-btn').forEach(b => b.setAttribute('aria-pressed', 'false'));
  if (btn) btn.setAttribute('aria-pressed', 'true');
  scrubShock(val, label);
}

function scrubShock(rawVal, customLabel) {
  const shockPct = parseInt(rawVal, 10);
  shockIntensity = Math.abs(shockPct);
  const ratio = shockIntensity / 15.0;

  const bookInput = document.getElementById('inputPortfolioUsd');
  const capInput = document.getElementById('inputMaxDrawdownUsd');
  const portfolioUsd = bookInput ? parseFloat(bookInput.value || '20000') : 20000;
  const maxCapUsd = capInput ? parseFloat(capInput.value || '2000') : 2000;
  const scaleBook = portfolioUsd / 20000.0;

  const unhedgedLoss = Math.round(3420 * ratio * scaleBook);
  const hedgedLoss = Math.round(1690 * ratio * scaleBook);
  const saved = unhedgedLoss - hedgedLoss;

  const uPct = ((unhedgedLoss / portfolioUsd) * 100).toFixed(1);
  const hPct = ((hedgedLoss / portfolioUsd) * 100).toFixed(1);
  const sPct = ((saved / portfolioUsd) * 100).toFixed(1);

  const readout = document.getElementById('shockReadout');
  if (readout) {
    readout.textContent = customLabel ? `${shockPct}.0% · ${customLabel.toUpperCase()}` : `${shockPct}.0% BTC CRASH`;
  }
  const heroShock = document.getElementById('heroShockText');
  if (heroShock) heroShock.textContent = `${shockPct}%`;

  const breachTag = document.getElementById('mBreachTag');
  const heroVerdict = document.getElementById('heroVerdictText');
  if (breachTag && heroVerdict) {
    if (unhedgedLoss > maxCapUsd) {
      const over = Math.round(unhedgedLoss - maxCapUsd);
      breachTag.textContent = `BREACH +$${over.toLocaleString()}`;
      breachTag.className = 'status-tag tag-breach';
      heroVerdict.textContent = `BREACHES $${maxCapUsd.toLocaleString()} CAP`;
      heroVerdict.style.color = 'var(--crimson)';
    } else {
      breachTag.textContent = `WITHIN $${maxCapUsd.toLocaleString()} CAP`;
      breachTag.className = 'status-tag tag-pass';
      heroVerdict.textContent = `HOLDS $${maxCapUsd.toLocaleString()} CAP`;
      heroVerdict.style.color = 'var(--emerald)';
    }
  }

  const passTag = document.getElementById('mPassTag');
  if (passTag) {
    if (hedgedLoss <= maxCapUsd) {
      passTag.textContent = `WITHIN $${maxCapUsd.toLocaleString()} CAP`;
      passTag.className = 'status-tag tag-pass';
    } else {
      passTag.textContent = `RESIDUAL +$${Math.round(hedgedLoss - maxCapUsd).toLocaleString()}`;
      passTag.className = 'status-tag tag-warn';
    }
  }

  scrambleText(document.getElementById('mUnhedged'), `-$${unhedgedLoss.toLocaleString()}`, 180);
  scrambleText(document.getElementById('mHedged'), `-$${hedgedLoss.toLocaleString()}`, 180);
  scrambleText(document.getElementById('mSaved'), `+$${saved.toLocaleString()}`, 180);

  const uPctEl = document.getElementById('mUnhedgedPct');
  if (uPctEl) uPctEl.textContent = `-${uPct}% of $${portfolioUsd.toLocaleString()} Book`;
  const hPctEl = document.getElementById('mHedgedPct');
  if (hPctEl) hPctEl.textContent = `-${hPct}% of $${portfolioUsd.toLocaleString()} Book`;
  const sPctEl = document.getElementById('mSavedPct');
  if (sPctEl) sPctEl.textContent = `+${sPct}% Tail Cushion Added`;

  const solU = document.getElementById('solUnhedged');
  if (solU) {
    solU.textContent = `-$${Math.round(1865 * ratio * scaleBook).toLocaleString()}`;
    document.getElementById('solHedged').textContent = `-$${Math.round(977 * ratio * scaleBook).toLocaleString()}`;
    document.getElementById('avaxUnhedged').textContent = `-$${Math.round(1310 * ratio * scaleBook).toLocaleString()}`;
    document.getElementById('avaxHedged').textContent = `-$${Math.round(655 * ratio * scaleBook).toLocaleString()}`;
    document.getElementById('btcUnhedged').textContent = `-$${Math.round(245 * ratio * scaleBook).toLocaleString()}`;
    document.getElementById('btcHedged').textContent = `-$${Math.round(58 * ratio * scaleBook).toLocaleString()}`;
  }

  // Update SVG Fan Cone End Coordinates dynamically
  const unhedgedMeanLine = document.getElementById('unhedgedMeanLine');
  if (unhedgedMeanLine) {
    const endUnhedgedY = Math.min(242, Math.round(96 + (unhedgedLoss / maxCapUsd) * 62));
    const endHedgedY = Math.min(215, Math.round(96 + (hedgedLoss / maxCapUsd) * 62));

    unhedgedMeanLine.setAttribute('points', `540,96 630,${Math.round((96 + endUnhedgedY) / 2)} 720,${Math.round(endUnhedgedY - 12)} 825,${endUnhedgedY}`);
    document.getElementById('unhedgedEndDot').setAttribute('cy', endUnhedgedY);
    document.getElementById('unhedgedEndLabel').setAttribute('y', Math.max(185, endUnhedgedY - 8));
    document.getElementById('unhedgedEndLabel').textContent = `UNHEDGED $${Math.round(portfolioUsd - unhedgedLoss).toLocaleString()} (-$${unhedgedLoss.toLocaleString()})`;

    document.getElementById('hedgedMeanLine').setAttribute('points', `540,96 630,${Math.round((96 + endHedgedY) / 2)} 720,${Math.round(endHedgedY - 6)} 825,${endHedgedY}`);
    document.getElementById('hedgedEndDot').setAttribute('cy', endHedgedY);
    document.getElementById('hedgedEndLabel').setAttribute('y', Math.max(122, endHedgedY - 10));
    document.getElementById('hedgedEndLabel').textContent = `MANDATE $${Math.round(portfolioUsd - hedgedLoss).toLocaleString()} (-$${hedgedLoss.toLocaleString()})`;
  }

  const trailMeta = document.getElementById('trailShockMeta');
  if (trailMeta) {
    trailMeta.textContent = `SCENARIO: BTC ${shockPct}.0%`;
    document.getElementById('trailShockBody').textContent =
      `Under a ${shockPct}.0% BTC shock vector, tail beta compression drives an unhedged portfolio drawdown of -$${unhedgedLoss.toLocaleString()}.00 (-${uPct}%). Executing the rebalance mandate preserves +$${saved.toLocaleString()}.00.`;
  }

  drawStressField();
}

let activePositions = [
  { symbol: 'SOL', weight: 0.42 },
  { symbol: 'AVAX', weight: 0.28 },
  { symbol: 'BTC', weight: 0.20 },
  { symbol: 'USDC', weight: 0.10 }
];

function selectBasket(basketKey, btn) {
  if (btn && btn.parentElement) {
    btn.parentElement.querySelectorAll('.preset-btn').forEach(b => b.setAttribute('aria-pressed', 'false'));
    btn.setAttribute('aria-pressed', 'true');
  }
  if (basketKey === 'inj_sui') {
    activePositions = [
      { symbol: 'INJ', weight: 0.45 },
      { symbol: 'SUI', weight: 0.30 },
      { symbol: 'ETH', weight: 0.15 },
      { symbol: 'USDC', weight: 0.10 }
    ];
  } else {
    activePositions = [
      { symbol: 'SOL', weight: 0.42 },
      { symbol: 'AVAX', weight: 0.28 },
      { symbol: 'BTC', weight: 0.20 },
      { symbol: 'USDC', weight: 0.10 }
    ];
  }
  runLiveServerStress();
}

// Run Live Server Stress + DeepSeek Audit
async function runLiveServerStress() {
  const btn = document.getElementById('runLiveAuditBtn');
  if (btn) btn.textContent = 'RUNNING RYO + DEEPSEEK...';
  const portfolioUsd = parseFloat(document.getElementById('inputPortfolioUsd')?.value || '20000');
  const maxDrawdownUsd = parseFloat(document.getElementById('inputMaxDrawdownUsd')?.value || '2000');
  const correlationCap = parseFloat(document.getElementById('inputCorrCap')?.value || '0.75');
  const shockPct = parseFloat(document.getElementById('shockRange')?.value || '-15');

  try {
    const resp = await fetch('/api/stress/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portfolio_usd: portfolioUsd,
        positions: activePositions,
        shock_btc_pct: shockPct,
        scenario_id: activeScenarioId,
        max_drawdown_usd: maxDrawdownUsd,
        correlation_cap: correlationCap,
        use_live_llm: true
      })
    });
    const payload = await resp.json();
    if (payload && payload.stress) {
      const s = payload.stress;
      scrambleText(document.getElementById('mUnhedged'), `-$${Math.round(Math.abs(s.unhedged_drawdown_usd)).toLocaleString()}`, 220);
      scrambleText(document.getElementById('mHedged'), `-$${Math.round(Math.abs(s.rebalanced_drawdown_usd)).toLocaleString()}`, 220);
      scrambleText(document.getElementById('mSaved'), `+$${Math.round(s.capital_preserved_usd).toLocaleString()}`, 220);
      const corrEl = document.getElementById('heroCorrText');
      if (corrEl) corrEl.textContent = s.max_pair_correlation_168h.toFixed(2);

      // Update book table rows dynamically
      const tbody = document.getElementById('bookTableBody');
      if (tbody && Array.isArray(s.asset_rows)) {
        tbody.innerHTML = s.asset_rows.map(row => {
          const curPct = Math.round(row.initial_weight * 100);
          const mndPct = Math.round(row.mandate_weight * 100);
          const tagClass = row.action === 'TRIM' ? 'tag-breach' : row.action === 'SHIELD' ? 'tag-pass' : 'tag-cobalt';
          const uStr = row.unhedged_loss_usd === 0 ? '$0' : `-$${Math.round(Math.abs(row.unhedged_loss_usd)).toLocaleString()}`;
          const mStr = row.mandate_loss_usd === 0 ? '$0' : `-$${Math.round(Math.abs(row.mandate_loss_usd)).toLocaleString()}`;
          const uColor = row.action === 'TRIM' ? 'color:var(--crimson);' : '';
          const mColor = row.action === 'SHIELD' ? 'color:var(--emerald);' : '';
          return `
            <tr>
              <td><span class="token-badge">${row.symbol}</span> <span class="status-tag ${tagClass}">${row.action}</span></td>
              <td class="mono-num">${row.atr_14d_pct.toFixed(1)}%</td>
              <td class="mono-num">${row.beta_vs_btc.toFixed(2)}x</td>
              <td>
                <div class="weight-bar-wrap">
                  <span class="mono-num" style="width:82px;">${curPct}% → <strong>${mndPct}%</strong></span>
                  <div class="mini-track"><div class="mini-fill-cur" style="width:${curPct}%"></div></div>
                  <div class="mini-track"><div class="mini-fill-tgt" style="width:${mndPct}%"></div></div>
                </div>
              </td>
              <td class="mono-num" style="${uColor}">${uStr}</td>
              <td class="mono-num" style="${mColor}">${mStr}</td>
            </tr>
          `;
        }).join('');
      }

      if (payload.officer && payload.officer.steps && payload.officer.steps.length >= 3) {
        const bodyEls = document.querySelectorAll('#pane-desk .officer-text');
        payload.officer.steps.forEach((step, idx) => {
          if (bodyEls[idx]) bodyEls[idx].textContent = step.body;
        });
      }
      const sealEl = document.getElementById('liveEvidenceHash');
      if (sealEl && payload.evidence_sha256) {
        scrambleText(sealEl, `0x${payload.evidence_sha256.slice(0, 16)}`, 260);
      }
    }
  } catch (err) {
    console.error(err);
  } finally {
    if (btn) btn.textContent = 'RECOMPUTE LIVE AUDIT';
  }
}

// Interactive Correlation Matrix Scatter Lens
function inspectPair(a, b, rho, beta, statusText, btn) {
  document.querySelectorAll('.m-cell').forEach(c => c.classList.remove('active-lens'));
  if (btn) btn.classList.add('active-lens');
  const titleEl = document.getElementById('lensPairTitle');
  if (titleEl) titleEl.textContent = `${a} × ${b} (168H)`;
  const rhoEl = document.getElementById('lensRhoMetric');
  if (rhoEl) rhoEl.textContent = `PEARSON ρ: ${rho.toFixed(2)}`;
  const betaEl = document.getElementById('lensBetaMetric');
  if (betaEl) betaEl.textContent = `JOINT BETA: ${beta.toFixed(2)}x`;
  const badge = document.getElementById('lensStatusBadge');
  if (badge) {
    badge.textContent = statusText;
    badge.className = 'status-tag ' + (rho > 0.75 ? 'tag-breach' : rho >= 0.71 ? 'tag-warn' : 'tag-pass');
  }

  const slopeY1 = Math.round(65 + 48 * rho);
  const slopeY2 = Math.round(65 - 48 * rho);
  const regLine = document.getElementById('lensRegLine');
  if (regLine) {
    regLine.setAttribute('y1', slopeY1);
    regLine.setAttribute('y2', slopeY2);
    regLine.setAttribute('stroke', rho > 0.75 ? 'var(--crimson)' : 'var(--cobalt-bright)');
  }
}

// Commit Signed Practice Mandate to SQLite WAL Ledger
async function sealAndCommitMandate() {
  const btn = document.getElementById('commitMandateBtn');
  if (btn) btn.textContent = 'SEALING MANDATE TO SQLITE WAL...';

  const portfolioUsd = parseFloat(document.getElementById('inputPortfolioUsd')?.value || '20000');
  const maxDrawdownUsd = parseFloat(document.getElementById('inputMaxDrawdownUsd')?.value || '2000');
  const correlationCap = parseFloat(document.getElementById('inputCorrCap')?.value || '0.75');
  const shockPct = parseFloat(document.getElementById('shockRange')?.value || '-15');
  const scenarioLabel = document.getElementById('shockReadout')?.textContent || `BTC ${shockPct}% Shock`;

  try {
    const resp = await fetch('/api/mandates/commit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        portfolio_usd: portfolioUsd,
        positions: activePositions,
        shock_btc_pct: shockPct,
        scenario_label: scenarioLabel,
        max_drawdown_usd: maxDrawdownUsd,
        correlation_cap: correlationCap
      })
    });
    const res = await resp.json();
    if (res && res.mandate_id) {
      window.location.href = '/ledger?committed=' + encodeURIComponent(res.mandate_id);
      return;
    }
  } catch (e) {
    console.error(e);
  }
  if (btn) btn.textContent = 'SEAL & COMMIT MANDATE';
}

// Deterministic SHA-256 Replay Check on /ledger
async function verifySingleMandate(mandateId, btnEl) {
  try {
    const resp = await fetch(`/api/mandates/${encodeURIComponent(mandateId)}/verify`);
    const data = await resp.json();
    if (data && data.verified) {
      scrambleText(btnEl, `${data.short_hash} REPLAY MATCH`, 320);
      btnEl.className = 'status-tag tag-pass';
    }
  } catch (e) {
    console.error(e);
  }
}

function runDeterministicReplayAll() {
  document.querySelectorAll('[data-mandate-id]').forEach(el => {
    const id = el.getAttribute('data-mandate-id');
    verifySingleMandate(id, el);
  });
}

// Track 3 MCP Skill Workbench & Fault-Injection Drill on /skills
async function executeLiveMcpDrill(toolName, faultMode, btn) {
  if (btn && btn.parentElement) {
    btn.parentElement.querySelectorAll('.preset-btn').forEach(b => b.setAttribute('aria-pressed', 'false'));
    btn.setAttribute('aria-pressed', 'true');
  }

  const badge = document.getElementById('drillEnvelopeBadge');
  const pre = document.getElementById('drillEnvelopeJson');
  const hdrBadge = document.getElementById('mcpHeaderBadge');

  try {
    const resp = await fetch(`/api/mcp/tools/${encodeURIComponent(toolName)}/call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        arguments: {
          portfolio_usd: 20000,
          shock_btc_pct: -15.0,
          max_drawdown_usd: 2000.0,
          correlation_cap: 0.75,
          fault_mode: faultMode
        }
      })
    });
    const env = await resp.json();
    if (pre) {
      pre.textContent = JSON.stringify(env, null, 2);
    }
    if (badge) {
      badge.textContent = `status: "${env.status}" · data_mode: "${env.data_mode}"`;
      badge.className = 'status-tag ' + (env.status === 'ok' ? 'tag-pass' : 'tag-warn');
    }
    if (hdrBadge) {
      if (faultMode === 'ryo_429') {
        hdrBadge.innerHTML = '<span class="pulse-dot" style="background:var(--gold);"></span><span>RYO MCP: <strong>429 QUOTA GUARD</strong> · OKX 1H LIVE</span>';
      } else if (faultMode === 'null_perp') {
        hdrBadge.innerHTML = '<span class="pulse-dot" style="background:var(--gold);"></span><span>RYO MCP: <strong>PERP=NULL GUARD</strong> · OKX 1H LIVE</span>';
      } else {
        hdrBadge.innerHTML = '<span class="pulse-dot"></span><span>RYO MCP: <strong>9aa2de95</strong> · OKX 1H LIVE</span>';
      }
    }
  } catch (e) {
    console.error(e);
  }
}
