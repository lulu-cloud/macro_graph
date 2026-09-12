const state = { snapshot: null, graph: null, report: null, manual: null, glossary: null, graphFilter: "all", transform: { x: 0, y: 0, k: 1 } };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const fmt = (value, suffix = "") => value == null ? "—" : `${value >= 0 ? "+" : ""}${Number(value).toFixed(2)}${suffix}`;
const cls = (value) => value == null || value === 0 ? "neutral" : value > 0 ? "positive" : "negative";
const safe = (value) => String(value ?? "").replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
const regimeLabels = {HAWKISH_TIGHTENING:"鹰派 / 金融条件收紧",DOVISH_EASING:"鸽派 / 金融条件宽松",RISK_ON:"风险偏好上升",RISK_OFF:"风险规避",INFLATION_SHOCK:"通胀冲击",GROWTH_SCARE:"增长担忧",AI_HARDWARE_BOOM:"AI 硬件景气",AI_SOFTWARE_ROTATION:"AI 软件轮动",HARDWARE_ROTATION:"硬件轮动",MIXED:"混合 / 无明确主线"};
const metricLabels = {FED_FUNDS:"联邦基金有效利率",US02Y:"2 年期美债",US10Y:"10 年期美债",US30Y:"30 年期美债",US_BREAKEVEN_10Y:"10 年期通胀预期",US_REAL_YIELD_10Y:"10 年期实际利率",DXY:"美元指数"};
const nodeTypeLabels = {policy:"政策变量",rate:"利率",macro_indicator:"宏观指标",fx:"外汇",commodity:"商品",industry_demand:"产业需求",industry_segment:"产业环节",public_equity:"上市公司",private_company:"非上市公司",market:"市场"};
const relationshipLabels = {policy_path_repricing:"政策路径重定价",opportunity_cost_pressure:"持有机会成本压力",dollar_translation_pressure:"美元计价压力",energy_input_pressure:"能源成本传导",infrastructure_demand:"基础设施需求",custom_compute_demand:"定制计算需求",memory_content_demand:"内存需求",cluster_connectivity_demand:"集群连接需求",ecosystem_compute_demand:"生态算力需求",accelerator_revenue_exposure:"加速器收入敞口",custom_accelerator_exposure:"定制加速器敞口",memory_revenue_exposure:"存储收入敞口",optical_component_exposure:"光器件业务敞口",optical_fiber_exposure:"光纤连接业务敞口"};
const nodeLabels = {FED_FUNDS_EFFECTIVE:"联邦基金有效利率",US02Y:"2 年期美债收益率",US10Y:"10 年期美债收益率",US_REAL_YIELD_10Y:"10 年期实际收益率",US_BREAKEVEN_10Y:"10 年期盈亏平衡通胀率",DXY:"美元指数",GOLD:"COMEX 黄金期货代理",BRENT:"布伦特原油期货代理",SP500:"标普 500 指数",NASDAQ:"纳斯达克综合指数",SOXX:"半导体 ETF",FED_HAWKISHNESS:"美联储鹰派程度",INFLATION:"通胀",AI_CAPEX:"AI 资本开支",GPU_DEMAND:"GPU 需求",ASIC_DEMAND:"ASIC 需求",HBM_DRAM_DEMAND:"HBM 与 DRAM 需求",DATACENTER_OPTICAL_DEMAND:"数据中心光通信需求",OPENAI:"OpenAI（未上市）",NVDA:"英伟达",AVGO:"博通",MU:"美光科技",SNDK:"Sandisk",INTC:"英特尔",LITE:"Lumentum",GLW:"康宁"};
const confidenceLabels = {high:"高",medium:"中等",low:"低"};

async function loadData() {
  const [snapshot, graph, report, manual, glossary] = await Promise.all([
    fetch("/api/snapshot").then(r => r.json()),
    fetch("/api/graph").then(r => r.json()),
    fetch("/api/report").then(r => r.json()),
    fetch("/api/manual").then(r => r.json()),
    fetch("/api/glossary").then(r => r.json()),
  ]);
  if (snapshot.error) {
    $("#overview-view").hidden = true;
    $("#empty-state").hidden = false;
    return;
  }
  state.snapshot = snapshot; state.graph = graph; state.report = report; state.manual = manual; state.glossary = glossary;
  renderOverview(); renderGraph(); renderReport(); renderManual(); renderGlossary(); annotatePage();
}

