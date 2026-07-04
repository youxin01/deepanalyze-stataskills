# DeepAnalyze WebUI v2 启动说明

这个目录的 WebUI 由两个服务组成：

- 后端 FastAPI：默认 `http://localhost:8200`
- 前端 Next.js：默认 `http://localhost:4000`

模型服务不是由 `start.sh` 启动的。后端默认会去连接 OpenAI-compatible 模型接口 `http://localhost:8000/v1`，所以本地模型或 API 服务需要单独准备。

## 1. 启动模型服务

如果你使用本地 DeepAnalyze-8B，可以先在一个终端启动 vLLM：

```bash
CUDA_VISIBLE_DEVICES=2 /data1/zyx/conda/envs/qlora1/bin/python -m vllm.entrypoints.openai.api_server \
  --model /nfsdata/zyx/models/RUC-DataLab/DeepAnalyze-8B \
  --served-model-name DeepAnalyze-8B \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.85 \
  --trust-remote-code
```

如果 `8000` 端口上已经有可用模型服务，可以跳过这一步。可以用下面命令确认：

```bash
curl http://localhost:8000/v1/models
```

## 2. 启动 WebUI

在另一个终端中运行：

```bash
cd /nfsdata/zyx/statabench/skills-create/deepanalyze-stataskills-release/DeepAnalyze/demo/chat_v2
conda activate deepanalyze_app
bash start.sh
```

建议先激活 `deepanalyze_app`。如果忘记激活，`start.sh` 也会尝试从当前 Python 或 `conda run -n deepanalyze_app` 自动找到能运行后端的 Python。

`start.sh` 会做这些事情：

- 停掉旧的 WebUI 后端和前端进程
- 启动后端 `backend.py`，默认监听 `8200`
- 启动前端 Next.js，默认监听 `4000`
- 等待两个服务都真正可访问后才打印成功
- 脚本退出后，前端和后端会继续在后台运行
- 如果当前机器的 Next.js native SWC 不能运行，会自动改用 WASM SWC fallback

成功后会看到类似输出：

```text
Backend is ready: http://127.0.0.1:8200/docs
Frontend is ready: http://127.0.0.1:4000
All services started successfully.
```

## 3. 远程服务器访问

如果你通过 Cursor 或 SSH 连接远程服务器，需要把这两个端口都转发到本地：

- `4000`：浏览器打开的前端页面
- `8200`：前端页面调用的后端 API

本地浏览器访问：

```text
http://localhost:4000
```

进入页面后，如果使用本地 vLLM，模型配置一般选择：

- Provider：`Local`
- Model：`DeepAnalyze-8B`
- API Base：默认指向后端配置里的 `http://localhost:8000/v1`

## 4. 停止服务

```bash
cd /nfsdata/zyx/statabench/skills-create/deepanalyze-stataskills-release/DeepAnalyze/demo/chat_v2
bash stop.sh
```

这只会停止 WebUI 的前端和后端，不会停止你单独启动的 vLLM 模型服务。

## 5. 常用检查

```bash
curl -I http://localhost:8200/docs
curl -I http://localhost:4000
```

日志位置：

```text
DeepAnalyze/demo/chat_v2/logs/backend.log
DeepAnalyze/demo/chat_v2/logs/frontend.log
```

说明：WebUI v2 的 workspace 文件预览和下载接口由后端 `8200` 提供，不需要单独转发 `8100`。`8100` 只是旧配置中保留的文件服务端口字段，在当前 WebUI 启动脚本中不会启动独立服务。
