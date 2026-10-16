/* =============================================================================
 * cloud.js — 量子图谱查询台 · 云服务接入层（WorkBuddy Cloud Service）
 *
 * 接入模块：
 *   Auth      账号（邮箱密码 / 邮箱验证码 / 手机验证码）
 *   Database  查询历史 kg_queries、视图偏好 kg_user_prefs（均按 owner_id 行级隔离）
 *   LLM       自然语言问答（无需任何 API Key，由云服务代持上游凭据）
 *
 * 安全约定：
 *   - 前端只持有 publishableKey（标识应用、本身不含权限），不含任何长期密钥；
 *   - owner_id 一律由数据库 DEFAULT auth.uid() 填充，前端绝不发送；
 *   - 数据读写的隔离由 RLS 在服务端强制，前端只据此决定 UI 呈现。
 * ========================================================================== */
(function (global) {
  'use strict';

  /* ---- 开通云服务时返回的 publicConfig（可安全置于前端） ---- */
  const PUBLIC_CONFIG = {
    endpoint: 'https://quantum-graph-explorer.app.workbuddy.host',
    oauthRelayBaseUrl: 'https://www.workbuddy.cn/v2/as/genie-baas/oauth',
    publishableKey: 'wbpk_XktbF5bkETj6L1xkKP8JNY_6bVXixNvcPMMMjHAeji2gdi7Cytn7ucY'
  };

  /* ---------------------------------------------------------------- 客户端 */
  const SC = global.WorkBuddyCloud;
  let client = null;
  let initError = '';
  try {
    if (SC && typeof SC.createWorkBuddyCloud === 'function') {
      client = SC.createWorkBuddyCloud({
        endpoint: PUBLIC_CONFIG.endpoint,
        oauthRelayBaseUrl: PUBLIC_CONFIG.oauthRelayBaseUrl,
        publishableKey: PUBLIC_CONFIG.publishableKey
      });
    } else {
      initError = '云服务 SDK 未加载';
    }
  } catch (e) {
    initError = (e && e.message) || '云服务初始化失败';
  }

  const state = { user: null, session: null, prefs: null, prefsRowId: null, listeners: [] };
  const ready = !!client;

  function emit() { state.listeners.forEach(function (fn) { try { fn(state); } catch (e) {} }); }

  /* ------------------------------------------------------------ 错误与提示 */
  function errText(err, fallback) {
    if (!err) return fallback || '操作失败';
    const code = (err.error && err.error.code) || err.code || '';
    const msg = (err.error && err.error.message) || err.message || String(err);
    if (/^auth_/.test(code)) return '云服务拒绝本次访问：当前访问域名与该应用的发布域名不一致（请从应用发布链接进入）。';
    if (/^quota_/.test(code)) return '云服务额度不足或触发限流：' + msg;
    if (code === 'request_stream_required') return '云服务要求流式调用（内部参数错误）。';
    if (/^request_/.test(code)) return '请求参数不被接受：' + msg;
    if (/^gateway_|^model_/.test(code)) return '模型服务暂时不可用，请稍后重试。';
    if (code === '42P01') return '数据表不存在，请先在云数据库中初始化。';
    if (code === '42501') return '没有权限执行该操作（行级安全策略已拦截）。';
    if (code === '23505') return '该记录已存在。';
    return msg;
  }

  /* ------------------------------------------------------------------- Auth */
  const auth = {
    /** 当前会话（未登录返回 null） */
    async session() {
      if (!client) return null;
      const r = await client.auth.getSession();
      if (r.error || !r.data) return null;
      return r.data;
    },
    async signedUser() {
      if (!client) return null;
      try {
        const r = await client.auth.getUser();
        if (!r.error && r.data && r.data.user) return r.data.user;
      } catch (e) {}
      const s = await auth.session();
      return (s && s.user) || null;
    },
    /** 获取邮箱验证码 → { verificationId, isExistingUser } */
    async sendEmailCode(email) {
      const r = await client.auth.sendOtp({ email: email });
      if (r.error) throw r.error;
      return r.data;
    },
    /** 提交邮箱验证码（新用户需同时设置密码） */
    async verifyEmailOtp(pending, token, password) {
      const r = await client.auth.verifyOtp({
        email: pending.email,
        verificationId: pending.verificationId,
        isExistingUser: pending.isExistingUser,
        token: token,
        password: pending.isExistingUser ? undefined : password
      });
      if (r.error) throw r.error;
      return r.data;
    },
    /** 获取手机验证码 */
    async sendPhoneCode(phone) {
      const r = await client.auth.sendOtp({ phone: phone });
      if (r.error) throw r.error;
      return r.data;
    },
    async verifyPhoneOtp(pending, token) {
      const r = await client.auth.verifyOtp({
        phone: pending.phone,
        verificationId: pending.verificationId,
        isExistingUser: pending.isExistingUser,
        token: token
      });
      if (r.error) throw r.error;
      return r.data;
    },
    async signInPassword(email, password) {
      const r = await client.auth.signInWithPassword({ email: email, password: password });
      if (r.error) throw r.error;
      return r.data;
    },
    /** 忘记密码：发码 → 用码换新密码 */
    async startReset(email) {
      const r = await client.auth.resetPasswordForEmail(email);
      if (r.error) throw r.error;
      return r.data;
    },
    async finishReset(handle, nonce, newPassword) {
      const r = await handle.updateUser({ nonce: nonce, password: newPassword });
      if (r.error) throw r.error;
      return r.data;
    },
    async signOut() {
      if (client) { try { await client.auth.signOut(); } catch (e) {} }
      state.user = null; state.session = null; state.prefs = null; state.prefsRowId = null;
      emit();
    }
  };

  /* --------------------------------------------------------------- Database */
  const db = {
    /** 查询历史（RLS 自动只返回当前用户的行） */
    async listHistory(limit) {
      const r = await client.database.from('kg_queries')
        .select('id,question,cypher,answer,row_count,use_inferred,starred,created_at')
        .order('created_at', { ascending: false })
        .limit(limit || 30);
      if (r.error) throw r.error;
      return r.data || [];
    },
    /** 新增一条历史；owner_id 由数据库填充，这里绝不发送 */
    async addHistory(rec) {
      const r = await client.database.from('kg_queries')
        .insert({
          question: rec.question,
          cypher: rec.cypher || null,
          answer: rec.answer || null,
          row_count: (typeof rec.rowCount === 'number') ? rec.rowCount : null,
          use_inferred: !!rec.useInferred
        })
        .select();
      if (r.error) throw r.error;
      return (r.data && r.data[0]) || null;
    },
    /** 标星 / 取消标星；返回受影响行数（0 表示被 RLS 拦截或行不属于当前用户） */
    async setStar(id, starred) {
      const r = await client.database.from('kg_queries')
        .update({ starred: !!starred }).eq('id', id).select();
      if (r.error) throw r.error;
      return Array.isArray(r.data) ? r.data.length : 0;
    },
    async removeHistory(id) {
      const r = await client.database.from('kg_queries').delete().eq('id', id).select();
      if (r.error) throw r.error;
      return Array.isArray(r.data) ? r.data.length : 0;
    },
    async clearHistory() {
      const r = await client.database.from('kg_queries')
        .delete().not('id', 'is', null).select();
      if (r.error) throw r.error;
      return Array.isArray(r.data) ? r.data.length : 0;
    },
    /** 读取当前用户的视图偏好（可能为空 → null） */
    async loadPrefs() {
      const r = await client.database.from('kg_user_prefs')
        .select('id,hidden_types,fast_mode,use_inferred')
        .order('id', { ascending: true })
        .limit(1);
      if (r.error) throw r.error;
      const rows = r.data || [];
      return rows.length ? rows[0] : null;
    },
    /** 写入偏好：有行则更新，无行则插入 */
    async savePrefs(p, rowId) {
      const payload = {
        hidden_types: p.hiddenTypes || [],
        fast_mode: p.fastMode !== false,
        use_inferred: !!p.useInferred,
        updated_at: new Date().toISOString()
      };
      if (rowId) {
        const u = await client.database.from('kg_user_prefs')
          .update(payload).eq('id', rowId).select();
        if (u.error) throw u.error;
        if (Array.isArray(u.data) && u.data.length) return u.data[0];
        // 行已被删除（受影响 0 行）→ 走插入
      }
      const i = await client.database.from('kg_user_prefs').insert(payload).select();
      if (i.error) throw i.error;
      return (i.data && i.data[0]) || null;
    }
  };

  /* -------------------------------------------------------------------- LLM */
  let modelCache = null;
  const llm = {
    /** 模型目录（返回全部条目，含 disabled 标记；空数组是合法结果） */
    async models() {
      if (modelCache) return modelCache;
      const list = await client.llm.models.list();
      modelCache = Array.isArray(list) ? list : [];
      return modelCache;
    },
    /** 可选模型（disabled === true 的不可选） */
    async selectableModels() {
      const all = await llm.models();
      return all.filter(function (m) { return m.disabled !== true; });
    },
    /**
     * 一次性取回完整文本。云服务只支持流式，这里收集 SSE 分片。
     * messages[0] 必须是应用自有的 system 消息，否则调用会被拒绝。
     */
    async text(messages, modelId) {
      if (!messages || !messages.length || messages[0].role !== 'system') {
        throw new Error('内部错误：messages 首条必须是 system 消息');
      }
      let out = '';
      const stream = client.llm.chat.completions.create({
        model: modelId,
        messages: messages,
        stream: true,
        temperature: 1,
        stream_options: { include_usage: true }
      });
      for await (const chunk of stream) {
        const d = chunk && chunk.choices && chunk.choices[0] && chunk.choices[0].delta;
        if (d && d.content) out += d.content;
      }
      return out.trim();
    }
  };

  /* ------------------------------------------------------------------ 提示条 */
  function toast(msg, kind) {
    let el = document.getElementById('wbToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'wbToast';
      document.body.appendChild(el);
    }
    el.className = 'wbt-' + (kind || 'info');
    el.textContent = msg;
    el.style.display = 'block';
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.style.display = 'none'; }, kind === 'err' ? 7000 : 3600);
  }

  /* ------------------------------------------------------------------ 样式 */
  const CSS = [
    '#wbToast{position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:99;display:none;max-width:70vw;',
    'padding:9px 14px;border-radius:8px;font-size:13px;line-height:1.6;box-shadow:0 8px 24px rgba(15,23,42,.16);background:#fff;border:1px solid var(--line)}',
    '#wbToast.wbt-err{background:#fef2f2;border-color:#fecaca;color:#b91c1c}',
    '#wbToast.wbt-ok{background:#f0fdf4;border-color:#bbf7d0;color:#15803d}',
    '.wbauth{display:flex;align-items:center;gap:8px}',
    '.wbuser{display:flex;align-items:center;gap:7px;font-size:12.5px;background:#f1f5f9;border:1px solid var(--line);border-radius:16px;padding:3px 10px 3px 4px}',
    '.wbuser .av{width:20px;height:20px;border-radius:50%;background:#1f2933;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px}',
    '.wbmodal{position:fixed;inset:0;z-index:100;background:rgba(15,23,42,.42);display:none;align-items:center;justify-content:center}',
    '.wbmodal.show{display:flex}',
    '.wbbox{width:376px;max-width:94vw;max-height:90vh;overflow:auto;background:#fff;border-radius:12px;box-shadow:0 24px 60px rgba(15,23,42,.28)}',
    '.wbbox .hd{display:flex;align-items:center;justify-content:space-between;padding:13px 16px;border-bottom:1px solid var(--line)}',
    '.wbbox .hd h2{font-size:14.5px}',
    '.wbbox .hd .x{cursor:pointer;color:var(--sub);font-size:18px;line-height:1}',
    '.wbbox .bd{padding:14px 16px}',
    '.wbtabs{display:flex;gap:6px;margin-bottom:12px}',
    '.wbtabs button{flex:1;padding:7px 0;font-size:12.5px;border:1px solid var(--line);background:#fff;border-radius:7px;cursor:pointer;color:var(--sub)}',
    '.wbtabs button.on{background:#1f2937;border-color:#1f2937;color:#fff}',
    '.wbf{margin-bottom:9px}',
    '.wbf label{display:block;font-size:11.5px;color:var(--sub);margin-bottom:4px}',
    '.wbf input{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:7px;font-size:13px;font-family:inherit}',
    '.wbf input:focus{outline:none;border-color:#93c5fd}',
    '.wbrow{display:flex;gap:8px}',
    '.wbrow input{flex:1}',
    '.wbbtn{padding:8px 13px;border:1px solid var(--line);background:#fff;border-radius:7px;cursor:pointer;font-size:12.5px;color:var(--txt);white-space:nowrap}',
    '.wbbtn:hover{background:#f1f5f9}',
    '.wbbtn.p{background:#1f2933;border-color:#1f2933;color:#fff}',
    '.wbbtn.p:hover{background:#111827}',
    '.wbbtn:disabled{opacity:.55;cursor:not-allowed}',
    '.wbbtn.full{width:100%;margin-top:4px}',
    '.wbsep{display:flex;align-items:center;gap:8px;color:#94a3b8;font-size:11px;margin:12px 0}',
    '.wbsep::before,.wbsep::after{content:"";flex:1;height:1px;background:var(--line)}',
    '.wblink{color:#5f6b76;cursor:pointer;font-size:12px;text-decoration:underline}',
    '.wbhint{font-size:11.5px;color:var(--sub);line-height:1.7}',
    '.wberr{color:#b91c1c;font-size:12px;min-height:16px;margin-top:6px;line-height:1.5}',
    '#wbHistoryList{max-height:210px;overflow-y:auto}',
    '.wbhi{border:1px solid var(--line);border-radius:7px;padding:6px 8px;margin:4px 0;font-size:12px;cursor:pointer;background:#fff}',
    '.wbhi:hover{background:#f3f4f6;border-color:#d1d5db}',
    '.wbhi .q{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.wbhi .m{color:#94a3b8;font-size:11px;margin-top:2px;display:flex;gap:7px;align-items:center}',
    '.wbhi .m .sp{margin-left:auto;display:flex;gap:6px}',
    '.wbhi .m a{color:#94a3b8;text-decoration:none}',
    '.wbhi .m a.on{color:#f59e0b}',
    '.wbhi .m a:hover{color:#1f2933}',
    '.wbm{margin-top:6px;display:flex;flex-wrap:wrap;gap:6px}',
    '.wbm label{display:flex;align-items:center;gap:4px;font-size:12px;color:var(--sub);cursor:pointer;border:1px solid var(--line);border-radius:14px;padding:3px 9px}',
    '.wbm label.on{border-color:#9aa7b5;background:#f3f4f6;color:#1f2933}'
  ].join('');
  (function () {
    const s = document.createElement('style');
    s.textContent = CSS;
    (document.head || document.documentElement).appendChild(s);
  })();

  /* -------------------------------------------------------------- 账号 UI */
  function esc(s) {
    return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function displayName(u) {
    if (!u) return '已登录';
    const e = u.email || (u.phone ? String(u.phone).replace(/^\+\d+\s*/, '') : '');
    if (e) return e.length > 22 ? e.slice(0, 20) + '…' : e;
    return '已登录';
  }

  function modal(html) {
    let m = document.getElementById('wbModal');
    if (!m) {
      m = document.createElement('div');
      m.id = 'wbModal';
      m.className = 'wbmodal';
      document.body.appendChild(m);
      m.addEventListener('click', function (e) { if (e.target === m) closeModal(); });
    }
    m.innerHTML = '<div class="wbbox">' + html + '</div>';
    m.classList.add('show');
    return m;
  }
  function closeModal() {
    const m = document.getElementById('wbModal');
    if (m) { m.classList.remove('show'); m.innerHTML = ''; }
  }

  /* 登录弹窗 */
  const pending = { email: null, phone: null, reset: null };

  function loginHTML(tab) {
    tab = tab || 'email';
    let body;
    if (tab === 'email') {
      body = [
        '<div class="wbf"><label>邮箱</label><input id="wbEmail" type="email" autocomplete="username" placeholder="you@example.com"></div>',
        '<div class="wbf"><label>密码（新账号注册时需设置）</label><input id="wbPwd" type="password" autocomplete="current-password" placeholder="已有账号可只填密码直接登录"></div>',
        '<button class="wbbtn p full" id="wbLoginPwd">密码登录</button>',
        '<div class="wbsep">或使用邮箱验证码</div>',
        '<div class="wbf"><label>验证码</label><div class="wbrow"><input id="wbCode" inputmode="numeric" placeholder="6 位数字"><button class="wbbtn" id="wbGetCode">获取验证码</button></div></div>',
        '<button class="wbbtn full" id="wbLoginCode">验证码登录 / 注册</button>',
        '<div style="margin-top:9px;display:flex;justify-content:space-between"><span class="wblink" id="wbForgot">忘记密码</span><span class="wblink" id="wbToPhone">改用手机号 →</span></div>'
      ].join('');
    } else {
      body = [
        '<div class="wbf"><label>手机号</label><input id="wbPhone" type="tel" inputmode="numeric" placeholder="11 位手机号"></div>',
        '<div class="wbf"><label>验证码</label><div class="wbrow"><input id="wbCode" inputmode="numeric" placeholder="6 位数字"><button class="wbbtn" id="wbGetCode">获取验证码</button></div></div>',
        '<button class="wbbtn p full" id="wbLoginPhone">登录 / 注册</button>',
        '<div style="margin-top:9px"><span class="wblink" id="wbToEmail">← 改用邮箱</span></div>'
      ].join('');
    }
    return [
      '<div class="hd"><h2>登录 · 量子图谱查询台</h2><span class="x" id="wbClose">×</span></div>',
      '<div class="bd">',
      '<div class="wbtabs"><button data-tab="email" class="' + (tab === 'email' ? 'on' : '') + '">邮箱</button>',
      '<button data-tab="phone" class="' + (tab === 'phone' ? 'on' : '') + '">手机号</button></div>',
      body,
      '<div class="wberr" id="wbErr"></div>',
      '<div class="wbhint" style="margin-top:10px;border-top:1px solid var(--line);padding-top:9px">',
      '登录后可用：<b>查询历史云端留存</b>（跨设备同步、可标星）与 <b>视图偏好同步</b>。',
      '未登录也可正常使用图谱与自然语言问答。</div>',
      '</div>'
    ].join('');
  }

  function setErr(msg) {
    const e = document.getElementById('wbErr');
    if (e) e.textContent = msg || '';
  }
  function busy(sel, on, label) {
    const b = document.querySelector(sel);
    if (!b) return;
    b.disabled = !!on;
    if (label) b.textContent = label;
  }
  function countdown(btnSel) {
    const b = document.querySelector(btnSel);
    if (!b) return;
    let n = 60;
    b.disabled = true;
    const t = setInterval(function () {
      b.textContent = '重发 ' + n + 's';
      if (--n < 0) { clearInterval(t); b.disabled = false; b.textContent = '重新获取'; }
    }, 1000);
  }

  function openLogin(tab) {
    if (!ready) { toast('云服务不可用：' + (initError || '请从应用发布链接访问'), 'err'); return; }
    modal(loginHTML(tab));
    wireLogin();
  }

  function wireLogin() {
    const close = document.getElementById('wbClose');
    if (close) close.onclick = closeModal;
    document.querySelectorAll('.wbtabs button').forEach(function (b) {
      b.onclick = function () { openLogin(b.dataset.tab); };
    });
    const toPhone = document.getElementById('wbToPhone');
    if (toPhone) toPhone.onclick = function () { openLogin('phone'); };
    const toEmail = document.getElementById('wbToEmail');
    if (toEmail) toEmail.onclick = function () { openLogin('email'); };

    /* --- 邮箱：密码登录 --- */
    const lp = document.getElementById('wbLoginPwd');
    if (lp) lp.onclick = async function () {
      const email = (document.getElementById('wbEmail').value || '').trim();
      const pwd = document.getElementById('wbPwd').value || '';
      if (!email || !pwd) { setErr('请输入邮箱与密码'); return; }
      busy('#wbLoginPwd', true, '登录中…');
      try {
        await auth.signInPassword(email, pwd);
        closeModal(); toast('已登录', 'ok'); await afterSignIn();
      } catch (e) { setErr('账号或密码不正确（' + errText(e) + '）'); busy('#wbLoginPwd', false, '密码登录'); }
    };

    /* --- 邮箱：获取验证码 --- */
    const gc = document.getElementById('wbGetCode');
    const isEmail = !!document.getElementById('wbEmail');
    if (gc) gc.onclick = async function () {
      if (isEmail) {
        const email = (document.getElementById('wbEmail').value || '').trim();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setErr('请输入正确的邮箱地址'); return; }
        setErr(''); busy('#wbGetCode', true, '发送中…');
        try {
          const d = await auth.sendEmailCode(email);
          pending.email = { email: email, verificationId: d.verificationId, isExistingUser: d.isExistingUser };
          toast('验证码已发送，请查收邮箱', 'ok'); countdown('#wbGetCode');
        } catch (e) { setErr('发送失败：' + errText(e)); busy('#wbGetCode', false, '获取验证码'); }
      } else {
        const phone = (document.getElementById('wbPhone').value || '').trim();
        if (!/^1\d{10}$/.test(phone)) { setErr('请输入正确的 11 位手机号'); return; }
        setErr(''); busy('#wbGetCode', true, '发送中…');
        try {
          const d = await auth.sendPhoneCode(phone);
          pending.phone = { phone: phone, verificationId: d.verificationId, isExistingUser: d.isExistingUser };
          toast('验证码已发送', 'ok'); countdown('#wbGetCode');
        } catch (e) { setErr('发送失败：' + errText(e)); busy('#wbGetCode', false, '获取验证码'); }
      }
    };

    /* --- 邮箱：验证码登录 / 注册 --- */
    const lc = document.getElementById('wbLoginCode');
    if (lc) lc.onclick = async function () {
      const email = (document.getElementById('wbEmail').value || '').trim();
      const code = (document.getElementById('wbCode').value || '').trim();
      const pwd = document.getElementById('wbPwd').value || '';
      if (!pending.email || pending.email.email !== email) { setErr('请先获取该邮箱的验证码'); return; }
      if (!code) { setErr('请输入验证码'); return; }
      if (!pending.email.isExistingUser && !pwd) { setErr('该邮箱尚未注册，请设置密码后提交（用于日后密码登录）'); return; }
      busy('#wbLoginCode', true, '验证中…');
      try {
        await auth.verifyEmailOtp(pending.email, code, pwd);
        pending.email = null; closeModal(); toast('已登录', 'ok'); await afterSignIn();
      } catch (e) { setErr('验证失败：' + errText(e)); busy('#wbLoginCode', false, '验证码登录 / 注册'); }
    };

    /* --- 邮箱：忘记密码 --- */
    const fg = document.getElementById('wbForgot');
    if (fg) fg.onclick = async function () {
      const email = (document.getElementById('wbEmail').value || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setErr('请先填写邮箱，再点“忘记密码”'); return; }
      busy('#wbForgot', true, '发送中…');
      try {
        pending.reset = await auth.startReset(email);
        toast('重置验证码已发送，请在下方输入新密码', 'ok');
        setErr(''); busy('#wbForgot', false, '忘记密码');
        const code = prompt('请输入邮件中的重置验证码：');
        if (!code) return;
        const np = prompt('请设置新密码（至少 6 位）：');
        if (!np) return;
        await auth.finishReset(pending.reset, code.trim(), np);
        pending.reset = null; toast('密码已重置并登录', 'ok'); closeModal(); await afterSignIn();
      } catch (e) { setErr('重置失败：' + errText(e)); busy('#wbForgot', false, '忘记密码'); }
    };

    /* --- 手机：验证码登录 --- */
    const lph = document.getElementById('wbLoginPhone');
    if (lph) lph.onclick = async function () {
      const phone = (document.getElementById('wbPhone').value || '').trim();
      const code = (document.getElementById('wbCode').value || '').trim();
      if (!pending.phone || pending.phone.phone !== phone) { setErr('请先获取该手机号的验证码'); return; }
      if (!code) { setErr('请输入验证码'); return; }
      busy('#wbLoginPhone', true, '验证中…');
      try {
        await auth.verifyPhoneOtp(pending.phone, code);
        pending.phone = null; closeModal(); toast('已登录', 'ok'); await afterSignIn();
      } catch (e) { setErr('验证失败：' + errText(e)); busy('#wbLoginPhone', false, '登录 / 注册'); }
    };
  }

  /* -------------------------------------------------------- 账号区 / 历史区 */
  function renderAuthArea() {
    const el = document.getElementById('wbAuth');
    if (!el) return;
    if (!ready) {
      el.innerHTML = '<span class="wbhint" title="' + esc(initError) + '">云服务未连接</span>';
      return;
    }
    if (state.user) {
      el.innerHTML = '<span class="wbuser"><span class="av">' + esc((displayName(state.user)[0] || 'U').toUpperCase()) +
        '</span>' + esc(displayName(state.user)) + '</span>' +
        '<button class="wbbtn" id="wbOut">退出</button>';
      const o = document.getElementById('wbOut');
      if (o) o.onclick = function () { auth.signOut().then(function () { toast('已退出登录'); }); };
    } else {
      el.innerHTML = '<button class="wbbtn" id="wbIn">登录</button>';   // 描边按钮：不与左栏「查询图谱」主按钮抢视觉
      const i = document.getElementById('wbIn');
      if (i) i.onclick = function () { openLogin('email'); };
    }
  }

  function fmtTime(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const p = function (n) { return (n < 10 ? '0' : '') + n; };
      return (d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
    } catch (e) { return ''; }
  }

  let historyCache = [];
  function renderHistory() {
    const wrap = document.getElementById('wbHistory');
    const list = document.getElementById('wbHistoryList');
    if (!wrap || !list) return;
    if (!state.user) { wrap.style.display = 'none'; return; }
    wrap.style.display = '';
    const cnt = document.getElementById('wbHistCount');
    if (cnt) cnt.textContent = String(historyCache.length);
    const clr = document.getElementById('wbHistClear');
    if (clr) clr.onclick = async function () {
      if (!historyCache.length) { toast('当前没有历史记录'); return; }
      if (!confirm('确定清空你的全部查询历史（共 ' + historyCache.length + ' 条）？该操作不可撤销。')) return;
      try {
        const n = await db.clearHistory();
        historyCache = []; renderHistory();
        toast('已清空 ' + n + ' 条历史记录', 'ok');
      } catch (e) { toast('清空失败：' + errText(e), 'err'); }
    };
    if (!historyCache.length) {
      list.innerHTML = '<div class="wbhint" style="padding:4px 2px">还没有查询记录。提问一次即自动留存（可跨设备查看）。</div>';
      return;
    }
    list.innerHTML = historyCache.map(function (h) {
      return '<div class="wbhi" data-id="' + h.id + '">' +
        '<div class="q">' + esc(h.question) + '</div>' +
        '<div class="m">' + esc(fmtTime(h.created_at)) +
        (typeof h.row_count === 'number' ? ' · ' + h.row_count + ' 行' : '') +
        (h.use_inferred ? ' · 含推断层' : '') +
        '<span class="sp">' +
        '<a href="javascript:void 0" class="st' + (h.starred ? ' on' : '') + '" title="标星">' + (h.starred ? '★' : '☆') + '</a>' +
        '<a href="javascript:void 0" class="rm" title="删除">✕</a>' +
        '</span></div></div>';
    }).join('');
    list.querySelectorAll('.wbhi').forEach(function (row) {
      const id = +row.dataset.id;
      const rec = historyCache.find(function (x) { return x.id === id; });
      row.onclick = function (ev) {
        if (ev.target.classList.contains('st') || ev.target.classList.contains('rm')) return;
        if (rec && rec.cypher && typeof global.__wbRunCypher === 'function') {
          global.__wbRunCypher(rec.cypher, rec.use_inferred);
          toast('已按历史中的 Cypher 重新查询');
        } else if (rec && typeof global.__wbAsk === 'function') {
          global.__wbAsk(rec.question, rec.use_inferred);
        }
      };
      const st = row.querySelector('.st');
      if (st) st.onclick = async function () {
        try {
          const n = await db.setStar(id, !rec.starred);
          if (!n) { toast('未能修改：该记录不属于当前账号', 'err'); return; }
          rec.starred = !rec.starred; renderHistory();
        } catch (e) { toast(errText(e), 'err'); }
      };
      const rm = row.querySelector('.rm');
      if (rm) rm.onclick = async function () {
        try {
          const n = await db.removeHistory(id);
          if (!n) { toast('未能删除：该记录不属于当前账号', 'err'); return; }
          historyCache = historyCache.filter(function (x) { return x.id !== id; });
          renderHistory(); toast('已删除');
        } catch (e) { toast(errText(e), 'err'); }
      };
    });
  }

  async function refreshHistory() {
    if (!state.user) { historyCache = []; renderHistory(); return; }
    try {
      historyCache = await db.listHistory(30);
    } catch (e) {
      historyCache = [];
      toast('查询历史加载失败：' + errText(e), 'err');
    }
    renderHistory();
  }

  /** 登录后的统一收尾：加载偏好 + 历史 */
  async function afterSignIn() {
    state.session = await auth.session();
    state.user = await auth.signedUser();
    emit(); renderAuthArea();
    await Promise.all([loadCloudPrefs(), refreshHistory()]);
  }

  /* --------------------------------------------------------------- 偏好同步 */
  async function loadCloudPrefs() {
    if (!state.user) return null;
    try {
      const row = await db.loadPrefs();
      if (!row) return null;
      state.prefsRowId = row.id;
      state.prefs = row;
      if (typeof global.__wbApplyPrefs === 'function') {
        global.__wbApplyPrefs({
          hiddenTypes: row.hidden_types || [],
          fastMode: row.fast_mode !== false,
          useInferred: !!row.use_inferred
        });
      }
      return row;
    } catch (e) {
      toast('偏好同步失败：' + errText(e), 'err');
      return null;
    }
  }

  let prefsTimer = null;
  /** 页面偏好变化时调用（可只传变化的部分）；未登录则只留在本机 */
  function pushPrefs(partial) {
    if (!state.user) return;
    const cur = state.prefs || { hiddenTypes: [], fastMode: true, useInferred: false };
    state.prefs = Object.assign({}, cur, partial || {});
    const snap = state.prefs;
    clearTimeout(prefsTimer);
    prefsTimer = setTimeout(async function () {
      try {
        const row = await db.savePrefs({
          hiddenTypes: snap.hiddenTypes, fastMode: snap.fastMode, useInferred: snap.useInferred
        }, state.prefsRowId);
        if (row && row.id) state.prefsRowId = row.id;
      } catch (e) { toast('偏好同步失败：' + errText(e), 'err'); }
    }, 600);
  }

  /* --------------------------------------------------------------- 对外 API */
  const WB = {
    ready: ready,
    initError: initError,
    PUBLIC_CONFIG: PUBLIC_CONFIG,
    client: client,
    state: state,
    auth: auth,
    db: db,
    llm: llm,
    toast: toast,
    errText: errText,
    openLogin: openLogin,
    onAuth: function (fn) { state.listeners.push(fn); },
    onPrefsChanged: pushPrefs,
    refreshHistory: refreshHistory,
    /** 记录一次成功的自然语言查询（未登录时静默跳过） */
    async recordQuery(rec) {
      if (!state.user) return null;
      try {
        const row = await db.addHistory(rec);
        if (row) { historyCache.unshift(row); if (historyCache.length > 30) historyCache.pop(); renderHistory(); }
        return row;
      } catch (e) { toast('历史留存失败：' + errText(e), 'err'); return null; }
    }
  };
  global.WB = WB;

  /* ------------------------------------------------------------------ 启动 */
  async function boot() {
    renderAuthArea();
    renderHistory();
    if (!ready) return;
    try {
      const s = await auth.session();
      if (s) {
        state.session = s;
        state.user = (s && s.user) || await auth.signedUser();
        emit(); renderAuthArea();
        await Promise.all([loadCloudPrefs(), refreshHistory()]);
      }
    } catch (e) { /* 未登录是正常状态 */ }
    try {
      if (client.auth.onAuthStateChange) {
        client.auth.onAuthStateChange(function (event, session) {
          if (event === 'SIGNED_OUT') {
            state.user = null; state.session = null; state.prefs = null; state.prefsRowId = null;
            historyCache = []; renderAuthArea(); renderHistory();
          }
        });
      }
    } catch (e) {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

})(window);
