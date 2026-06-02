#!/usr/bin/env node

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '.');
const captchaPath = path.join(root, 'captcha.js');
const wasmPath = path.join(root, 'index.wasm');
const DEBUG_ENABLED = process.env.CAPTCHA_DEBUG === '1';
const DEFAULT_RUNTIME = 'local-jsdom';
const DEFAULT_USER_AGENT =
  process.env.CAPTCHA_WEB_UA ||
  ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ' +
  '(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36');
const DEFAULT_DATA_IMAGE =
  'data:image/png;base64,' +
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9bP8UAAAAASUVORK5CYII=';

const CDP_HTTP = process.env.CAPTCHA_CDP_HTTP || 'http://127.0.0.1:9334';
const CDP_PAGE_MATCH = process.env.CAPTCHA_CDP_PAGE_MATCH || 'rmc.bytedance.com/verifycenter/captcha/v2';

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function httpJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${url}`);
  }
  return response.json();
}

async function findLivePage(pageUrl) {
  const pages = await httpJson(`${CDP_HTTP}/json/list`);
  const exact = pages.find((p) => p.type === 'page' && p.webSocketDebuggerUrl && p.url === pageUrl);
  if (exact) return exact;
  // For browser-live encryption the page URL matters: render config/detail/env
  // are taken from options.pageUrl, so prefer a fresh exact tab over reusing an
  // unrelated old captcha tab.
  const created = await httpJson(`${CDP_HTTP}/json/new?${encodeURIComponent(pageUrl)}`, { method: 'PUT' });
  await sleep(800);
  return created;
}

class SimpleCdp {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
  }
  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('CDP websocket timeout')), 5000);
      this.ws.onopen = () => { clearTimeout(timer); resolve(); };
      this.ws.onerror = (err) => { clearTimeout(timer); reject(err); };
    });
    this.ws.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch (e) { return; }
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject, timer } = this.pending.get(msg.id);
        clearTimeout(timer);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(`CDP error ${JSON.stringify(msg.error)}`));
        else resolve(msg);
      }
    };
  }
  call(method, params = {}, timeoutMs = 30000) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP ${method} timeout`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
    });
  }
  async eval(expression, timeoutMs = 60000) {
    const result = await this.call('Runtime.evaluate', {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
      timeout: timeoutMs,
    }, timeoutMs + 5000);
    const root = result.result || {};
    if (root.exceptionDetails) {
      throw new Error(`Runtime exception ${JSON.stringify(root.exceptionDetails).slice(0, 1000)}`);
    }
    return root.result && root.result.value;
  }
  close() {
    try { this.ws.close(); } catch (e) {}
  }
}

async function runLiveBrowserEncrypt(options, payloadText, detail, order, tagStateOps) {
  const page = await findLivePage(options.pageUrl);
  const cdp = new SimpleCdp(page.webSocketDebuggerUrl);
  await cdp.connect();
  try {
    await cdp.call('Runtime.enable', {}, 5000).catch(() => {});
    await sleep(500);
    const expression = `
(async () => {
  const payloadText = ${JSON.stringify(payloadText)};
  const payload = JSON.parse(payloadText);
  const detail = ${JSON.stringify(detail)};
  const order = ${JSON.stringify(Array.from(order || []))};
  const tagStateOps = ${JSON.stringify(tagStateOps || null)};
  const targetPageUrl = ${JSON.stringify(options.pageUrl)};
  function sleep(ms){ return new Promise(r => setTimeout(r, ms)); }
  function buildConfigFromUrl(pageUrl) {
    const url = new URL(pageUrl || location.href);
    const query = url.searchParams;
    let env = {};
    try { env = JSON.parse(query.get('env') || '{}'); } catch (e) {}
    if (!document.getElementById('captcha_container')) {
      const div = document.createElement('div');
      div.id = 'captcha_container';
      div.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden;';
      document.body.appendChild(div);
    }
    return {
      info: {
        aid: query.get('aid') || '', appName: query.get('appName') || '', lang: query.get('lang') || 'zh',
        did: query.get('did') || '', fp: query.get('fp') || '', repoId: query.get('repoId') || '', pageId: query.get('pageId') || ''
      },
      ele: query.get('ele') || 'captcha_container',
      host: query.get('host') || '//verify.zijieapi.com/',
      baseEM: query.get('baseEM') || '', viewport: query.get('viewport') === 'false' ? false : true,
      hideCloseBtn: query.get('hideCloseBtn') === 'true', theme: query.get('theme') || 'light',
      env, extraConfig: query.get('extraConfig') || '{}', static_domain: query.get('static_domain') || '',
      successCb(){}, errorCb(){}, closeCb(){}, onSuccess(){}, onClose(){}, onError(){}, log(){}
    };
  }
  async function makeOwnRuntime(pageUrl) {
    if (!window.bdCaptcha || typeof window.bdCaptcha.CaptchaVerify !== 'function') return null;
    const query = new URL(pageUrl || location.href).searchParams;
    const verifyData = query.get('verify_data');
    const runtimeKey = '__dy759LiveInst_' + (payload && payload.id ? payload.id : 'default');
    if (!window[runtimeKey]) {
      window[runtimeKey] = new window.bdCaptcha.CaptchaVerify(buildConfigFromUrl(pageUrl));
      if (window[runtimeKey].init) {
        const initRet = window[runtimeKey].init();
        if (initRet && initRet.then) await initRet;
      }
    }
    const inst = window[runtimeKey];
    if (verifyData && inst.render && (!inst.captcha || !inst.captcha.wasm)) {
      try {
        const renderRet = inst.render(verifyData);
        if (renderRet && renderRet.then) await renderRet;
      } catch (e) {}
    }
    return inst;
  }
  async function waitRuntime(timeoutMs) {
    const end = Date.now() + timeoutMs;
    while (Date.now() < end) {
      const insts = [];
      const runtimeKey = '__dy759LiveInst_' + (payload && payload.id ? payload.id : 'default');
      if (window[runtimeKey]) insts.push(window[runtimeKey]);
      if (window.__dy759Instances) insts.push(...window.__dy759Instances);
      if (window.__dy759Probe && window.__dy759Probe.instances) insts.push(...window.__dy759Probe.instances);
      for (const inst of insts) {
        if (inst && inst.captcha && inst.captcha.id && inst.captcha.id !== payload.id) {
          continue;
        }
        if (inst && inst.captcha && inst.captcha.wasm && (inst.captcha.wasm.encrypt || inst.captcha.wasm.invoke)) {
          return { captcha: inst.captcha, wasm: inst.captcha.wasm };
        }
      }
      if (typeof window.__dy759ScanForCaptcha === 'function') {
        try { window.__dy759ScanForCaptcha(); } catch (e) {}
      }
      try { await makeOwnRuntime(targetPageUrl); } catch (e) {}
      await sleep(100);
    }
    throw new Error('live captcha wasm runtime not found in page');
  }
  const { captcha, wasm } = await waitRuntime(8000);
  if (wasm.loadTask && wasm.loadTask.then) await wasm.loadTask;
  async function invoke(name, argTypes, argValues) {
    if (typeof wasm.invoke !== 'function') throw new Error('wasm.invoke missing: ' + name);
    return wasm.invoke(name, null, argTypes, argValues);
  }
  const ops = Array.isArray(tagStateOps) && tagStateOps.length ? tagStateOps : null;
  if (ops) {
    for (const op of ops) {
      const args = Array.isArray(op.args) ? op.args : [];
      if (op.name === 'tagZInit') {
        if (wasm.tagZInit) await wasm.tagZInit(args[0] == null ? detail : args[0]);
        else await invoke('tag_z_init', ['string','number'], [args[0] == null ? detail : args[0], String(args[0] == null ? detail : args[0]).length]);
      } else if (op.name === 'pushGetID') {
        if (wasm.pushGetID) await wasm.pushGetID(args[0] == null ? payload.id : args[0]);
        else await invoke('tag_z_push_getid', ['string','number'], [args[0] == null ? payload.id : args[0], String(args[0] == null ? payload.id : args[0]).length]);
      } else if (op.name === 'tagYInit') {
        if (wasm.tagYInit) await wasm.tagYInit(); else await invoke('tag_y_init', [], []);
      } else if (op.name === 'tagYEntry') {
        const idx = Number(args[0]);
        if (wasm.tagYEntry) await wasm.tagYEntry(idx); else await invoke('tag_y_entry' + idx, [], []);
      }
    }
  } else {
    if (wasm.tagZInit) await wasm.tagZInit(detail); else await invoke('tag_z_init', ['string','number'], [detail, detail.length]);
    if (wasm.pushGetID) await wasm.pushGetID(payload.id); else await invoke('tag_z_push_getid', ['string','number'], [payload.id, payload.id.length]);
    if (wasm.tagYInit) await wasm.tagYInit(); else await invoke('tag_y_init', [], []);
    for (const idx of order) {
      if (wasm.tagYEntry) await wasm.tagYEntry(idx); else await invoke('tag_y_entry' + idx, [], []);
    }
  }
  const body = wasm.encrypt ? await wasm.encrypt(payloadText) : await invoke('entry', ['string','number'], [payloadText, payloadText.length]);
  return { captchaBody: body, hookKeys: Object.keys(wasm), preEncryptSnapshot: { source: 'browser-live', payloadId: payload.id, payloadLength: payloadText.length, order } };
})()
`;
    return await cdp.eval(expression, 90000);
  } finally {
    cdp.close();
  }
}