function renderOverview() {
  const s = state.snapshot;
  $("#asof").textContent = `${s.run.run_date} · ${s.run.status}`;
  const regime = s.regimes[0];
  $("#regime-name").textContent = `${regimeLabels[regime.regime] || regime.regime.replaceAll("_", " ")}（${regime.regime.replaceAll("_", " ")}）`;
  $("#regime-reason").textContent = regime.reason || regime.counterevidence || "由透明规则和当日证据共同判定。";
  $("#regime-score").textContent = `置信度 ${confidenceLabels[regime.confidence] || regime.confidence} · 规则得分 ${regime.score}`;
  const providers = Object.values(s.run.provider_status).filter(item => item.status === "OK");
  $("#quality-state").textContent = s.quality.missing_series.length ? "数据降级（DEGRADED）" : "数据齐全（COMPLETE）";
  $("#provider-count").textContent = providers.length ? `${providers.length} 个数据源` : "使用缓存数据";
  $("#quality-note").textContent = `${s.quality.missing_series.length} 缺失 · ${s.quality.stale_series.length} 过期`;

  const rates = {FED_FUNDS: s.macro.fed_rate, ...s.rates, DXY: s.fx.DXY};
  $("#macro-cards").innerHTML = Object.entries(rates).map(([name, item]) => {
    const value = name === "DXY" ? item.price : item.value_pct;
    const delta = name === "DXY" ? item.daily_return : item.daily_change_bp;
    const unit = name === "DXY" ? "%" : " bp";
    const suffix = name === "DXY" ? "" : "%";
    return `<article class="metric-card"><div class="label">${safe(metricLabels[name] || name)} <span>${safe(name)}</span></div><div class="value">${value == null ? "—" : Number(value).toFixed(name === "DXY" ? 2 : 3)}${suffix}</div><div class="delta ${cls(delta)}">${fmt(delta, unit)}</div><div class="date">${safe(item.as_of_session || item.as_of_observation || "暂无数据")}</div></article>`;
  }).join("");

  const groups = [
    ["DXY", s.fx.DXY, "外汇"], ["GOLD", s.commodities.GOLD, "商品"], ["BRENT", s.commodities.BRENT, "商品"],
    ...Object.entries(s.equity).map(([k,v]) => [k,v,"指数 / ETF"]),
    ...Object.entries(s.companies).map(([k,v]) => [k,v,"AI 产业链"]),
  ];
  $("#market-table").innerHTML = groups.map(([name,item,type]) => `<tr><td><span class="asset-name">${safe(name)}</span><span class="asset-class">${type}</span></td><td>${item.price == null ? "—" : Number(item.price).toFixed(2)}</td><td class="${cls(item.daily_return)}">${fmt(item.daily_return,"%")}</td><td class="${cls(item.weekly_return)}">${fmt(item.weekly_return,"%")}</td><td class="${cls(item.monthly_return)}">${fmt(item.monthly_return,"%")}</td><td>${item.volume_ratio_20d == null ? "—" : Number(item.volume_ratio_20d).toFixed(2)+"×"}</td><td class="${cls(item.zscore)}">${fmt(item.zscore)}</td></tr>`).join("");

  const relative = Object.entries(s.companies).map(([name,item]) => [name,item.relative_strength?.["5d"]]).filter(([,v]) => v != null).sort((a,b) => b[1]-a[1]);
  const max = Math.max(1, ...relative.map(([,v]) => Math.abs(v)));
  $("#relative-bars").innerHTML = relative.map(([name,value]) => `<div class="bar-row"><strong>${name}</strong><div class="bar-track"><div class="bar-fill ${value < 0 ? "negative" : ""}" style="width:${Math.abs(value)/max*50}%"></div></div><span class="bar-value ${cls(value)}">${fmt(value," pp")}</span></div>`).join("");

  $("#correlation-list").innerHTML = Object.entries(s.correlations).map(([name, windows]) => {
    const item = windows["20d"];
    return `<div class="correlation-row"><span>${safe(name.replace("_vs_", " 对 ").replaceAll("_", " "))}</span><span class="corr-value ${cls(item.value)}">${item.value == null ? "无数据" : Number(item.value).toFixed(2)}</span></div>`;
  }).join("");
}

