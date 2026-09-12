# Macro Graph 中文手工研究说明书

这份说明书回答两个问题：网页上的数字是什么意思，以及不依赖程序时，应该打开哪些网站、点击哪里、记录什么，才能完成一次可复核的宏观与科技产业研究。网页问号和手册底部的可搜索词典共用 `config/glossary.zh-CN.json`，定义会同步更新。

本系统用于研究，不用于自动交易。任何解释都必须分成四层：

- **FACT（事实）**：官方发布值或可复核的市场价格，例如“2Y 收益率上升 12bp”。
- **OBSERVATION（观察）**：由事实计算出的现象，例如“SOXX 五日跑赢 QQQ 2.3 个百分点”。
- **INFERENCE（推断）**：证据支持但不能直接观测的解释，例如“市场上调了利率路径预期”。
- **HYPOTHESIS（假设）**：尚待验证的可能原因，例如“半导体走强可能来自 AI 硬件轮动”。

如果证据链断裂，结论写成 `UNKNOWN / INSUFFICIENT EVIDENCE`。

## 一、先看懂本地网页

打开 [Macro Graph 本地网页](http://127.0.0.1:8765/)，先按以下顺序读，不要从单只股票开始。

### 1. CURRENT REGIME

这是规则匹配出的“市场环境标签”，不是事实，也不是预测。

- `Hawkish / Tightening`：通常表示实际利率、美元或短端收益率走强，风险资产承压。
- `Risk-on / Risk-off`：是跨资产共振标签，不等于所有股票都同涨或同跌。
- `AI Hardware Boom / Hardware Rotation`：表示硬件相对强，不自动证明有新增资金流入。
- `CONFIDENCE` 是规则证据完整度；`SCORE` 是命中规则的分数，不是上涨概率。

### 2. DATA QUALITY

- `COMPLETE`：本次快照要求的序列齐全，不代表数据绝对准确，也不代表解释正确。
- `DEGRADED`：有缺失或过期序列，报告应降低结论强度。
- `缺失`：该序列没有可用值。
- `过期`：最后观测日明显早于本次研究日期。宏观月度数据天然比日行情慢，不一定是故障。

### 3. 利率与美元卡片

- `FED_FUNDS`、`US02Y`、`US10Y`、`REAL_YIELD_10Y`、`BREAKEVEN_10Y` 的大数字是百分比收益率。
- 卡片上的 `bp` 是相对前一观测日的变化。`1bp = 0.01 个百分点`；例如 4.20% 到 4.32% 是 `+12bp`。
- `DXY` 大数字是指数点位；其变化是百分比，不是 bp。
- 先看 2Y，再看 10Y 和实际利率，最后看 DXY。2Y 更接近政策路径，10Y 还包含长期增长、通胀与期限溢价。

### 4. 资产表现表

- `1D / 5D / 20D`：分别是 1、5、20 个交易时段的价格回报。
- `量比`：当日成交量除以过去 20 日平均量。大于 `1.5×` 才算明显放量的初步信号；小于 `0.7×` 偏低。它不能单独证明资金流入。
- `20D Z`：当前价格距离过去 20 日均值多少个标准差。绝对值大于 2 表示相对极端，不代表必然反转，也不是概率。
- 绿色只表示上涨，红色只表示下跌，不代表好坏。

### 5. 科技公司 / Nasdaq 相对强弱

网页中的 `pp` 是百分点：

`公司 5D 回报 - Nasdaq 5D 回报`

例如 NVDA 为 `+3.0pp`，表示五日内跑赢基准 3 个百分点。它能证明相对强弱，不能证明“资金从软件流入 NVDA”。确认轮动至少还要观察行业广度、成交量、ETF 表现和基本面催化。

### 6. 20 日相关性

- `+1`：同步同向；`-1`：同步反向；`0`：没有稳定线性关系。
- 经验上 `|r| ≥ 0.6` 可称较强，`0.3–0.6` 为中等，低于 `0.3` 偏弱；但样本只有 20 日时很容易漂移。
- 相关性只用于检查理论关系最近是否有效，不能替代因果解释。

### 7. 因果图谱

- 圆点是变量、资产、产业环节或公司；箭头表示有明确语义的传导关系。
- `positive / negative` 表示其他条件不变时的理论方向。
- `strength` 表示关系的经济重要度；`confidence` 表示我们对这条关系的研究把握。两者都不是统计显著性。
- 点击节点后先读 `reason`，再回到当日市场数据验证。图谱表达的是“待验证的机制”，不是当天已经发生的事实。

### 8. 每日报告

报告中四类标签必须分开读。最有价值的不是某个结论，而是从 FACT 到 HYPOTHESIS 是否有完整证据链。看到没有事实支撑的 HYPOTHESIS，不应据此交易。

## 二、每天 20 分钟的手工流程

### 第 1 步：确认今天有什么事件

1. 打开 [BLS 发布日历](https://www.bls.gov/schedule/)。
2. 点击当前月份，记录 CPI、PPI、Employment Situation 的日期与美国东部时间。
3. 打开 [BEA News](https://www.bea.gov/news)，记录 Personal Income and Outlays（PCE）和 GDP。
4. 打开 [FOMC 日历](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)，查看今天是否有 Statement、Press Conference 或 Minutes。
5. 把“预定事件”与“已经公布的事实”分开。日历只说明时间，不说明结果。

### 第 2 步：读 Fed 预期

1. 打开 [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)。
2. 在会议选择处点击最近一次 FOMC 会议。
3. 记录各目标利率区间的当前概率，并与 `1 Day / 1 Week / 1 Month` 前比较。
4. 再点击下一次和下下次会议，观察市场预期的是一次变化还是整条路径变化。
5. 写成事实：“期货隐含概率发生变化”；不要写成“Fed 一定会降息”。FedWatch 来自 30-Day Fed Funds futures，是市场定价，不是 Fed 承诺。

### 第 3 步：读美国国债曲线

1. 打开 [美国财政部 Daily Treasury Par Yield Curve Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve)。
2. 在 `Select Time Period` 选择当前年份和月份，点击 `Apply`。
3. 找到最新日期，记录 `2-year`、`5-year`、`10-year`、`30-year`。
4. 与上一行相减并乘以 100，得到日变化 bp。
5. 计算 `10Y - 2Y` 和 `30Y - 10Y`。前者反映曲线倒挂/陡峭程度，后者帮助观察长端期限溢价压力。
6. 点击页面的 `Download CSV` 可保存原始表。

判断顺序：

- 2Y 上升明显、10Y 变化较小：优先检查 Fed 路径是否变鹰。
- 10Y 和 30Y 上升更明显：检查长期通胀、增长、国债供给与期限溢价。
- 不能只凭曲线变化断言原因；还要对照当天数据和事件。

### 第 4 步：拆分实际利率与通胀预期

1. 打开 [财政部 Daily Treasury Real Yield Curve Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_real_yield_curve)。
2. 选择当前时间段并点击 `Apply`，记录 `10-year` 实际收益率。
3. 打开 [FRED 10-Year Breakeven Inflation Rate](https://fred.stlouisfed.org/series/T10YIE)，点击图表上方时间范围，观察当天与近一个月变化。
4. 用近似恒等式检查：`10Y nominal yield ≈ 10Y real yield + 10Y breakeven`。

解读：名义 10Y 上升若主要来自 real yield，通常对黄金和高久期科技估值压力更直接；若主要来自 breakeven，上游能源和通胀交易的解释权重更高。

### 第 5 步：读美元、黄金、原油与股票

使用 [TradingView Supercharts](https://www.tradingview.com/chart/) 做统一价格检查：

1. 点击左上角品种名称，搜索并确认交易所/数据源。
2. 建议依次查看 `DXY`、`XAUUSD` 或 COMEX `GC`、NYMEX `CL`（WTI）、ICE Brent、`SPY`、`QQQ`、`SOXX` 或 `SMH`、`IGV`。
3. 时间周期先选 `1D`，范围依次看 5 日、1 月、6 月。日内事件研究再切 5 分钟或 15 分钟。
4. 点击顶部 `Compare or Add symbol`，加入对照资产。比较不同价格尺度时，在刻度菜单使用 `Indexed to 100`。
5. 研究相对强弱时，在品种搜索框直接输入比值，例如 `NASDAQ:SOXX / NASDAQ:QQQ`、`NASDAQ:MU / NASDAQ:QQQ`。比值上涨才表示前者跑赢后者。
6. 打开 Volume 指标，只记录“放量/缩量”的观察，不把上涨成交量直接命名为净流入。

期货权威合约资料可交叉检查：[COMEX Gold](https://www.cmegroup.com/markets/metals/precious/gold.quotes.html)、[NYMEX WTI](https://www.cmegroup.com/markets/energy/crude-oil.html)。连续合约可能受换月影响，现货、近月期货和 ETF 的回报不能无条件混用。

### 第 6 步：写一句跨资产结论

使用固定句式：

> FACT：2Y、10Y、实际利率、DXY、Gold、QQQ、SOXX 各自如何变化。  
> OBSERVATION：哪一段曲线、哪个行业、哪一个比值最突出。  
> INFERENCE：市场可能在重定价政策、增长、通胀还是期限溢价。  
> HYPOTHESIS：可能的催化是什么，下一项需要什么证据验证。

只有价格同涨同跌而没有事件、成交量、仓位或基本面证据时，写：“无法确认资金流向，只观察到价格相对强弱。”

## 三、CPI 日怎么手工读

1. 公布前记录市场一致预期。共识不是官方数据，必须注明第三方来源和截取时间。
2. 8:30 ET 后打开 [BLS CPI Summary](https://www.bls.gov/news.release/cpi.nr0.htm)。先读 headline CPI 的月环比和同比，再读 all items less food and energy（Core CPI）。
3. 点击 `Table A`，确认能源、食品、核心的贡献方向。
4. 在 [CPI Table of Contents](https://www.bls.gov/news.release/cpi.toc.htm) 点击 `Table 6` 看一个月变化细项，点击 `Table 7` 看 12 个月细项。
5. 记录 `actual - consensus`，不要只比较同比，因为基数效应可能掩盖当前动量。
6. 立刻检查 2Y、10Y、10Y real yield、DXY、Gold、QQQ 的 5 分钟和当日反应。
7. 30–60 分钟后再次检查：第一次跳动可能是算法交易，第二阶段才可能反映细项消化。

典型假设链：

`Core CPI 正向意外 → 预期 Fed 路径上移 → 2Y / real yield 上升 → DXY 偏强 → 黄金与高久期估值承压`

这是待验证路径。如果 CPI 超预期而 2Y 不升，先检查是否有修正、细项偏软、仓位过度或其他同时发生的事件。

## 四、NFP 日怎么手工读

1. 8:30 ET 后打开 [BLS Employment Situation](https://www.bls.gov/news.release/empsit.toc.htm)。
2. 先读 Summary，但不要停在新增非农人数。
3. 点击 `Table B-1`：记录 total nonfarm payrolls，检查前两个月修正和就业集中在哪些行业。
4. 点击 `Table A-1`：记录 unemployment rate、labor force participation rate 和 employment-population ratio。
5. 点击 `Table B-3`：记录 average hourly earnings 的月环比、同比以及 average weekly hours。
6. 对照 2Y、FedWatch、DXY、Gold、QQQ。工资比单一就业人数更可能影响通胀与 Fed 预期。

不要把“就业人数强”直接等同于“经济全面强”。若新增就业集中、工时下降、失业率上升或历史值大幅下修，结论必须降级。

## 五、FOMC 日怎么手工读

1. 打开 [FOMC Calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)，找到本次会议。
2. 决议发布后依次点击 `Statement`、`Implementation Note`。有星号的会议再点击 `Projection Materials`，查看 SEP 和 dot plot。
3. 新闻发布会开始后点击 `Press Conference`，区分主席对当前决定、未来路径和风险管理的表述。
4. 逐句比较上次 Statement：通胀、就业、经济活动、风险平衡的措辞是新增、删除还是强化。
5. 对照 FedWatch 的整条会议路径以及 2Y，而不是只看当次加息/降息。
6. 对照 10Y 与 30Y：若短端下降而长端上升，可能是曲线陡峭化，不应简单写成“全面鸽派”。
7. Minutes 通常晚于会议发布，只能用于复盘内部讨论，不能冒充当日新信息。

## 六、黄金的手工证据链

按以下顺序检查：

1. Gold 当日及五日回报。
2. 10Y real yield 是否反向变化。
3. DXY 是否反向变化。
4. [CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) 中 COMEX Gold 的 Managed Money 或 Non-Commercial 净仓位是否处于极端。
5. [World Gold Council Goldhub](https://www.gold.org/goldhub/data) 的央行储备、ETF 和需求数据是否支持中期需求。
6. 是否存在地缘、信用或储备多元化事件。

“Real Yield 上升但 Gold 也上涨”不代表理论失效。可能是地缘风险、央行购买、美元走弱、通胀尾部风险或仓位挤压压过了持有成本效应。必须找到额外证据，否则写 UNKNOWN。

## 七、原油的手工证据链

每周三美国东部时间 10:30 左右：

1. 打开 [EIA Weekly Petroleum Status Report](https://www.eia.gov/petroleum/supply/weekly/)。
2. 先点 `Highlights` 看概览。
3. 点击 `Table 1` 看美国石油供需平衡。
4. 点击 `Table 4` 看 crude oil 和主要成品油库存。
5. 点击 `Table 7` 看进出口，点击 `Table 9` 看周度供应估计。
6. 对照 WTI 与 Brent 当时反应，再检查近月和次近月价差。

判断：

- 需求冲击：油价、工业/运输需求和风险资产可能同向；通胀上行但增长也偏强。
- 供给冲击：油价上升、增长预期下修、通胀预期上升；对股票更可能形成滞胀压力。
- `Backwardation` 加深常提示近端供应更紧；`Contango` 加深常提示现货宽松或库存压力，但还要考虑利息和储存成本。

## 八、AI 科技产业的手工研究

### 1. 先找原始文件

1. 打开 [SEC Search Filings](https://www.sec.gov/search-filings)。
2. 在 `Company Search` 输入 ticker，例如 `NVDA`，点击 `Submit`。
3. 用 filing type 筛选 `10-Q`、`10-K` 和 `8-K`。
4. 财报日优先打开 8-K 附件中的 earnings release（常见为 Exhibit 99.1），再读 10-Q/10-K；演示材料只能作为补充。
5. 在文档内搜索 `data center`、`AI`、`capex`、`inventory`、`customer`、`guidance`、`gross margin`。

同时打开公司官网的 `Investor Relations → Quarterly Results / Financial Results`。SEC 文件负责可核验披露，IR 演示负责管理层叙事，两者不要混为一类证据。

### 2. 各公司至少记录什么

- `NVDA`：Data Center revenue、供给约束、毛利率、产品代际、客户集中与出口限制。
- `AMD`：Data Center、Instinct GPU 指引、CPU/GPU 组合及毛利率。
- `AVGO`：AI revenue、custom accelerator、networking、客户集中与下一年度指引。
- `MRVL`：data center revenue、custom silicon、electro-optics/interconnect 节奏。
- `MU`：Data Center、HBM 收入/产能、DRAM/NAND 定价、库存与 capex。
- `SNDK`：NAND、enterprise SSD、供需/定价、库存周期；不要把它简单当作 DRAM/HBM proxy。
- `INTC`：DCAI、Foundry、制程节点、capex、外部客户与补贴。
- `LITE`：Cloud & Networking、800G/1.6T、激光器/光器件产能、客户认证与订单能见度。
- `GLW`：Optical Communications、Enterprise/Carrier、数据中心连接、玻璃业务的周期差异。
- `MSFT / GOOGL / META / AMZN / ORCL`：capex、云增速、AI capacity、折旧、供需约束和 monetization。

### 3. 把事件写成可验证路径

例如 Broadcom 上调 AI revenue guidance：

1. FACT：原始 earnings release 中的新指引及原指引。
2. OBSERVATION：AVGO、MRVL、SOXX、LITE、GLW 相对 QQQ 的 1D/5D 表现和量比。
3. INFERENCE：市场上调 custom ASIC / networking 需求预期。
4. HYPOTHESIS：需求可能外溢到 optical；等待 LITE/GLW 的订单、指引或 hyperscaler capex 证明。

同一条链中，上游公司股价上涨不能自动证明下游订单已经增长。

## 九、每周仓位与“资金流”检查

1. 周五打开 [CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)。
2. 选择 Futures Only 或 Futures and Options Combined，并固定一种口径长期使用。
3. 查找 USD Index、Gold、Crude Oil、Treasury 对应合约，记录投机多头、空头和净头寸的周变化。
4. 注意 COT 反映的是周二持仓，通常周五发布，有时间滞后。
5. ETF flow 只有在来源、申赎口径和日期一致时才记录；成交量、价格和 AUM 变化都不能单独替代净申赎。

资金轮动的最低证据组合：

- 相对价格：例如 `SOXX / QQQ` 上升。
- 广度：多数半导体成分而非一只权重股走强。
- 成交量：相关行业有持续而非单日异常的放量。
- 仓位/申赎：COT 或可靠 ETF flow 支持。
- 催化：财报、capex、政策或宏观数据能解释时间点。

缺少后三项时，只写“相对强弱”，不要写“资金从 A 流入 B”。

## 十、可复制的每日记录模板

```text
日期（纽约）：

FACT
- FedWatch 最近两次会议概率：
- US02Y / 日变动bp：
- US10Y / 日变动bp：
- 10Y real yield / 日变动bp：
- 10Y breakeven / 日变动bp：
- DXY / Gold / WTI / Brent：
- SPY / QQQ / SOXX / IGV：
- NVDA / AVGO / MU / SNDK / INTC / LITE / GLW：

OBSERVATION
- 曲线：2s10s、10s30s：
- 最强/最弱资产：
- 关键相对强弱比值：
- 成交量是否支持：

INFERENCE
- 市场主要重定价：政策 / 通胀 / 增长 / 期限溢价 / AI基本面 / UNKNOWN
- 支持证据：
- 反证：

HYPOTHESIS
- 候选解释：
- 下一步需要验证的官方数据或公司披露：

结论
- 今天市场在交易什么：
- 不能确认什么：
```

## 十一、建议收藏的网站

- [Federal Reserve Monetary Policy](https://www.federalreserve.gov/monetarypolicy.htm)：FOMC 声明、SEP、新闻发布会和 Minutes。
- [CME FedWatch](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)：期货隐含的 Fed 路径概率。
- [U.S. Treasury Interest Rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates)：名义与实际收益率曲线。
- [FRED](https://fred.stlouisfed.org/)：利率、breakeven 与宏观时间序列。
- [BLS News Releases](https://www.bls.gov/bls/newsrels.htm)：CPI、PPI、就业和工资。
- [BEA News](https://www.bea.gov/news)：PCE、GDP 和个人收入支出。
- [EIA Petroleum](https://www.eia.gov/petroleum/weekly/)：原油库存、供需和进出口。
- [CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)：期货持仓代理。
- [SEC EDGAR](https://www.sec.gov/search-filings)：公司法定披露。
- [TradingView Supercharts](https://www.tradingview.com/chart/)：统一查看价格、成交量、比较线和比值图；属于第三方行情界面，需核对数据源与延迟。

## 十二、最后的纪律

每天只回答三件事：什么是已知事实；哪些市场反应可以观察；哪些解释仍只是推断或假设。宏观机制提供候选路径，真实价格用于验证，公司披露用于确认产业链，三者不能相互替代。