const defaultPageUrl =
    'https://rmc.bytedance.com/verifycenter/captcha/v2?from=iframe&fp=verify_mncjwsfo_X4z7ByzP_aO5W_4Ff3_BGPT_KQJmre7f78VE&env=%7B%22screen%22%3A%7B%22w%22%3A1470%2C%22h%22%3A956%7D%2C%22browser%22%3A%7B%22w%22%3A1470%2C%22h%22%3A798%7D%2C%22page%22%3A%7B%22w%22%3A1470%2C%22h%22%3A369%7D%2C%22document%22%3A%7B%22width%22%3A1470%7D%2C%22product_host%22%3A%22www.life-data.cn%22%2C%22vc_version%22%3A%221.0.0.287%22%2C%22maskTime%22%3A1774836640904%2C%22h5_check_version%22%3A%224.0.5%22%7D&aid=480844&repoId=579047&scene_level=p0&host=https%3A%2F%2Fverify.zijieapi.com&lang=zh&verify_data=%7B%22code%22%3A%2210000%22%2C%22from%22%3A%22shark_admin%22%2C%22type%22%3A%22verify%22%2C%22version%22%3A%221%22%2C%22region%22%3A%22cn%22%2C%22subtype%22%3A%22slide%22%2C%22ui_type%22%3A%22%22%2C%22detail%22%3A%22PnW77Kjz3kFXECIIHc04R2o*saKxWWAQ--RXsLJrp53ckqVuemMuuqIEK8iCzGRmYj1oO7w*xP6pkzMH5FiNCXzBIvBMUiAsOOldmaKhFtsZycKC5SQe4t5Lisgnd-c886FmLiG954JgDDxM4zO5BGJhaGKpH5d65CJU2P4-oEnSjGNf0Vq0Xjj1tGxIAfTSY6PULdPk8hm9UCAGgONl5QoOCfi9Z5Jwy4QXJAI0B38GBpzzdtwF9bETFsAmELnzBPz1-i1ERrr61uDKEWDhT0hjwSn4zjQRA4aAMiDDyErNFnM9R4kokQghsMRJ2BMLe-PJi-hVGw1rJNdOuKh9T-fpf5bAoiFsl8f2IDQvqaStLNHhfEUzrIT8WFM-qV*JRd4q9hUPOA..%22%2C%22verify_event%22%3A%22tt_sso_send_code%22%2C%22fp%22%3A%22verify_mncjwsfo_X4z7ByzP_aO5W_4Ff3_BGPT_KQJmre7f78VE%22%2C%22verify_ticket%22%3A%22VTIDEFXPCSNXWMNQD6A4NHZTGCQM46K6HSF8RG_lf%22%2C%22server_sdk_env%22%3A%22%7B%5C%22idc%5C%22%3A%5C%22lf%5C%22%2C%5C%22region%5C%22%3A%5C%22CN%5C%22%2C%5C%22server_type%5C%22%3A%5C%22passport%5C%22%7D%22%2C%22log_id%22%3A%2220260330101040AF7EA871F017165562B6%22%2C%22is_assist_mobile%22%3Afalse%2C%22is_complex_sms%22%3Afalse%2C%22identity_action%22%3A%22%22%2C%22identity_scene%22%3A%22%22%2C%22verify_scene%22%3A%22passport%22%2C%22login_status%22%3A0%2C%22aid%22%3A0%2C%22replay_data%22%3A%7B%22x-tt-passport-replay-params%22%3A%22%7B%7D%22%7D%7D&extraConfig=%7B%7D'

const defaultPayload =
'{"modified_img_width":340,"id":"2429a6d6f015dd4cbdd6cc8c6c915307a80b6e08","mode":"slide","c":[6,7,13,4,3],"8uyk1GN":[{"x":0,"y":81,"relative_time":18},{"x":1,"y":81,"relative_time":183},{"x":2,"y":81,"relative_time":200},{"x":5,"y":81,"relative_time":218},{"x":8,"y":81,"relative_time":233},{"x":13,"y":81,"relative_time":250},{"x":19,"y":81,"relative_time":267},{"x":25,"y":81,"relative_time":284},{"x":33,"y":81,"relative_time":300},{"x":40,"y":81,"relative_time":316},{"x":45,"y":81,"relative_time":333},{"x":51,"y":81,"relative_time":350},{"x":56,"y":81,"relative_time":367},{"x":59,"y":81,"relative_time":383},{"x":62,"y":81,"relative_time":400},{"x":64,"y":81,"relative_time":418},{"x":65,"y":81,"relative_time":434},{"x":65,"y":81,"relative_time":451},{"x":65,"y":81,"relative_time":550},{"x":65,"y":81,"relative_time":566},{"x":65,"y":81,"relative_time":583},{"x":64,"y":81,"relative_time":600},{"x":63,"y":81,"relative_time":617},{"x":62,"y":81,"relative_time":634}],"1ZBkmqar4":[],"Q1FvvZeZE":{"AGV8DioD":{"x":238,"y":276,"time":1774839484176},"2MILE":{"x":38,"y":327,"time":1774839619748},"J9c":[{"x":39,"y":349,"time":1774839619199},{"x":39,"y":347,"time":1774839619241},{"x":39,"y":345,"time":1774839619291},{"x":39,"y":344,"time":1774839619329},{"x":39,"y":343,"time":1774839619375},{"x":39,"y":341,"time":1774839619411},{"x":40,"y":340,"time":1774839619452},{"x":40,"y":338,"time":1774839619493},{"x":40,"y":337,"time":1774839619534},{"x":40,"y":336,"time":1774839619575},{"x":40,"y":335,"time":1774839619616},{"x":40,"y":333,"time":1774839619658},{"x":39,"y":330,"time":1774839619698},{"x":38,"y":328,"time":1774839619741},{"x":37,"y":326,"time":1774839619775},{"x":37,"y":324,"time":1774839619813},{"x":37,"y":322,"time":1774839619855},{"x":37,"y":319,"time":1774839619895},{"x":37,"y":316,"time":1774839619939},{"x":37,"y":314,"time":1774839619977},{"x":38,"y":312,"time":1774839620018},{"x":42,"y":310,"time":1774839620060},{"x":44,"y":309,"time":1774839620128},{"x":45,"y":309,"time":1774839620293},{"x":49,"y":309,"time":1774839620328},{"x":63,"y":309,"time":1774839620376},{"x":77,"y":309,"time":1774839620410},{"x":95,"y":309,"time":1774839620460},{"x":106,"y":310,"time":1774839620509},{"x":109,"y":310,"time":1774839620544},{"x":109,"y":310,"time":1774839620660},{"x":108,"y":310,"time":1774839620709},{"x":106,"y":309,"time":1774839620744}],"FrZXd9GD":[],"rHqT9pMS":[{"x":44,"y":309,"time":1774839620110,"t":0},{"x":44,"y":309,"time":1774839620128,"t":0},{"x":46,"y":309,"time":1774839620310,"t":0},{"x":52,"y":309,"time":1774839620343,"t":0},{"x":63,"y":309,"time":1774839620377,"t":0},{"x":77,"y":309,"time":1774839620410,"t":0},{"x":89,"y":309,"time":1774839620443,"t":0},{"x":100,"y":309,"time":1774839620477,"t":0},{"x":106,"y":310,"time":1774839620510,"t":0},{"x":109,"y":310,"time":1774839620544,"t":0},{"x":109,"y":310,"time":1774839620660,"t":0},{"x":109,"y":310,"time":1774839620693,"t":0},{"x":107,"y":310,"time":1774839620727,"t":0}],"pE2N":[]},"env":{"canvas_hash":"20be8370141b74c676508259b0abddaa","webgl_hash":"52497e308a4259f66bf07a8977e40d65","font_hash":"1ba6a6ed1090cd3ef107372e43853b43ad797cb8ab46","audio_hash":194.04348155876505,"time_offset":-480,"time_zone":"Asia/Shanghai","languages":["zh-CN"],"plugins":["PDF Viewer","Chrome PDF Viewer","Chromium PDF Viewer","Microsoft Edge PDF Viewer","WebKit built-in PDF"],"platform":"MacIntel","max_touch_points":0,"webdriver":false,"touch_actions":[],"mouse_actions":["1,1","1,1","1,1","1,1"],"device":{"model":"Macintosh","vendor":"Apple"},"os":{"name":"Mac OS","version":"10.15.7"},"browser":{"name":"Chrome","version":"146.0.0.0","vendor":[0,1]},"engine":{"name":"Blink","version":"146.0.0.0"},"gpu":{"vendor":"Google Inc. (Apple)","renderer":"ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)"},"c":[2,1,9,124,6],"d":3549673283791,"f":8,"k":[4,4,2],"m":["0","5","7‍‍‍"],"n":[33],"o":[4],"fps":45,"resolution":"1470,956","browser_size":"1470,798","page_size":"1470,369","captcha_origin":"0,0","captcha_size":"380, 384","mask_time":177483664090407,"loading_time":1774836641357,"ready_time":1774836641894,"detectors":{"RegToString":{"enabled":false,"value":0},"DefineId":{"enabled":true,"value":0},"DateToString":{"enabled":true,"value":0},"FuncToString":{"enabled":true,"value":0},"Debugger":{"enabled":false,"value":0},"Performance":{"enabled":true,"value":1},"DebugLib":{"enabled":true,"value":0}},"scale":"1.0.0.8","g":10},"a":98,"b":73}'
function debugLog() {
  if (!DEBUG_ENABLED) {
    return;
  }
  process.stderr.write(
    Array.from(arguments)
      .map((item) => (typeof item === 'string' ? item : JSON.stringify(item)))
      .join(' ') + '\n'
  );
}