function renderReport() {
  if (!state.report || state.report.error) return;
  $("#report-date").textContent = `${state.report.date} 日报`;
  const lines = state.report.content.split("\n");
  $("#report-content").innerHTML = lines.map(line => {
    if (line.startsWith("# ")) return `<h1>${safe(line.slice(2))}</h1>`;
    if (line.startsWith("## ")) return `<h2>${safe(line.slice(3))}</h2>`;
    if (line.startsWith("- [")) {
      const end = line.indexOf("]"); const tag = line.slice(3,end); const body = line.slice(end+1).trim();
      const kind = tag.split(",")[0].toLowerCase();
      return `<p class="evidence ${safe(kind)}"><span class="tag">${safe(tag)}</span>${inlineCode(body)}</p>`;
    }
    if (line.trim().startsWith("`")) return `<p>${inlineCode(line.trim())}</p>`;
    if (line.trim().startsWith("_As of")) return `<p class="caveat">${safe(line.replaceAll("_", ""))}</p>`;
    return line.trim() ? `<p>${inlineCode(line.trim())}</p>` : "";
  }).join("");
}

function inlineCode(text) {
  return safe(text).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function richText(text) {
  let output = safe(text);
  output = output.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>');
  output = output.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  output = output.replace(/`([^`]+)`/g, "<code>$1</code>");
  return output;
}

function renderManual() {
  if (!state.manual || state.manual.error) {
    $("#manual-content").innerHTML = "<p>中文说明书暂不可用。</p>";
    return;
  }
  const lines = state.manual.content.split("\n");
  let html = "", listType = null, inCode = false, codeLines = [];
  const closeList = () => { if (listType) { html += `</${listType}>`; listType = null; } };
  lines.forEach(line => {
    if (line.startsWith("```")) {
      closeList();
      if (inCode) { html += `<pre><code>${safe(codeLines.join("\n"))}</code></pre>`; codeLines = []; }
      inCode = !inCode;
      return;
    }
    if (inCode) { codeLines.push(line); return; }
    const numbered = line.match(/^\d+\.\s+(.*)$/);
    const bullet = line.match(/^-\s+(.*)$/);
    if (numbered || bullet) {
      const wanted = numbered ? "ol" : "ul";
      if (listType !== wanted) { closeList(); html += `<${wanted}>`; listType = wanted; }
      html += `<li>${richText((numbered || bullet)[1])}</li>`;
      return;
    }
    closeList();
    if (line.startsWith("# ")) return;
    if (line.startsWith("## ")) {
      const title = line.slice(3);
      const anchor = title.includes("先看懂") ? "manual-page-guide" : title.includes("每天 20") ? "manual-daily-flow" : title.includes("CPI 日") ? "manual-event-days" : title.includes("AI 科技") ? "manual-ai-research" : "";
      html += `<h2${anchor ? ` id="${anchor}"` : ""}>${richText(title)}</h2>`;
    } else if (line.startsWith("### ")) html += `<h3>${richText(line.slice(4))}</h3>`;
    else if (line.startsWith("> ")) html += `<blockquote>${richText(line.slice(2))}</blockquote>`;
    else if (line.trim()) html += `<p>${richText(line.trim())}</p>`;
  });
  closeList();
  $("#manual-content").innerHTML = html;
}

function renderGlossary(query = "") {
  const terms = state.glossary?.terms || [];
  const needle = query.trim().toLocaleLowerCase("zh-CN");
  const filtered = terms.filter(term => !needle || [term.key, term.label, term.category, term.plain, term.why, ...(term.aliases || [])].join(" ").toLocaleLowerCase("zh-CN").includes(needle));
  $("#glossary-count").textContent = `显示 ${filtered.length} / ${terms.length} 个术语`;
  $("#glossary-list").innerHTML = filtered.length ? filtered.map(term => `<article class="glossary-card"><div><span class="glossary-category">${safe(term.category)}</span><h3>${safe(term.label)}<small>${safe(term.key)}</small></h3></div><p>${safe(term.plain)}</p><dl><div><dt>为什么重要</dt><dd>${safe(term.why)}</dd></div><div><dt>常见误区</dt><dd>${safe(term.pitfall)}</dd></div></dl>${term.learn_more ? `<a href="${safe(term.learn_more)}" target="_blank" rel="noopener noreferrer">查看权威资料 ↗</a>` : ""}</article>`).join("") : '<p class="glossary-empty">没有匹配项。可以尝试英文缩写或中文含义。</p>';
}

