#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub Actions から自動実行 — pa.html と se.html を生成"""

import time
from pathlib import Path

import requests

API_BASE = "https://sports-api.smt.docomo.ne.jp/data/baseball/npb/rankings"
HEADERS = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'),
    'Referer': 'https://service.smt.docomo.ne.jp/portal/sports/baseball_j/ranking_detail.html',
    'Origin': 'https://service.smt.docomo.ne.jp',
}

BATTER_STATS = [
    ('avg', '打率', 'ranking_b_batting_average', 'batting_average'),
    ('hr', '本塁打', 'ranking_b_homerun', 'homerun'),
    ('rbi', '打点', 'ranking_b_runs_batting_in', 'runs_batting_in'),
    ('sb', '盗塁', 'ranking_b_stolen_base', 'stolen_base'),
    ('risp', '得点圏打率', 'ranking_b_tbawris', 'tbawris'),
    ('so', '三振', 'ranking_b_strikeout', 'strikeout'),
]
PITCHER_STATS = [
    ('era', '防御率', 'ranking_p_earned_run_ave', 'earned_run_average'),
    ('w', '勝利', 'ranking_p_win', 'win'),
    ('pct', '勝率', 'ranking_p_wa', 'wa'),
    ('so', '奪三振', 'ranking_p_strikeout', 'strikeout'),
    ('sv', 'セーブ', 'ranking_p_save', 'save'),
]

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NPBランキング コピペ用 __LEAGUE_NAME__</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: 'Inter', 'Hiragino Sans', 'Yu Gothic', sans-serif;
    background: #f7f8fa;
    color: #0a0a0a;
    margin: 0;
    padding: 20px;
    font-size: 14px;
    line-height: 1.5;
  }
  .header {
    max-width: 1200px;
    margin: 0 auto 24px;
    background: #fff;
    padding: 24px 28px;
    border-radius: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }
  .header h1 { margin: 0; font-size: 22px; font-weight: 700; }
  .updated { font-size: 12px; color: #6b7280; letter-spacing: 0.03em; }
  .updated strong { color: #0a0a0a; font-weight: 700; }
  .section-title {
    max-width: 1200px;
    margin: 0 auto 12px;
    padding: 0 28px;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-weight: 700;
    color: #6b7280;
  }
  .grid {
    max-width: 1200px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 20px;
    padding: 0 0 32px;
  }
  .card { background: #fff; border-radius: 20px; padding: 22px 24px; }
  .card-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
  }
  .card-title { font-size: 18px; font-weight: 700; }
  .card-update { font-size: 10px; color: #9ca3af; letter-spacing: 0.03em; }
  .copy-btn {
    background: #1DB954;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    font-family: inherit;
    letter-spacing: 0.04em;
    transition: filter 150ms ease;
  }
  .copy-btn:hover { filter: brightness(1.1); }
  .copy-btn:active { transform: scale(0.97); }
  .copy-btn.done { background: #0a0a0a; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed; }
  th {
    text-align: left;
    font-size: 10px;
    letter-spacing: 0.08em;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    padding: 6px 0;
  }
  td { padding: 7px 0; border-bottom: 1px solid #f0f1f4; }
  tr:last-child td { border-bottom: none; }
  td.rank { width: 32px; font-weight: 700; color: #6b7280; }
  td.player { font-weight: 600; }
  td.team { width: 38px; font-size: 11px; font-weight: 700; color: #6b7280; }
  td.value { width: 60px; text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; }
  .empty { text-align: center; color: #9ca3af; padding: 24px; font-size: 13px; }
  .footer { max-width: 1200px; margin: 0 auto; padding: 16px 28px; font-size: 12px; color: #6b7280; }
  .copy-hint {
    background: #fff7e6;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 0 auto 24px;
    max-width: 1200px;
    font-size: 13px;
    color: #92400e;
    line-height: 1.6;
  }
  .copy-hint strong { color: #78350f; }
  .standings-card {
    max-width: 1200px;
    margin: 0 auto 24px;
    background: #fff;
    border-radius: 20px;
    padding: 22px 28px;
  }
  .standings-card .card-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 14px;
  }
  .standings-card .card-title { font-size: 18px; font-weight: 700; }
  .standings-card .card-update { font-size: 10px; color: #9ca3af; letter-spacing: 0.03em; }
  .standings-card table { width: 100%; border-collapse: collapse; font-size: 13px; table-layout: auto; }
  .standings-card th, .standings-card td { padding: 8px 6px; border-bottom: 1px solid #f0f1f4; }
  .standings-card tr:last-child td { border-bottom: none; }
  .standings-card th {
    text-align: center;
    font-size: 10px;
    letter-spacing: 0.06em;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 700;
  }
  .standings-card th:nth-child(2) { text-align: left; }
  .standings-card td.rank { width: 40px; text-align: center; font-weight: 700; color: #6b7280; }
  .standings-card td.team { font-weight: 700; }
  .standings-card td.num { text-align: center; font-variant-numeric: tabular-nums; }
  .standings-card td.pct { text-align: center; font-weight: 700; font-variant-numeric: tabular-nums; }
  .standings-card td.gb { text-align: center; color: #6b7280; font-variant-numeric: tabular-nums; }
  .back-link {
    max-width: 1200px;
    margin: 0 auto 20px;
    display: block;
    font-size: 13px;
    color: #6b7280;
    text-decoration: none;
  }
  .back-link:hover { color: #0a0a0a; }
  .header-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
  .header-btn-row { display: flex; gap: 8px; align-items: center; }
  .update-btn {
    background: #0a0a0a;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 9px 16px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    font-family: inherit;
    letter-spacing: 0.04em;
    transition: filter 150ms ease;
  }
  .update-btn:hover { filter: brightness(1.3); }
  .update-btn:active { transform: scale(0.97); }
  .update-btn:disabled { opacity: 0.5; cursor: default; transform: none; }
  .settings-btn {
    background: none;
    border: 1.5px solid #e5e7eb;
    border-radius: 10px;
    padding: 7px 10px;
    font-size: 13px;
    cursor: pointer;
    color: #6b7280;
    transition: border-color 150ms;
    font-family: inherit;
  }
  .settings-btn:hover { border-color: #0a0a0a; color: #0a0a0a; }
  #update-status { font-size: 11px; color: #6b7280; min-height: 16px; }
  .modal-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.45);
    z-index: 1000;
    align-items: center;
    justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: #fff;
    border-radius: 20px;
    padding: 28px;
    max-width: 440px;
    width: calc(100% - 40px);
  }
  .modal h2 { margin: 0 0 12px; font-size: 17px; font-weight: 700; }
  .modal p { font-size: 13px; color: #6b7280; line-height: 1.6; margin: 0 0 4px; }
  .modal ol { font-size: 13px; color: #6b7280; line-height: 1.9; margin: 8px 0 16px; padding-left: 20px; }
  .modal ol a { color: #3d5afe; }
  .token-input {
    width: 100%;
    padding: 12px 14px;
    border-radius: 10px;
    border: 1.5px solid #e5e7eb;
    font-size: 14px;
    box-sizing: border-box;
    margin-bottom: 14px;
    font-family: monospace;
    outline: none;
  }
  .token-input:focus { border-color: #0a0a0a; }
  .modal-actions { display: flex; gap: 8px; justify-content: flex-end; }
  .btn-cancel {
    padding: 10px 18px; border-radius: 10px; border: none;
    background: #f3f4f6; font-size: 14px; cursor: pointer; font-weight: 600; font-family: inherit;
  }
  .btn-save {
    padding: 10px 18px; border-radius: 10px; border: none;
    background: #0a0a0a; color: #fff; font-size: 14px; cursor: pointer; font-weight: 600; font-family: inherit;
  }
</style>
</head>
<body>
  <!-- Token modal -->
  <div id="token-modal" class="modal-overlay" onclick="overlayClick(event)">
    <div class="modal">
      <h2>GitHubトークン設定</h2>
      <p>更新ボタンを使うには<strong>GitHub Personal Access Token</strong>が必要です。一度設定すればこのデバイスでは保存されます。</p>
      <ol>
        <li><a href="https://github.com/settings/personal-access-tokens/new" target="_blank">GitHub → Fine-grained tokens</a> を開く</li>
        <li>Repository access: <strong>npb-ranking</strong> のみ選択</li>
        <li>Permissions → Repository permissions → <strong>Actions: Read and write</strong></li>
        <li>Generate token → コピーして下に貼り付け</li>
      </ol>
      <input id="token-input" class="token-input" type="password" placeholder="github_pat_..." autocomplete="off">
      <div class="modal-actions">
        <button class="btn-cancel" onclick="closeSettings()">キャンセル</button>
        <button class="btn-save" onclick="saveToken()">保存</button>
      </div>
    </div>
  </div>

  <a class="back-link" href="index.html">← リーグ選択に戻る</a>
  <div class="header">
    <h1>NPBランキング <span style="font-size:14px;color:#6b7280;font-weight:500;margin-left:8px">__LEAGUE_NAME__</span></h1>
    <div class="header-right">
      <div class="header-btn-row">
        <button id="update-btn" class="update-btn" onclick="triggerUpdate()">↻ 今すぐ更新</button>
        <button class="settings-btn" onclick="openSettings()" title="トークン設定">⚙</button>
      </div>
      <div class="updated">最新更新: <strong>__LATEST_UPDATE__</strong></div>
      <div id="update-status"></div>
    </div>
  </div>

  <div class="copy-hint">
    <strong>使い方:</strong> 各カードの「コピー」ボタンを押すと、順位／選手名／球団／値の4列がタブ区切りでクリップボードにコピーされます。
    Excelの貼り付けたいセル（例: A5）を選択して <strong>⌘+V</strong>（AndroidはCtrl+V）で4列が一気に埋まります。
  </div>

  __STANDINGS__

  <div class="section-title">打者ランキング</div>
  <div class="grid">__BATTER_CARDS__</div>

  <div class="section-title">投手ランキング</div>
  <div class="grid">__PITCHER_CARDS__</div>

  <div class="footer">
    Source: docomoスポーツ（dメニュースポーツ） / 自動更新: 毎日3回（8時・14時・20時 JST）
  </div>

<script>
function copyTSV(btn) {
  const tsv = btn.dataset.tsv;
  navigator.clipboard.writeText(tsv).then(() => {
    const original = btn.textContent;
    btn.textContent = '✓ コピー完了';
    btn.classList.add('done');
    setTimeout(() => { btn.textContent = original; btn.classList.remove('done'); }, 1500);
  }).catch(err => { alert('コピー失敗: ' + err.message); });
}

const REPO = 'uyf2Hfbu2/npb-ranking';
const WORKFLOW = 'update.yml';
const TOKEN_KEY = 'npb_gh_token';

function getToken() { return localStorage.getItem(TOKEN_KEY) || ''; }
function openSettings() {
  document.getElementById('token-input').value = getToken();
  document.getElementById('token-modal').classList.add('open');
}
function closeSettings() { document.getElementById('token-modal').classList.remove('open'); }
function overlayClick(e) { if (e.target.id === 'token-modal') closeSettings(); }
function saveToken() {
  const t = document.getElementById('token-input').value.trim();
  if (t) { localStorage.setItem(TOKEN_KEY, t); closeSettings(); setStatus('トークンを保存しました', '#1DB954'); }
}

async function triggerUpdate() {
  const token = getToken();
  if (!token) { openSettings(); return; }
  const btn = document.getElementById('update-btn');
  btn.disabled = true;
  btn.textContent = '更新中...';
  setStatus('GitHub Actions を起動しています...', '#6b7280');
  try {
    const res = await fetch(
      `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ref: 'main' }),
      }
    );
    if (res.status === 204) {
      setStatus('✅ 更新開始。2〜3分後に再読み込みしてください', '#1DB954');
      setTimeout(() => { btn.disabled = false; btn.textContent = '↻ 今すぐ更新'; }, 10000);
    } else if (res.status === 401) {
      setStatus('❌ トークンが無効です。⚙ から再設定してください', '#ef4444');
      btn.disabled = false; btn.textContent = '↻ 今すぐ更新';
    } else {
      const body = await res.json().catch(() => ({}));
      setStatus(`❌ エラー ${res.status}: ${body.message || ''}`, '#ef4444');
      btn.disabled = false; btn.textContent = '↻ 今すぐ更新';
    }
  } catch (e) {
    setStatus('❌ ネットワークエラー: ' + e.message, '#ef4444');
    btn.disabled = false; btn.textContent = '↻ 今すぐ更新';
  }
}

function setStatus(msg, color) {
  const el = document.getElementById('update-status');
  el.textContent = msg;
  el.style.color = color || '#6b7280';
}
</script>
</body>
</html>
"""


def fetch_json(url):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == 2:
                print(f"  [エラー] {url}: {e}")
                return {}
            time.sleep(1.5)
    return {}


TEAM_NAME_MAP = {
    'DeNA': 'De',
}


def norm_team(name):
    return TEAM_NAME_MAP.get(name, name)


def match_id(league):
    return '1' if league.upper() == 'C' else '2'


def fetch_standings(league):
    name = 'central' if league.upper() == 'C' else 'pacific'
    data = fetch_json(f"{API_BASE}/{name}_order.json")
    if not data or 'rank' not in data:
        return {'update_date': '', 'rows': []}
    rows = [{
        'rank': r.get('ranking', ''),
        'team': norm_team(r.get('short_name-team', '')),
        'game': r.get('game', ''),
        'win': r.get('win', ''),
        'lose': r.get('lose', ''),
        'draw': r.get('draw', ''),
        'pct': r.get('winning_percentage', ''),
        'gb': r.get('game_behind_top', ''),
    } for r in data['rank']]
    return {'update_date': data.get('update_date', ''), 'rows': rows}


def fetch_ranking(file_prefix, value_key, league, top_rank=5):
    data = fetch_json(f"{API_BASE}/{file_prefix}_{match_id(league)}.json")
    if not data or 'rank' not in data:
        return {'update_date': '', 'rows': []}
    rows = []
    for r in data['rank']:
        rank = int(r.get('ranking', 0))
        if rank == 0 or rank > top_rank:
            continue
        rows.append((rank, r.get('name', '').strip(), norm_team(r.get('team_initial', '').strip()), r.get(value_key, '')))
    return {'update_date': data.get('update_date', ''), 'rows': rows}


def format_value(v, key):
    if v is None or v == '':
        return ''
    s = str(v)
    if key in ('batting_average', 'wa', 'tbawris') and s.startswith('0.'):
        return s[1:]
    return s


def card_html(title, update_date, rows, key):
    tsv_lines = [f"{rank}\t{player}\t{team}\t{format_value(value, key)}" for rank, player, team, value in rows]
    tsv = '\n'.join(tsv_lines)
    tsv_attr = tsv.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    rows_html = ''
    if rows:
        for rank, player, team, value in rows:
            v = format_value(value, key)
            rows_html += f'<tr><td class="rank">{rank}</td><td class="player">{player}</td><td class="team">{team}</td><td class="value">{v}</td></tr>'
    else:
        rows_html = '<tr><td colspan="4" class="empty">データなし</td></tr>'
    update_display = update_date[:16] if update_date else ''
    return f'''
    <div class="card">
      <div class="card-head">
        <div><div class="card-title">{title}</div><div class="card-update">{update_display}</div></div>
        <button class="copy-btn" data-tsv="{tsv_attr}" onclick="copyTSV(this)">コピー</button>
      </div>
      <table>
        <thead><tr><th>順位</th><th>選手</th><th>球団</th><th style="text-align:right">値</th></tr></thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>'''


def standings_html(standings):
    rows = standings.get('rows', [])
    update_date = standings.get('update_date', '')
    if not rows:
        return ''
    tsv = '\n'.join(f"{r['team']}\t{r['rank']}" for r in rows)
    tsv_attr = tsv.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    rows_html = ''.join(
        f'<tr><td class="rank">{r["rank"]}</td><td class="team">{r["team"]}</td>'
        f'<td class="num">{r["game"]}</td><td class="num">{r["win"]}</td>'
        f'<td class="num">{r["lose"]}</td><td class="num">{r["draw"]}</td>'
        f'<td class="pct">{r["pct"]}</td><td class="gb">{r["gb"]}</td></tr>'
        for r in rows
    )
    update_display = update_date[:16] if update_date else ''
    return f'''
  <div class="standings-card">
    <div class="card-head">
      <div><div class="card-title">順位表</div><div class="card-update">{update_display}</div></div>
      <button class="copy-btn" data-tsv="{tsv_attr}" onclick="copyTSV(this)">チーム名・順位 コピー</button>
    </div>
    <table>
      <thead><tr><th>順位</th><th>球団</th><th>試合</th><th>勝</th><th>負</th><th>分</th><th>勝率</th><th>差</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>'''


def generate(league):
    league_name = 'セ・リーグ' if league.upper() == 'C' else 'パ・リーグ'
    out_file = 'se.html' if league.upper() == 'C' else 'pa.html'
    print(f"\n[{league_name}] 取得中...")

    standings = fetch_standings(league)
    all_updates = [standings['update_date']] if standings.get('update_date') else []

    batter_cards = []
    for code, title, file_prefix, value_key in BATTER_STATS:
        d = fetch_ranking(file_prefix, value_key, league)
        batter_cards.append(card_html(title, d['update_date'], d['rows'], value_key))
        if d['update_date']:
            all_updates.append(d['update_date'])

    pitcher_cards = []
    for code, title, file_prefix, value_key in PITCHER_STATS:
        if league.upper() == 'C' and code == 'pct':
            pitcher_cards.append(f'<div class="card"><div class="card-head"><div><div class="card-title">{title}</div></div></div><div class="empty">セ・リーグでは勝率を使用しません</div></div>')
            continue
        d = fetch_ranking(file_prefix, value_key, league)
        pitcher_cards.append(card_html(title, d['update_date'], d['rows'], value_key))
        if d['update_date']:
            all_updates.append(d['update_date'])

    latest_update = max(all_updates) if all_updates else '（取得失敗）'

    html = HTML_TEMPLATE
    html = html.replace('__LEAGUE_NAME__', league_name)
    html = html.replace('__LATEST_UPDATE__', latest_update)
    html = html.replace('__STANDINGS__', standings_html(standings))
    html = html.replace('__BATTER_CARDS__', ''.join(batter_cards))
    html = html.replace('__PITCHER_CARDS__', ''.join(pitcher_cards))

    Path(out_file).write_text(html, encoding='utf-8')
    print(f"  ✅ {out_file} 生成完了 (最新更新: {latest_update})")


if __name__ == '__main__':
    generate('P')
    generate('C')
    print("\n完了: pa.html / se.html 更新しました")