function readText(filePath, label) {
  const resolved = path.resolve(filePath);
  try {
    return fs.readFileSync(resolved, 'utf8').trim();
  } catch (error) {
    throw new Error(`failed to read ${label}: ${resolved}`);
  }
}

function safeParseJson(text, label) {
  try {
    return JSON.parse(text);
  } catch (error) {
    const reason =
      error && typeof error.message === 'string' ? error.message : String(error);
    throw new Error(`invalid ${label} JSON: ${reason}`);
  }
}

function parseExplicitOrder(orderText) {
  if (!orderText) {
    return null;
  }
  const order = String(orderText)
    .split(',')
    .map((item) => Number.parseInt(item.trim(), 10))
    .filter((value) => Number.isInteger(value) && value >= 0 && value <= 7);
  return order.length > 0 ? order : null;
}

function parseSeed(seedText) {
  if (seedText == null || seedText === '') {
    return null;
  }
  const parsed = Number.parseInt(seedText, 10);
  if (!Number.isInteger(parsed)) {
    throw new Error(`invalid seed: ${seedText}`);
  }
  return parsed;
}

function deriveSeedFromId(idText) {
  if (typeof idText !== 'string' || idText.length === 0) {
    return null;
  }
  let digitSum = 0;
  let digitCount = 0;
  for (const char of idText) {
    if (char >= '0' && char <= '9') {
      digitSum += Number(char);
      digitCount += 1;
    }
  }
  if (digitCount === 0) {
    return null;
  }
  // Current 3.5.77 / bd_version=1.0.0.759 runtime consumes digitSum + 10.
  // Older notes said +9; fresh protocol success on 2026-05-11 matches +10.
  return digitSum + 10;
}

function buildTagYOrder(seed, baseOrder = [0, 1, 2, 3, 4, 5, 6, 7]) {
  const order = Array.from(baseOrder);
  for (let index = order.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor((seed + index) % (index + 1));
    [order[index], order[swapIndex]] = [order[swapIndex], order[index]];
  }
  return order;
}

function parseArgs(argv) {
  const options = {
    payload: defaultPayload,
    payloadFile: '',
    pageUrl: defaultPageUrl,
    pageUrlFile: '',
    detail: '',
    order: '',
    seed: '',
    runtime: DEFAULT_RUNTIME,
    chromePath: '',
    output: 'text',
    tagStateFile: '',
    skipTagInit: false,
    fixedNow: '',
    tagYMode: '',
  };

  for (const arg of argv) {
    if (arg === '--help') {
      options.help = true;
    } else if (arg === '--quiet') {
      continue;
    } else if (arg.startsWith('--payload=')) {
      options.payload = arg.slice('--payload='.length);
    } else if (arg.startsWith('--payload-file=')) {
      options.payloadFile = arg.slice('--payload-file='.length);
    } else if (arg.startsWith('--page-url=')) {
      options.pageUrl = arg.slice('--page-url='.length);
    } else if (arg.startsWith('--page-url-file=')) {
      options.pageUrlFile = arg.slice('--page-url-file='.length);
    } else if (arg.startsWith('--detail=')) {
      options.detail = arg.slice('--detail='.length);
    } else if (arg.startsWith('--seed=')) {
      options.seed = arg.slice('--seed='.length);
    } else if (arg.startsWith('--order=')) {
      options.order = arg.slice('--order='.length);
    } else if (arg.startsWith('--runtime=')) {
      options.runtime = arg.slice('--runtime='.length);
    } else if (arg.startsWith('--chrome-path=')) {
      options.chromePath = arg.slice('--chrome-path='.length);
    } else if (arg.startsWith('--output=')) {
      options.output = arg.slice('--output='.length);
    } else if (arg.startsWith('--tag-state-file=')) {
      options.tagStateFile = arg.slice('--tag-state-file='.length);
    } else if (arg === '--skip-tag-init') {
      options.skipTagInit = true;
    } else if (arg.startsWith('--fixed-now=')) {
      options.fixedNow = arg.slice('--fixed-now='.length);
    } else if (arg.startsWith('--tag-y-mode=')) {
      options.tagYMode = arg.slice('--tag-y-mode='.length);
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }

  if (!['text', 'json', 'body'].includes(options.output)) {
    throw new Error(`invalid output mode: ${options.output}`);
  }

  const runtimeAliases = {
    local: DEFAULT_RUNTIME,
    'node-vm': DEFAULT_RUNTIME,
    'node-jsdom': DEFAULT_RUNTIME,
    'local-jsdom': DEFAULT_RUNTIME,
    'browser-live': 'browser-live',
  };
  if (!(options.runtime in runtimeAliases)) {
    throw new Error(`invalid runtime: ${options.runtime}`);
  }
  options.runtimeRequested = options.runtime;
  options.runtime = runtimeAliases[options.runtime];

  return options;
}

function resolvePayloadText(options) {
  return options.payloadFile
    ? readText(options.payloadFile, 'payload file')
    : String(options.payload || '').trim();
}

function resolvePageUrl(options) {
  return options.pageUrlFile
    ? readText(options.pageUrlFile, 'page url file')
    : String(options.pageUrl || '').trim();
}

function resolveDetail(pageUrl, detailOverride) {
  if (detailOverride) {
    return detailOverride;
  }
  const verifyDataText = new URL(pageUrl).searchParams.get('verify_data');
  if (!verifyDataText) {
    throw new Error('page url is missing verify_data');
  }
  const verifyData = safeParseJson(verifyDataText, 'verify_data');
  if (!verifyData || typeof verifyData.detail !== 'string' || !verifyData.detail) {
    throw new Error('page url verify_data.detail is missing');
  }
  return verifyData.detail;
}

function resolveSeedAndOrder(options, payloadObject) {
  const explicitOrder = parseExplicitOrder(options.order);
  const explicitSeed = parseSeed(options.seed);
  const derivedSeed = deriveSeedFromId(payloadObject.id);
  const seed = explicitSeed != null ? explicitSeed : derivedSeed;

  if (!explicitOrder && seed == null) {
    throw new Error('payload.id is missing digits; pass --seed or --order');
  }

  return {
    seed,
    order: explicitOrder || buildTagYOrder(seed),
  };
}

function loadJsdom() {
  const candidates = [
    'jsdom',
    path.join(root, '..', 'node_modules', 'jsdom'),
    path.join(root, 'external', 'JSReverser-MCP', 'node_modules', 'jsdom'),
  ];

  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (error) {
      void error;
    }
  }

  throw new Error(
    'failed to load jsdom; expected it in parent node_modules or a regular install'
  );
}