function glossaryLookup() {
  const lookup = new Map();
  (state.glossary?.terms || []).forEach(term => {
    [term.key, term.label, ...(term.aliases || [])].forEach(alias => lookup.set(String(alias).toLocaleLowerCase("en-US"), term));
  });
  return lookup;
}

function annotatePage() {
  [$(".topbar"), ...$$('.view')].forEach(root => annotateTerms(root));
}

function annotateTerms(root) {
  if (!root || !state.glossary?.terms?.length) return;
  const lookup = glossaryLookup();
  const aliases = [...lookup.keys()].sort((a, b) => b.length - a.length).map(value => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const matcher = new RegExp(`(^|[^A-Za-z0-9_])(${aliases.join("|")})(?![A-Za-z0-9_])`, "gi");
  const seen = new Set();
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent || !node.nodeValue.trim() || parent.closest("a, button, pre, .term-label, .manual-glossary")) return NodeFilter.FILTER_REJECT;
      matcher.lastIndex = 0;
      return matcher.test(node.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    }
  });
  const nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
  nodes.forEach(node => {
    const text = node.nodeValue; const fragment = document.createDocumentFragment(); let cursor = 0; let changed = false; matcher.lastIndex = 0; let match;
    while ((match = matcher.exec(text))) {
      const leading = match[1]; const visible = match[2]; const term = lookup.get(visible.toLocaleLowerCase("en-US"));
      const termStart = match.index + leading.length;
      const seenKey = visible.toLocaleLowerCase("en-US");
      if (!term || seen.has(seenKey)) continue;
      fragment.append(document.createTextNode(text.slice(cursor, termStart)));
      const wrapper = document.createElement("span"); wrapper.className = "term-label"; wrapper.append(document.createTextNode(visible));
      const button = document.createElement("button"); button.type = "button"; button.className = "term-help"; button.dataset.term = term.key; button.setAttribute("aria-label", `解释 ${term.label}`); button.setAttribute("aria-expanded", "false"); button.title = `${term.label}：${term.plain}`; button.textContent = "?";
      wrapper.append(button); fragment.append(wrapper); cursor = termStart + visible.length; seen.add(seenKey); changed = true;
    }
    if (changed) { fragment.append(document.createTextNode(text.slice(cursor))); node.replaceWith(fragment); }
  });
}

function openTermPopover(button) {
  const term = (state.glossary?.terms || []).find(item => item.key === button.dataset.term); if (!term) return;
  const popover = $("#term-popover"); $$('.term-help[aria-expanded="true"]').forEach(item => item.setAttribute("aria-expanded", "false")); button.setAttribute("aria-expanded", "true");
  popover.innerHTML = `<button type="button" class="term-close" aria-label="关闭术语解释">×</button><span class="glossary-category">${safe(term.category)}</span><h2>${safe(term.label)}</h2><p>${safe(term.plain)}</p><dl><div><dt>为什么重要</dt><dd>${safe(term.why)}</dd></div><div><dt>常见误区</dt><dd>${safe(term.pitfall)}</dd></div></dl>${term.learn_more ? `<a href="${safe(term.learn_more)}" target="_blank" rel="noopener noreferrer">查看权威资料 ↗</a>` : ""}`;
  popover.hidden = false;
  const rect = button.getBoundingClientRect(); const gap = 9; const width = Math.min(370, window.innerWidth - 24); popover.style.width = `${width}px`;
  const left = Math.max(12, Math.min(window.innerWidth - width - 12, rect.left - 18)); popover.style.left = `${left}px`;
  const height = popover.getBoundingClientRect().height; const below = rect.bottom + gap; popover.style.top = `${below + height <= window.innerHeight - 10 ? below : Math.max(10, rect.top - height - gap)}px`;
  popover.querySelector(".term-close").addEventListener("click", closeTermPopover);
}

function closeTermPopover() {
  $("#term-popover").hidden = true; $$('.term-help[aria-expanded="true"]').forEach(item => item.setAttribute("aria-expanded", "false"));
}

