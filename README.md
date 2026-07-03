# DeepAnalyze + stataskills

这是一个已接入 `stataskills` 统计工具库的 DeepAnalyze 复现发布包。它保留 DeepAnalyze 的 OpenAI-compatible API 和 WebUI v2，并在 DeepAnalyze 的 API prompt 中注入统计工具使用说明，使模型在执行统计分析、回归、时间序列、生存分析、A/B 测试和因果推断时优先调用 `stataskills.run_tool(...)`。

本仓库适合用于展示和复现：“DeepAnalyze 如何调用 StatABench 统计函数完成真实数据分析报告”。

## 来源与致谢

本发布包基于以下开源项目整理：

- DeepAnalyze: https://github.com/ruc-datalab/DeepAnalyze
- StatABench: https://github.com/youxin01/StatABench

本仓库中的 `DeepAnalyze/` 主要来自 RUC-DataLab 的 DeepAnalyze 项目，保留其原始 UI、API 结构和文档；本仓库中的 `stataskills_demo/stataskills/` 来自 StatABench 中统计函数的整理和 Python 包化。

许可证说明：

- DeepAnalyze 原项目为 MIT License，见 `THIRD_PARTY_LICENSES/DeepAnalyze-MIT-LICENSE`。
- StatABench 原项目为 GPLv3，见 `THIRD_PARTY_LICENSES/StatABench-GPLv3-LICENSE`。
- 本发布包根目录 `LICENSE` 使用 GPLv3。继续开源发布时请保留本 README、NOTICE 和第三方许可证文件。

## 目录结构

```text
.
├── DeepAnalyze/                  # 已接入 stataskills prompt 的 DeepAnalyze API + WebUI v2
├── stataskills_demo/             # stataskills 包、复现任务、数据、报告和验证脚本
│   ├── stataskills/              # 统计工具 Python 包
│   ├── examples/                 # 三个 DeepAnalyze demo prompt 和 runner
│   ├── data/datasets83/          # 三个 demo 和全工具验证所需 CSV 数据
│   ├── artifacts/reports/        # DeepAnalyze 原始报告、raw 输出和 validation
│   ├── scripts/                  # 全工具调用验证脚本
│   └── docs/                     # 中文集成说明
├── THIRD_PARTY_LICENSES/
├── NOTICE.md
└── LICENSE
```

## 改了 DeepAnalyze 哪里

只改了 DeepAnalyze API prompt 注入逻辑：

```text
DeepAnalyze/API/utils.py
```

新增了 `STATASKILLS_PROMPT`，并在 `prepare_vllm_messages()` 中追加到用户任务后面。这样 DeepAnalyze 在生成 Python 代码时会知道当前环境安装了：

```python
from stataskills import run_tool, list_tools, tool_help
```

WebUI v2 代码没有被改动，保留 DeepAnalyze 原始 `demo/chat_v2` 实现。

## 快速开始

以下命令假设你已经有可运行 DeepAnalyze 的 Python 环境。模型权重不包含在本发布包中，需要自行下载 DeepAnalyze-8B。

### 1. 安装 Python 依赖

```bash
cd DeepAnalyze
pip install -r requirements.txt

cd ../stataskills_demo
pip install -e ".[full]"
```

`[full]` 会安装时间序列、生存分析、贝叶斯和因果推断相关依赖。

### 2. 启动 DeepAnalyze-8B 的 vLLM 服务

```bash
vllm serve RUC-DataLab/DeepAnalyze-8B \
  --host 0.0.0.0 \
  --port 8000
```

如果模型已经下载到本地，也可以把 `RUC-DataLab/DeepAnalyze-8B` 换成本地模型路径。

### 3. 启动 DeepAnalyze API

```bash
cd DeepAnalyze/API
python start_server.py
```

默认服务：

- API: `http://localhost:8200`
- 文件服务: `http://localhost:8100`
- vLLM: `http://localhost:8000/v1`

健康检查：

```bash
curl http://localhost:8200/health
curl http://localhost:8000/v1/models
```

### 4. 运行三个复现任务

另开一个终端：

```bash
cd stataskills_demo
python examples/run_deepanalyze_demo_tasks.py --task all
```

也可以只跑一个任务：

```bash
python examples/run_deepanalyze_demo_tasks.py --task hospital
python examples/run_deepanalyze_demo_tasks.py --task growth
python examples/run_deepanalyze_demo_tasks.py --task policy
```

输出位置：

```text
stataskills_demo/artifacts/reports/hospital.md
stataskills_demo/artifacts/reports/growth.md
stataskills_demo/artifacts/reports/policy.md
```

这些 `*.md` 是 DeepAnalyze 原始最终回答抽取结果，没有人工润色或脚本改写。对应的完整 raw 输出和验证文件也保存在同一目录：

```text
*_raw.md
*_response.json
*_validation.json
summary.json
```

## 三个 demo 覆盖内容

- `hospital`: 医院运营与患者结局分析，覆盖描述统计、缺失值、异常值、相关性、多元回归、ADF、STL、Kaplan-Meier、log-rank、Cox。
- `growth`: 产品增长与转化实验，覆盖 A/B 测试、列联检验、bootstrap、样本量估计和相关分析。
- `policy`: 政策效果与因果评估，覆盖 DID、placebo DID、PSM ATT 和 synthetic control。

## 验证 stataskills 全部函数

```bash
cd stataskills_demo
python scripts/verify_stataskills_all_tools.py
```

预期结果中应看到全部公开工具可调用。当前开发环境中的结果是：

```text
Total cases: 55
Passed: 55
Failed: 0
Public tools covered by primary PASS: 38 / 38
```

## WebUI v2

WebUI v2 来自 DeepAnalyze 原项目，位于：

```text
DeepAnalyze/demo/chat_v2/
```

本发布包没有修改 UI 源码。前端首次运行前需要安装 Node 依赖：

```bash
cd DeepAnalyze/demo/chat_v2/frontend
npm ci
npm run build
```

运行 WebUI：

```bash
cd DeepAnalyze/demo/chat_v2
bash start.sh
```

默认地址：

- 前端: `http://localhost:4000`
- 后端: `http://localhost:8200`

## 注意事项

- 不要把模型权重、`.env`、API keys、`workspace/`、`logs/`、`node_modules/` 上传到 GitHub。
- GitHub 上传前建议运行：

```bash
find . -name '__pycache__' -o -name '*.pyc' -o -name '.env' -o -name 'node_modules' -o -name '.next'
```

- 如果你 fork 或再发布，请在 README 中继续保留 DeepAnalyze 和 StatABench 的来源与许可证说明。