function createPluginArray(names) {
  const plugins = names.map((name, index) => ({
    name,
    filename: name,
    description: name,
    index,
    0: name,
  }));
  plugins.item = (index) => plugins[index] || null;
  plugins.namedItem = (name) =>
    plugins.find((plugin) => plugin.name === name) || null;
  return plugins;
}

function createCanvasContextStub(canvas, type) {
  const common = {
    canvas,
    fillStyle: '#000000',
    strokeStyle: '#000000',
    font: '14px sans-serif',
    globalAlpha: 1,
    globalCompositeOperation: 'source-over',
    lineWidth: 1,
    textAlign: 'start',
    textBaseline: 'alphabetic',
    shadowBlur: 0,
    shadowColor: 'transparent',
    shadowOffsetX: 0,
    shadowOffsetY: 0,
    fillRect() {},
    clearRect() {},
    strokeRect() {},
    beginPath() {},
    closePath() {},
    moveTo() {},
    lineTo() {},
    bezierCurveTo() {},
    quadraticCurveTo() {},
    arc() {},
    arcTo() {},
    ellipse() {},
    rect() {},
    fill() {},
    stroke() {},
    clip() {},
    save() {},
    restore() {},
    translate() {},
    scale() {},
    rotate() {},
    transform() {},
    setTransform() {},
    resetTransform() {},
    drawImage() {},
    fillText() {},
    strokeText() {},
    measureText() {
      return { width: 10 };
    },
    createLinearGradient() {
      return { addColorStop() {} };
    },
    createRadialGradient() {
      return { addColorStop() {} };
    },
    createPattern() {
      return {};
    },
    setLineDash() {},
    getLineDash() {
      return [];
    },
    createImageData(width = 1, height = 1) {
      return {
        width,
        height,
        data: new Uint8ClampedArray(width * height * 4),
      };
    },
    getImageData(width = 1, height = 1) {
      return {
        width,
        height,
        data: new Uint8ClampedArray(width * height * 4),
      };
    },
    putImageData() {},
  };

  if (String(type).includes('webgl')) {
    return {
      ...common,
      getContextAttributes() {
        return {};
      },
      getExtension() {
        return null;
      },
      getSupportedExtensions() {
        return [];
      },
      getParameter(parameter) {
        if (parameter === 37445) {
          return 'Google Inc. (Apple)';
        }
        if (parameter === 37446) {
          return 'ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)';
        }
        return null;
      },
      getShaderPrecisionFormat() {
        return { precision: 23, rangeMin: 127, rangeMax: 127 };
      },
      createBuffer() {
        return {};
      },
      bindBuffer() {},
      bufferData() {},
      createProgram() {
        return {};
      },
      createShader() {
        return {};
      },
      shaderSource() {},
      compileShader() {},
      getShaderParameter() {
        return true;
      },
      getShaderInfoLog() {
        return '';
      },
      attachShader() {},
      linkProgram() {},
      getProgramParameter() {
        return true;
      },
      getProgramInfoLog() {
        return '';
      },
      useProgram() {},
      getAttribLocation() {
        return 0;
      },
      getUniformLocation() {
        return {};
      },
      enableVertexAttribArray() {},
      vertexAttribPointer() {},
      uniform1i() {},
      uniform2f() {},
      createTexture() {
        return {};
      },
      bindTexture() {},
      texImage2D() {},
      texParameteri() {},
      activeTexture() {},
      deleteTexture() {},
      createFramebuffer() {
        return {};
      },
      bindFramebuffer() {},
      framebufferTexture2D() {},
      checkFramebufferStatus() {
        return 0;
      },
      viewport() {},
      clearColor() {},
      clear() {},
      drawArrays() {},
      readPixels() {},
    };
  }

  return common;
}

function createMockResponseFactory() {
  return function makeResponse(definition) {
    const status = definition.status || 200;
    const headers = {
      ...(definition.headers || {}),
    };
    if (definition.contentType && !headers['content-type']) {
      headers['content-type'] = definition.contentType;
    }

    if (typeof Response === 'function') {
      return new Response(definition.body, {
        status,
        headers,
      });
    }

    const bodyBuffer = Buffer.isBuffer(definition.body)
      ? definition.body
      : Buffer.from(String(definition.body || ''), 'utf8');

    return {
      ok: status >= 200 && status < 300,
      status,
      headers: {
        get(name) {
          return headers[String(name).toLowerCase()] || null;
        },
      },
      async text() {
        return bodyBuffer.toString('utf8');
      },
      async json() {
        return JSON.parse(bodyBuffer.toString('utf8') || '{}');
      },
      async arrayBuffer() {
        return bodyBuffer.buffer.slice(
          bodyBuffer.byteOffset,
          bodyBuffer.byteOffset + bodyBuffer.byteLength
        );
      },
    };
  };
}

function createMockXMLHttpRequest(resolveRequest) {
  return class MockXMLHttpRequest {
    constructor() {
      this.readyState = 0;
      this.status = 0;
      this.response = null;
      this.responseText = '';
      this.responseType = '';
      this.timeout = 0;
      this.withCredentials = false;
      this.onreadystatechange = null;
      this.onload = null;
      this.onerror = null;
      this.onabort = null;
      this.onloadend = null;
      this._headers = {};
      this._responseHeaders = {};
      this._listeners = new Map();
    }

    open(method, url) {
      this._method = method || 'GET';
      this._url = url;
      this.readyState = 1;
      this._dispatch('readystatechange');
    }

    setRequestHeader(name, value) {
      this._headers[String(name).toLowerCase()] = value;
    }

    addEventListener(type, handler) {
      if (!this._listeners.has(type)) {
        this._listeners.set(type, new Set());
      }
      this._listeners.get(type).add(handler);
    }

    removeEventListener(type, handler) {
      this._listeners.get(type)?.delete(handler);
    }

    getAllResponseHeaders() {
      return Object.entries(this._responseHeaders)
        .map(([name, value]) => `${name}: ${value}`)
        .join('\r\n');
    }

    getResponseHeader(name) {
      return this._responseHeaders[String(name).toLowerCase()] || null;
    }

    abort() {
      this._dispatch('abort');
      this._dispatch('loadend');
    }

    send(body = null) {
      Promise.resolve(
        resolveRequest(this._url, {
          method: this._method || 'GET',
          headers: this._headers,
          body,
        })
      )
        .then((definition) => {
          const bodyBuffer = Buffer.isBuffer(definition.body)
            ? definition.body
            : Buffer.from(String(definition.body || ''), 'utf8');
          this.status = definition.status || 200;
          this.readyState = 4;
          this._responseHeaders = Object.fromEntries(
            Object.entries(definition.headers || {}).map(([name, value]) => [
              String(name).toLowerCase(),
              String(value),
            ])
          );
          if (definition.contentType && !this._responseHeaders['content-type']) {
            this._responseHeaders['content-type'] = definition.contentType;
          }

          if (this.responseType === 'arraybuffer') {
            this.response = bodyBuffer.buffer.slice(
              bodyBuffer.byteOffset,
              bodyBuffer.byteOffset + bodyBuffer.byteLength
            );
          } else if (this.responseType === 'json') {
            this.responseText = bodyBuffer.toString('utf8');
            this.response = this.responseText ? JSON.parse(this.responseText) : null;
          } else {
            this.responseText = bodyBuffer.toString('utf8');
            this.response = this.responseText;
          }

          this._dispatch('readystatechange');
          this._dispatch('load');
          this._dispatch('loadend');
        })
        .catch((error) => {
          debugLog('mock xhr error', this._url, error && error.message);
          this.status = 0;
          this.readyState = 4;
          this._dispatch('readystatechange');
          this._dispatch('error');
          this._dispatch('loadend');
        });
    }

    _dispatch(type) {
      const event = {
        type,
        target: this,
        currentTarget: this,
      };
      const handler = this[`on${type}`];
      if (typeof handler === 'function') {
        try {
          handler.call(this, event);
        } catch (error) {
          debugLog('mock xhr handler error', type, error && error.message);
        }
      }
      for (const listener of this._listeners.get(type) || []) {
        try {
          listener.call(this, event);
        } catch (error) {
          debugLog('mock xhr listener error', type, error && error.message);
        }
      }
    }
  };
}