function renderGraph() {
  if (!state.graph || state.graph.error) return;
  const svg = $("#graph-canvas");
  const width = Math.max(650, svg.clientWidth || 900), height = Math.max(520, svg.clientHeight || 650);
  const allNodes = state.graph.nodes || []; const allEdges = state.graph.links || state.graph.edges || [];
  const category = n => ["policy","rate","macro_indicator","fx","commodity"].includes(n.node_type) ? "macro" : ["industry_demand","industry_segment","public_equity","private_company"].includes(n.node_type) ? "industry" : "market";
  const connected = new Set(allEdges.flatMap(edge => [edge.source, edge.target]));
  const nodes = allNodes.filter(n => connected.has(n.id) && (state.graphFilter === "all" || category(n) === state.graphFilter));
  const allowed = new Set(nodes.map(n => n.id)); const edges = allEdges.filter(e => allowed.has(e.source) && allowed.has(e.target));
  const palette = {macro:"#42d7c7",industry:"#f1b85b",market:"#78aee8"};
  const positions = layout(nodes, edges, width, height);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.innerHTML = `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#547078"/></marker></defs><g id="graph-stage"></g>`;
  const stage = svg.querySelector("#graph-stage");
  edges.forEach(edge => {
    const a=positions[edge.source], b=positions[edge.target]; if(!a||!b)return;
    const line=document.createElementNS("http://www.w3.org/2000/svg","line");
    line.setAttribute("x1",a.x);line.setAttribute("y1",a.y);line.setAttribute("x2",b.x);line.setAttribute("y2",b.y);line.setAttribute("marker-end","url(#arrow)");line.setAttribute("class",`graph-edge ${edge.direction||""}`);line.setAttribute("stroke-width",String(1+Number(edge.strength||.5)*1.8));stage.appendChild(line);
  });
  nodes.forEach(node => {
    const p=positions[node.id], g=document.createElementNS("http://www.w3.org/2000/svg","g");
    g.setAttribute("class","graph-node");g.setAttribute("transform",`translate(${p.x} ${p.y})`);g.setAttribute("role","button");g.setAttribute("tabindex","0");g.setAttribute("aria-label",`${node.label||node.id}，${node.node_type}`);g.dataset.id=node.id;
    const circle=document.createElementNS("http://www.w3.org/2000/svg","circle");circle.setAttribute("r", category(node)==="industry"?"9":"8");circle.setAttribute("fill",palette[category(node)]);circle.setAttribute("fill-opacity",".22");circle.setAttribute("stroke",palette[category(node)]);
    const label=document.createElementNS("http://www.w3.org/2000/svg","text");label.setAttribute("x","14");label.setAttribute("y","4");label.textContent=node.id;
    g.append(circle,label);g.addEventListener("click",event=>{event.stopPropagation();showNode(node,edges,allNodes);});g.addEventListener("keydown",event=>{if(event.key==="Enter"||event.key===" ")showNode(node,edges,allNodes);});stage.appendChild(g);
  });
  showNodePicker(nodes, edges, allNodes);
  applyTransform(); wireGraphPanZoom(svg);
}

function showNodePicker(nodes, edges, allNodes) {
  $("#node-detail").innerHTML = `<span class="kicker">当前节点</span><h2>选择一个节点</h2><p>查看它如何影响下游资产与公司。</p><div class="node-picker">${nodes.map(node => `<button class="node-pick" data-node-pick="${safe(node.id)}">${safe(node.id)}</button>`).join("")}</div>`;
  $$("[data-node-pick]").forEach(button => button.addEventListener("click", () => {
    const node = allNodes.find(item => item.id === button.dataset.nodePick);
    if (node) showNode(node, edges, allNodes);
  }));
  annotateTerms($("#node-detail"));
}

function layout(nodes, edges, width, height) {
  const indegree = Object.fromEntries(nodes.map(node => [node.id, 0]));
  const outgoing = Object.fromEntries(nodes.map(node => [node.id, []]));
  edges.forEach(edge => { if (edge.source in outgoing && edge.target in indegree) { outgoing[edge.source].push(edge.target); indegree[edge.target]++; } });
  const levels = Object.fromEntries(nodes.map(node => [node.id, 0]));
  const queue = nodes.filter(node => indegree[node.id] === 0).map(node => node.id);
  while (queue.length) { const id = queue.shift(); outgoing[id].forEach(target => { levels[target] = Math.max(levels[target], levels[id] + 1); indegree[target]--; if (indegree[target] === 0) queue.push(target); }); }
  const maxLevel = Math.max(1, ...Object.values(levels)); const groups = {};
  nodes.forEach(node => (groups[levels[node.id]] ||= []).push(node));
  const pos = {};
  Object.entries(groups).forEach(([level, group]) => {
    group.sort((a,b) => a.id.localeCompare(b.id));
    const x = 52 + Number(level) * ((width - 160) / maxLevel);
    group.forEach((node, index) => { pos[node.id] = {x, y: 52 + (index + 1) * ((height - 104) / (group.length + 1))}; });
  });
  return pos;
}

function showNode(node, edges, nodes) {
  $$(".graph-node").forEach(n=>n.classList.toggle("selected",n.dataset.id===node.id));
  const related=edges.filter(e=>e.source===node.id||e.target===node.id); const map=Object.fromEntries(nodes.map(n=>[n.id,n]));
  $("#node-detail").innerHTML=`<span class="kicker">当前节点</span><h2>${safe(nodeLabels[node.id] || node.label || node.id)}</h2><p>${safe(node.id)}</p><div class="node-meta">类型：${safe(nodeTypeLabels[node.node_type] || node.node_type)}<br>直接关系：${related.length}</div>${related.length?related.map(e=>{const outgoing=e.source===node.id,target=outgoing?e.target:e.source;return `<div class="edge-detail"><strong>${outgoing?"→":"←"} ${safe(nodeLabels[target] || map[target]?.label || target)}</strong><span>${safe(relationshipLabels[e.relationship] || e.relationship)} · ${e.direction === "positive" ? "正向" : e.direction === "negative" ? "负向" : safe(e.direction)} · 置信度 ${e.confidence}</span><span>${safe(e.reason_zh || e.reason)}</span></div>`}).join(""):"<p>当前没有已配置的直接关系。</p>"}<button class="node-pick" id="choose-another">选择其他节点</button>`;
  $("#choose-another").addEventListener("click", () => {
    const connected = new Set(edges.flatMap(edge => [edge.source, edge.target]));
    showNodePicker(nodes.filter(item => connected.has(item.id)), edges, nodes);
  });
  annotateTerms($("#node-detail"));
}

function wireGraphPanZoom(svg) {
  let dragging=false,last={x:0,y:0};
  svg.onwheel=e=>{e.preventDefault();state.transform.k=Math.max(.45,Math.min(2.4,state.transform.k*(e.deltaY>0?.9:1.1)));applyTransform();};
  svg.onpointerdown=e=>{dragging=true;last={x:e.clientX,y:e.clientY};svg.setPointerCapture(e.pointerId);};
  svg.onpointermove=e=>{if(!dragging)return;state.transform.x+=e.clientX-last.x;state.transform.y+=e.clientY-last.y;last={x:e.clientX,y:e.clientY};applyTransform();};
  svg.onpointerup=()=>dragging=false;
}
function applyTransform(){const stage=$("#graph-stage");if(stage)stage.setAttribute("transform",`translate(${state.transform.x} ${state.transform.y}) scale(${state.transform.k})`);}

$$('.tab').forEach(tab=>tab.addEventListener('click',()=>{$$('.tab').forEach(t=>t.classList.remove('active'));tab.classList.add('active');$$('.view').forEach(v=>v.classList.remove('active'));$(`#${tab.dataset.view}-view`).classList.add('active');window.scrollTo({top:0,behavior:'instant'});if(tab.dataset.view==='graph')requestAnimationFrame(renderGraph);}));
$$('.filter').forEach(button=>button.addEventListener('click',()=>{$$('.filter').forEach(b=>b.classList.remove('active'));button.classList.add('active');state.graphFilter=button.dataset.filter;state.transform={x:0,y:0,k:1};renderGraph();}));
$("#glossary-search").addEventListener("input", event => renderGlossary(event.target.value));
document.addEventListener("click", event => { const button = event.target.closest?.(".term-help"); if (button) { event.stopPropagation(); openTermPopover(button); } else if (!event.target.closest?.("#term-popover")) closeTermPopover(); });
document.addEventListener("keydown", event => { if (event.key === "Escape") closeTermPopover(); });
window.addEventListener("scroll", closeTermPopover, {passive:true});
window.addEventListener("resize",()=>{if($("#graph-view").classList.contains("active"))renderGraph();});
loadData().catch(error=>{$("#asof").textContent="加载失败";console.error(error);});