function createMockImageClass() {
  return class MockImage {
    constructor() {
      this.complete = false;
      this.crossOrigin = '';
      this.onload = null;
      this.onerror = null;
      this.naturalWidth = 340;
      this.naturalHeight = 170;
      this.width = 340;
      this.height = 170;
      this._src = '';
    }

    get src() {
      return this._src;
    }

    set src(value) {
      this._src = String(value || '');
      this.complete = true;
      setTimeout(() => {
        if (typeof this.onload === 'function') {
          this.onload();
        }
      }, 0);
    }

    decode() {
      return Promise.resolve();
    }
  };
}

function buildMockCaptchaGetResponse(payloadObject) {
  const dragTrack =
    payloadObject &&
    Array.isArray(payloadObject['8uyk1GN']) &&
    payloadObject['8uyk1GN'].length > 0
      ? payloadObject['8uyk1GN']
      : payloadObject && Array.isArray(payloadObject.qiQezhn)
        ? payloadObject.qiQezhn
        : [];
  const tipY =
    dragTrack.length > 0 && Number.isFinite(dragTrack[0].y)
      ? Number(dragTrack[0].y)
      : 0;

  return {
    code: 200,
    message: '验证通过',
    data: {
      challenge_code: 99999,
      codifica: 'true',
      id:
        typeof payloadObject.id === 'string' && payloadObject.id
          ? payloadObject.id
          : '0000000000000000000000000000000000000000',
      mode:
        typeof payloadObject.mode === 'string' && payloadObject.mode
          ? payloadObject.mode
          : 'slide',
      version: 2,
      question: {
        tip_y: tipY,
        url1: DEFAULT_DATA_IMAGE,
        url2: DEFAULT_DATA_IMAGE,
        backup_url1: [DEFAULT_DATA_IMAGE, DEFAULT_DATA_IMAGE],
        backup_url2: [DEFAULT_DATA_IMAGE, DEFAULT_DATA_IMAGE],
        obfuscation: '',
      },
    },
  };
}

function buildMockI18nResponse() {
  return {
    code: 200,
    data: {},
  };
}

function buildMockVerifyResponse() {
  return {
    code: 200,
    message: 'ok',
    data: { success: true },
  };
}

function createLocalRequestResolver(payloadObject, wasmBytes) {
  return function resolveRequest(url, request = {}) {
    const normalized = new URL(String(url), defaultPageUrl);
    const pathname = normalized.pathname || '';

    if (/\/index\.wasm$/i.test(pathname)) {
      return {
        status: 200,
        contentType: 'application/wasm',
        body: wasmBytes,
      };
    }

    if (/bdms\.js/i.test(url) || /\/bdms\.js$/i.test(pathname)) {
      return {
        status: 200,
        contentType: 'application/javascript; charset=utf-8',
        body: 'window.bdms = { init() {} };',
      };
    }

    if (/\/captcha\/i18n$/i.test(pathname)) {
      return {
        status: 200,
        contentType: 'application/json; charset=utf-8',
        body: JSON.stringify(buildMockI18nResponse()),
      };
    }

    if (/\/captcha\/get$/i.test(pathname)) {
      return {
        status: 200,
        contentType: 'application/json; charset=utf-8',
        body: JSON.stringify(buildMockCaptchaGetResponse(payloadObject)),
      };
    }

    if (/\/captcha\/verify$/i.test(pathname)) {
      return {
        status: 200,
        contentType: 'application/json; charset=utf-8',
        body: JSON.stringify(buildMockVerifyResponse()),
      };
    }

    debugLog('mock request', request.method || 'GET', normalized.toString());
    return {
      status: 204,
      contentType: 'text/plain; charset=utf-8',
      body: '',
    };
  };
}

function defineValue(target, key, value) {
  try {
    Object.defineProperty(target, key, {
      configurable: true,
      enumerable: true,
      writable: true,
      value,
    });
  } catch (error) {
    try {
      target[key] = value;
    } catch (innerError) {
      void innerError;
    }
  }
}


function parseFixedNow(options, payloadObject) {
  const raw = options && options.fixedNow ? String(options.fixedNow) : process.env.CAPTCHA_FIXED_NOW || '';
  if (raw) {
    const parsed = Number.parseInt(raw, 10);
    if (Number.isFinite(parsed)) return parsed;
  }

  function pushFinite(candidates, value) {
    const parsed = Number.parseInt(value, 10);
    if (Number.isFinite(parsed) && parsed > 1000000000000) {
      candidates.push(parsed);
    }
  }

  const mode = String(process.env.CAPTCHA_FIXED_NOW_MODE || 'track-end').toLowerCase();
  const envCandidates = [];
  if (payloadObject && payloadObject.env) {
    pushFinite(envCandidates, payloadObject.env.d);
    pushFinite(envCandidates, payloadObject.env.ready_time);
    pushFinite(envCandidates, payloadObject.env.loading_time);
  }

  const trackCandidates = [];
  const compound = payloadObject && payloadObject.Q1FvvZeZE;
  for (const key of ['J9c', 'rHqT9pMS']) {
    const track = compound && compound[key];
    if (Array.isArray(track) && track.length) {
      pushFinite(trackCandidates, track[track.length - 1] && track[track.length - 1].time);
    }
  }

  if (mode === 'env' || mode === 'env-d') {
    return envCandidates.length ? envCandidates[0] : (trackCandidates.length ? Math.max(...trackCandidates) : null);
  }
  if (mode === 'now' || mode === 'none') {
    return null;
  }
  // Browser samples show captchaBody's header seconds are generated around
  // final data()/encrypt(), i.e. after the drag track has finished.  The old
  // env.d-first fallback placed the local fixed clock before the track and
  // made the stable header several seconds too early.
  if (trackCandidates.length) {
    const offsetRaw = process.env.CAPTCHA_FIXED_NOW_OFFSET_MS || '1000';
    const offset = Number.parseInt(offsetRaw, 10);
    return Math.max(...trackCandidates) + (Number.isFinite(offset) ? offset : 1000);
  }
  return envCandidates.length ? envCandidates[0] : null;
}

function installFixedClock(window, fixedNow) {
  if (!Number.isFinite(fixedNow)) return;
  const OriginalDate = window.Date || Date;
  function FixedDate(...args) {
    if (!(this instanceof FixedDate)) {
      return args.length === 0 ? new OriginalDate(fixedNow).toString() : OriginalDate(...args);
    }
    return args.length === 0 ? new OriginalDate(fixedNow) : new OriginalDate(...args);
  }
  Object.setPrototypeOf(FixedDate, OriginalDate);
  FixedDate.prototype = OriginalDate.prototype;
  FixedDate.now = () => fixedNow;
  FixedDate.UTC = OriginalDate.UTC.bind(OriginalDate);
  FixedDate.parse = OriginalDate.parse.bind(OriginalDate);
  defineValue(window, 'Date', FixedDate);
  const perfBase = Number(window.performance && window.performance.timeOrigin) || fixedNow;
  const perf = window.performance || {};
  try {
    Object.defineProperty(perf, 'now', {
      configurable: true,
      value: () => Math.max(0, fixedNow - perfBase),
    });
  } catch (error) {
    try { perf.now = () => Math.max(0, fixedNow - perfBase); } catch (innerError) { void innerError; }
  }
  defineValue(window, 'performance', perf);
}

function installBrowserShims(window, pageUrl, payloadObject, wasmBytes, options = {}) {
  const query = new URL(pageUrl).searchParams;
  const envText = query.get('env');
  const envObject = envText ? safeParseJson(envText, 'page url env') : {};
  const screenInfo = envObject.screen || {};
  const browserInfo = envObject.browser || {};
  const pageInfo = envObject.page || {};
  const documentInfo = envObject.document || {};

  window.console = DEBUG_ENABLED
    ? console
    : {
        log() {},
        info() {},
        warn() {},
        error() {},
        table() {},
        debug() {},
      };

  defineValue(window, 'window', window);
  defineValue(window, 'self', window);
  defineValue(window, 'globalThis', window);
  defineValue(window, 'crypto', globalThis.crypto);
  defineValue(window, 'WebAssembly', globalThis.WebAssembly);
  defineValue(window, 'TextEncoder', globalThis.TextEncoder);
  defineValue(window, 'TextDecoder', globalThis.TextDecoder);
  defineValue(window, 'Response', globalThis.Response);
  defineValue(window, 'Headers', globalThis.Headers);
  defineValue(window, 'Request', globalThis.Request);
  defineValue(window, 'Blob', globalThis.Blob);
  defineValue(window, 'File', globalThis.File);
  defineValue(window, 'ImageData', globalThis.ImageData);
  defineValue(window, 'URL', globalThis.URL);
  defineValue(window, 'URLSearchParams', globalThis.URLSearchParams);
  defineValue(window, 'performance', globalThis.performance);
  installFixedClock(window, parseFixedNow(options, payloadObject));
  defineValue(window, 'atob', (value) =>
    Buffer.from(String(value || ''), 'base64').toString('binary')
  );
  defineValue(window, 'btoa', (value) =>
    Buffer.from(String(value || ''), 'binary').toString('base64')
  );
  defineValue(window, 'requestAnimationFrame', (callback) =>
    setTimeout(() => callback(Date.now()), 16)
  );
  defineValue(window, 'cancelAnimationFrame', (handle) => clearTimeout(handle));
  defineValue(window, 'verifySDK', { log() {} });
  defineValue(window, 'gfdatav1', { canary: 0 });
  defineValue(window, 'matchMedia', () => ({
    matches: false,
    media: '',
    onchange: null,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() {
      return false;
    },
  }));
  defineValue(window, 'ResizeObserver', class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  });
  defineValue(window, 'IntersectionObserver', class IntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  });

  defineValue(window, 'innerWidth', browserInfo.w || 1200);
  defineValue(window, 'innerHeight', browserInfo.h || 816);
  defineValue(window, 'outerWidth', browserInfo.w || 1200);
  defineValue(window, 'outerHeight', browserInfo.h || 816);
  defineValue(window, 'devicePixelRatio', 1);
  defineValue(window, 'screen', {
    width: screenInfo.w || 1920,
    height: screenInfo.h || 1080,
    availWidth: screenInfo.w || 1920,
    availHeight: screenInfo.h || 1080,
    colorDepth: 24,
    pixelDepth: 24,
  });

  const pluginNames = [
    'PDF Viewer',
    'Chrome PDF Viewer',
    'Chromium PDF Viewer',
    'Microsoft Edge PDF Viewer',
    'WebKit built-in PDF',
  ];
  defineValue(window.navigator, 'userAgent', DEFAULT_USER_AGENT);
  defineValue(window.navigator, 'platform', 'MacIntel');
  defineValue(window.navigator, 'language', 'zh-CN');
  defineValue(window.navigator, 'languages', ['zh-CN']);
  defineValue(window.navigator, 'webdriver', false);
  defineValue(window.navigator, 'maxTouchPoints', 0);
  defineValue(window.navigator, 'plugins', createPluginArray(pluginNames));

  if (window.HTMLElement && window.HTMLElement.prototype) {
    window.HTMLElement.prototype.getBoundingClientRect = function getBoundingClientRect() {
      const width =
        Number(this.offsetWidth) ||
        Number(this.width) ||
        Number(browserInfo.w) ||
        Number(pageInfo.w) ||
        0;
      const height =
        Number(this.offsetHeight) || Number(this.height) || Number(pageInfo.h) || 0;
      return {
        x: 0,
        y: 0,
        top: 0,
        left: 0,
        right: width,
        bottom: height,
        width,
        height,
      };
    };
  }

  if (window.document && window.document.documentElement) {
    defineValue(window.document.documentElement, 'clientWidth', documentInfo.width || browserInfo.w || 1200);
    defineValue(window.document.documentElement, 'clientHeight', pageInfo.h || browserInfo.h || 816);
  }
  if (window.document && window.document.body) {
    defineValue(window.document.body, 'clientWidth', documentInfo.width || browserInfo.w || 1200);
    defineValue(window.document.body, 'clientHeight', pageInfo.h || browserInfo.h || 816);
  }

  const originalCreateElement = window.document.createElement.bind(window.document);
  window.document.createElement = function patchedCreateElement(tagName, options) {
    const element = originalCreateElement(tagName, options);
    const tag = String(tagName || '').toLowerCase();
    if (tag === 'canvas') {
      if (!element.width) {
        element.width = 340;
      }
      if (!element.height) {
        element.height = 170;
      }
    }
    return element;
  };

  if (window.HTMLCanvasElement && window.HTMLCanvasElement.prototype) {
    window.HTMLCanvasElement.prototype.getContext = function getContext(type) {
      const key = `__codex_ctx_${String(type || '2d')}`;
      if (!this[key]) {
        this[key] = createCanvasContextStub(this, type);
      }
      return this[key];
    };
    window.HTMLCanvasElement.prototype.toDataURL = function toDataURL() {
      return DEFAULT_DATA_IMAGE;
    };
  }

  if (window.HTMLImageElement && window.HTMLImageElement.prototype) {
    if (typeof window.HTMLImageElement.prototype.decode !== 'function') {
      window.HTMLImageElement.prototype.decode = function decode() {
        return Promise.resolve();
      };
    }
  }

  defineValue(window, 'Image', createMockImageClass());

  const resolveRequest = createLocalRequestResolver(payloadObject, wasmBytes);
  const makeResponse = createMockResponseFactory();

  window.fetch = async function fetch(input, init = {}) {
    const requestUrl = typeof input === 'string' ? input : input.url;
    return makeResponse(
      await resolveRequest(requestUrl, {
        method: init.method || 'GET',
        headers: init.headers || {},
        body: init.body,
      })
    );
  };

  defineValue(window, 'XMLHttpRequest', createMockXMLHttpRequest(resolveRequest));

  window.addEventListener('error', (event) => {
    if (!DEBUG_ENABLED && event && typeof event.preventDefault === 'function') {
      event.preventDefault();
    }
  });
  window.addEventListener('unhandledrejection', (event) => {
    if (!DEBUG_ENABLED && event && typeof event.preventDefault === 'function') {
      event.preventDefault();
    }
  });

  return envObject;
}

function buildRenderArgument(pageUrl, detailOverride) {
  const url = new URL(pageUrl);
  const verifyDataText = url.searchParams.get('verify_data');
  if (verifyDataText) {
    if (!detailOverride) {
      return verifyDataText;
    }
    const verifyData = safeParseJson(verifyDataText, 'verify_data');
    verifyData.detail = detailOverride;
    return JSON.stringify(verifyData);
  }
  const challengeCode = url.searchParams.get('challenge_code');
  return challengeCode ? Number(challengeCode) : undefined;
}

function buildCaptchaConfig(pageUrl) {
  const query = new URL(pageUrl).searchParams;
  const envText = query.get('env');
  const envObject = envText ? safeParseJson(envText, 'page url env') : {};

  return {
    info: {
      aid: query.get('aid') || '',
      appName: query.get('appName') || '',
      lang: query.get('lang') || 'zh',
      did: query.get('did') || '',
      fp: query.get('fp') || '',
      repoId: query.get('repoId') || '',
      pageId: query.get('pageId') || '',
    },
    ele: query.get('ele') || 'captcha_container',
    host: query.get('host') || '//verify.zijieapi.com/',
    baseEM: query.get('baseEM') || '',
    viewport: query.get('viewport') === 'false' ? false : true,
    hideCloseBtn: query.get('hideCloseBtn') === 'true',
    theme: query.get('theme') || 'light',
    env: envObject,
    extraConfig: query.get('extraConfig') || '{}',
    static_domain: query.get('static_domain') || '',
    successCb() {},
    errorCb() {},
    closeCb() {},
    onSuccess() {},
    onClose() {},
    onError() {},
    log() {},
  };
}

async function createLocalRuntime(options, payloadObject, captchaSource, wasmBytes) {
  const { JSDOM, VirtualConsole } = loadJsdom();
  const fixedNow = parseFixedNow(options, payloadObject);
  const originalDateNow = Date.now;
  if (Number.isFinite(fixedNow)) {
    Date.now = () => fixedNow;
  }
  const virtualConsole = new VirtualConsole();
  if (DEBUG_ENABLED && typeof virtualConsole.sendTo === 'function') {
    virtualConsole.sendTo(console, { omitJSDOMErrors: false });
  }

  const dom = new JSDOM(
    '<!doctype html><html><head></head><body><div id="captcha_container"></div></body></html>',
    {
      url: options.pageUrl,
      runScripts: 'dangerously',
      pretendToBeVisual: true,
      virtualConsole,
    }
  );

  const { window } = dom;
  installBrowserShims(window, options.pageUrl, payloadObject, wasmBytes, options);
  window.eval(captchaSource);

  if (!window.bdCaptcha || typeof window.bdCaptcha.CaptchaVerify !== 'function') {
    throw new Error('bdCaptcha.CaptchaVerify is unavailable in local runtime');
  }

  const instance = new window.bdCaptcha.CaptchaVerify(buildCaptchaConfig(options.pageUrl));

  const initResult = instance.init();
  if (initResult && typeof initResult.then === 'function') {
    await initResult;
  }

  const renderArgument = buildRenderArgument(options.pageUrl, options.detail);
  let renderError = null;
  if (typeof instance.render === 'function') {
    try {
      const renderResult = instance.render(renderArgument);
      if (renderResult && typeof renderResult.then === 'function') {
        await renderResult;
      }
    } catch (error) {
      renderError = error;
    }
  }

  if (!instance.captcha || !instance.captcha.wasm) {
    if (renderError) {
      throw renderError;
    }
    throw new Error('captcha runtime did not expose captcha.wasm');
  }

  return {
    dom,
    window,
    instance,
    captcha: instance.captcha,
    wasm: instance.captcha.wasm,
    originalDateNow,
  };
}

function buildHookKeys(captcha, wasm) {
  const keys = new Set();
  for (const target of [captcha, wasm]) {
    if (!target) {
      continue;
    }
    for (const key of Object.keys(target)) {
      keys.add(key);
    }
    const proto = Object.getPrototypeOf(target);
    if (!proto) {
      continue;
    }
    for (const key of Object.getOwnPropertyNames(proto)) {
      if (typeof target[key] === 'function') {
        keys.add(key);
      }
    }
  }
  return Array.from(keys);
}


function loadTagStateOperations(filePath) {
  if (!filePath) return null;
  const obj = safeParseJson(fs.readFileSync(path.resolve(filePath), 'utf8'), 'tag state file');
  if (Array.isArray(obj)) return obj;
  if (obj && Array.isArray(obj.operations)) return obj.operations;
  if (obj && Array.isArray(obj.logs)) {
    const out = [];
    for (const log of obj.logs) {
      const type = String(log && log.type || '');
      const sample = log && log.data && log.data.args && log.data.args.sample;
      if (!Array.isArray(sample)) continue;
      if (type.includes('.tagZInit.call')) out.push({ name: 'tagZInit', args: sample });
      else if (type.includes('.pushGetID.call')) out.push({ name: 'pushGetID', args: sample });
      else if (type.includes('.tagYInit.call')) out.push({ name: 'tagYInit', args: sample });
      else if (type.includes('.tagYEntry.call')) out.push({ name: 'tagYEntry', args: sample });
    }
    return out;
  }
  return null;
}


function buildTagStateOperationsFromMode(mode, order) {
  const text = String(mode || '').toLowerCase();
  if (!text) return null;
  const tagOrder = Array.from(order || []).map((value) => Number(value)).filter((value) => Number.isInteger(value));
  if (text === 'entries-only' || text === 'tagy-only') {
    return tagOrder.map((idx) => ({ name: 'tagYEntry', args: [idx] }));
  }
  if (text === 'post-get' || text === 'after-get') {
    const ops = [{ name: 'tagYInit', args: [] }];
    for (const idx of tagOrder) ops.push({ name: 'tagYEntry', args: [idx] });
    return ops;
  }
  if (text === 'browser-like' || text === 'browser') {
    if (tagOrder.length <= 1) return tagOrder.map((idx) => ({ name: 'tagYEntry', args: [idx] }));
    // Browser lifecycle usually does tagYInit + first tagYEntry around get, then
    // runs the remaining entries just before data()/encrypt().  In a fresh
    // local jsdom runtime replaying only the latter is closer to captured body
    // length than replaying the whole sequence twice.
    return tagOrder.slice(1).map((idx) => ({ name: 'tagYEntry', args: [idx] }));
  }
  if (text === 'browser-final' || text === 'final759') {
    // Fresh 1.0.0.759 browser logs show:
    //   tagZInit(detail) -> pushGetID(id) -> tagYInit()
    //   -> first three tagYEntry() around /captcha/get,
    // then the remaining final entries before data()/encrypt().
    // The local jsdom runtime has already performed the get-stage lifecycle
    // during render(), so replay only the final slice here.
    return tagOrder.slice(3).map((idx) => ({ name: 'tagYEntry', args: [idx] }));
  }
  if (text === 'browser-final-no4' || text === 'final759-no4') {
    // Experimental length-match mode from live 759 samples: same as
    // browser-final but drops tag_y_entry4, which is often already reflected
    // in jsdom render state.  Keep opt-in until more protocol A/B data lands.
    return tagOrder.slice(3)
      .filter((idx) => idx !== 4)
      .map((idx) => ({ name: 'tagYEntry', args: [idx] }));
  }
  return null;
}

async function runCaptchaFlow(captcha, wasm, payloadText, detail, order, tagStateOps, skipTagInit) {
  const preEncryptSnapshot = {
    source: null,
    plainJson: null,
    plainJsonLength: 0,
    detailLength: typeof detail === 'string' ? detail.length : 0,
    payloadLength: typeof payloadText === 'string' ? payloadText.length : 0,
    payloadId: null,
    order: Array.from(order || []),
    encryptArgc: null,
  };

  if (!captcha || !wasm) {
    throw new Error('local runtime is missing captcha or wasm');
  }

  captcha.wasm = captcha.wasm || wasm;

  async function invoke(name, argTypes, argValues) {
    if (typeof wasm.invoke !== 'function') {
      throw new Error(`wasm.invoke is missing while calling ${name}`);
    }
    if (
      name === 'entry' &&
      !preEncryptSnapshot.plainJson &&
      Array.isArray(argValues) &&
      typeof argValues[0] === 'string'
    ) {
      preEncryptSnapshot.source = 'invoke';
      preEncryptSnapshot.encryptArgc = Array.isArray(argTypes) ? argTypes.length : null;
      preEncryptSnapshot.plainJson = argValues[0];
      preEncryptSnapshot.plainJsonLength = argValues[0].length;
    }
    return wasm.invoke(name, null, argTypes, argValues);
  }

  const payloadObject = safeParseJson(payloadText, 'payload');
  const id = typeof payloadObject.id === 'string' ? payloadObject.id : '';
  preEncryptSnapshot.payloadId = id;

  if (wasm.loadTask && typeof wasm.loadTask.then === 'function') {
    await wasm.loadTask;
  } else if (typeof wasm.loadWithCdnRetry === 'function') {
    await wasm.loadWithCdnRetry();
  }

  if (skipTagInit) {
    preEncryptSnapshot.skipTagInit = true;
  } else if (Array.isArray(tagStateOps) && tagStateOps.length > 0) {
    preEncryptSnapshot.tagStateReplay = tagStateOps.map((op) => ({ name: op.name, args: op.args }));
    for (const op of tagStateOps) {
      const args = Array.isArray(op.args) ? op.args : [];
      if (op.name === 'tagZInit') {
        if (typeof wasm.tagZInit === 'function') await wasm.tagZInit(args[0] == null ? detail : args[0]);
        else await invoke('tag_z_init', ['string', 'number'], [args[0] == null ? detail : args[0], String(args[0] == null ? detail : args[0]).length]);
      } else if (op.name === 'pushGetID') {
        if (typeof wasm.pushGetID === 'function') await wasm.pushGetID(args[0] == null ? id : args[0]);
        else await invoke('tag_z_push_getid', ['string', 'number'], [args[0] == null ? id : args[0], String(args[0] == null ? id : args[0]).length]);
      } else if (op.name === 'tagYInit') {
        if (typeof wasm.tagYInit === 'function') await wasm.tagYInit();
        else await invoke('tag_y_init', [], []);
      } else if (op.name === 'tagYEntry') {
        const index = Number(args[0]);
        if (typeof wasm.tagYEntry === 'function') await wasm.tagYEntry(index);
        else await invoke(`tag_y_entry${index}`, [], []);
      }
    }
  } else {
    if (typeof wasm.tagZInit === 'function') {
      await wasm.tagZInit(detail);
    } else {
      await invoke('tag_z_init', ['string', 'number'], [detail, detail.length]);
    }

    if (typeof wasm.pushGetID === 'function') {
      await wasm.pushGetID(id);
    } else {
      await invoke('tag_z_push_getid', ['string', 'number'], [id, id.length]);
    }
  }

  if (process.env.CAPTCHA_DUMP_TRACK_AFTER_PUSH === '1' && typeof captcha.getTrack === 'function') {
    try {
      const trackAfterPush = await captcha.getTrack();
      process.stderr.write('[track_after_push] ' + JSON.stringify(trackAfterPush) + '\n');
    } catch (error) {
      process.stderr.write('[track_after_push_error] ' + (error && error.stack || error) + '\n');
    }
  }

  if (!skipTagInit && !(Array.isArray(tagStateOps) && tagStateOps.length > 0)) {
    if (typeof wasm.tagYInit === 'function') {
      await wasm.tagYInit();
    } else {
      await invoke('tag_y_init', [], []);
    }

    for (const index of order) {
      if (typeof wasm.tagYEntry === 'function') {
        await wasm.tagYEntry(index);
      } else {
        await invoke(`tag_y_entry${index}`, [], []);
      }
    }
  }

  let originalEncrypt = null;
  if (typeof wasm.encrypt === 'function') {
    originalEncrypt = wasm.encrypt.bind(wasm);
    wasm.encrypt = async function patchedEncrypt() {
      if (
        !preEncryptSnapshot.plainJson &&
        arguments.length > 0 &&
        typeof arguments[0] === 'string'
      ) {
        preEncryptSnapshot.source = 'encrypt';
        preEncryptSnapshot.encryptArgc = arguments.length;
        preEncryptSnapshot.plainJson = arguments[0];
        preEncryptSnapshot.plainJsonLength = arguments[0].length;
      }
      return originalEncrypt.apply(this, arguments);
    };
  }

  try {
    const captchaBody =
      typeof wasm.encrypt === 'function'
        ? await wasm.encrypt(payloadText)
        : await invoke('entry', ['string', 'number'], [payloadText, payloadText.length]);

    if (typeof captchaBody !== 'string' || captchaBody.length < 1000) {
      throw new Error(
        'generated captchaBody is unexpectedly short: ' +
          JSON.stringify({ length: typeof captchaBody === 'string' ? captchaBody.length : null })
      );
    }

    return {
      captchaBody,
      hookKeys: buildHookKeys(captcha, wasm),
      preEncryptSnapshot,
    };
  } finally {
    if (originalEncrypt) {
      wasm.encrypt = originalEncrypt;
    }
  }
}

function buildPlainJsonMetadata(preEncryptSnapshot, payloadText) {
  if (
    !preEncryptSnapshot ||
    typeof preEncryptSnapshot.plainJson !== 'string' ||
    preEncryptSnapshot.plainJson.length === 0
  ) {
    return preEncryptSnapshot || null;
  }
  return {
    ...preEncryptSnapshot,
    plainJsonMatchesPayload: preEncryptSnapshot.plainJson === payloadText,
    plainJsonSha256: crypto
      .createHash('sha256')
      .update(preEncryptSnapshot.plainJson, 'utf8')
      .digest('hex'),
  };
}

function printHelp() {
  process.stdout.write(
    [
      'Usage:',
      '  node probe/run_vm_wasm_node.js [--payload=JSON] [--payload-file=file]',
      '                                  [--page-url=url] [--page-url-file=file]',
      '                                  [--detail=text] [--seed=int] [--order=0,1,2,...]',
      '                                  [--runtime=local-jsdom|node-vm|browser-live]',
      '                                  [--output=text|json|body] [--tag-state-file=file] [--skip-tag-init]',
      '',
      'Notes:',
      '  - The default runtime is fully local: `local-jsdom`.',
      '  - `--runtime=browser-live` and `--chrome-path=...` are kept only for',
      '    CLI compatibility and no longer switch away from the local runtime.',
      '',
      'Output:',
      '  tag_y_seed=<seed>',
      '  tag_y_order=<comma-separated order>',
      '  <captchaBody>',
      '',
    ].join('\n')
  );
}

function printResult(options, seed, order, payloadText, runtimeResult) {
  const captchaBody = runtimeResult.captchaBody;
  const preEncryptSnapshot = buildPlainJsonMetadata(
    runtimeResult.preEncryptSnapshot,
    payloadText
  );

  if (options.output === 'body') {
    process.stdout.write(`${captchaBody}\n`);
    return;
  }

  if (options.output === 'json') {
    process.stdout.write(
      `${JSON.stringify({
        runtime_mode: options.runtime,
        runtime_requested: options.runtimeRequested,
        tag_y_seed: seed,
        tag_y_order: order,
        captchaBody,
        hookKeys: runtimeResult.hookKeys,
        preEncryptSnapshot,
      })}\n`
    );
    return;
  }

  process.stdout.write(`tag_y_seed=${seed == null ? '' : String(seed)}\n`);
  process.stdout.write(`tag_y_order=${order.join(',')}\n`);
  process.stdout.write(`${captchaBody}\n`);
}

function formatError(error) {
  if (!error) {
    return 'unknown error';
  }
  if (typeof error.stack === 'string' && error.stack) {
    return error.stack;
  }
  if (typeof error.message === 'string' && error.message) {
    return error.message;
  }
  return String(error);
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    printHelp();
    return;
  }

  const payloadText = resolvePayloadText(options);
  const payloadObject = safeParseJson(payloadText, 'payload');
  options.pageUrl = resolvePageUrl(options);

  const detail = resolveDetail(options.pageUrl, options.detail);
  const { seed, order } = resolveSeedAndOrder(options, payloadObject);
  let tagStateOps = loadTagStateOperations(options.tagStateFile);
  if (!tagStateOps && options.tagYMode) {
    tagStateOps = buildTagStateOperationsFromMode(options.tagYMode, order);
  }
  const captchaSource = fs.readFileSync(captchaPath, 'utf8');
  const wasmBytes = fs.readFileSync(wasmPath);

  debugLog('runtimeRequested', options.runtimeRequested, 'runtimeUsed', options.runtime);
  debugLog('pageUrl', options.pageUrl);
  debugLog('detailLength', detail.length);
  debugLog('seed', seed, 'order', order);
  if (options.chromePath) {
    debugLog('chromePathIgnored', options.chromePath);
  }

  if (options.runtime === 'browser-live') {
    const runtimeResult = await runLiveBrowserEncrypt(options, payloadText, detail, order, tagStateOps);
    printResult(options, seed, order, payloadText, runtimeResult);
    return;
  }

  let runtime = null;
  try {
    runtime = await createLocalRuntime(options, payloadObject, captchaSource, wasmBytes);
    const runtimeResult = await runCaptchaFlow(
      runtime.captcha,
      runtime.wasm,
      payloadText,
      detail,
      order,
      tagStateOps,
      options.skipTagInit
    );
    printResult(options, seed, order, payloadText, runtimeResult);
  } finally {
    if (runtime && runtime.originalDateNow) {
      Date.now = runtime.originalDateNow;
    }
    if (runtime && runtime.window && typeof runtime.window.close === 'function') {
      runtime.window.close();
    }
  }
}

main().catch((error) => {
  process.stderr.write(`${formatError(error)}\n`);
  process.exitCode = 1;
});
