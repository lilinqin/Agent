# 自建智能体框架

> 适用场景：技术面试、框架设计、深度理解

---

## 为什么要自建框架

| 现有框架问题 | 自建优势 |
|-------------|----------|
| 过度抽象，学习曲线陡峭 | 完全可控，理解每个组件 |
| API 变更频繁，维护成本高 | 无依赖，想改就改 |
| 黑盒实现，缺乏深度定制 | 按需定制，无多余功能 |
| 依赖包重，体积大 | 轻量级，按需引入 |

**本质**：从"使用者"到"构建者"的能力跃迁。亲手实现每个组件，才能真正理解 Agent 工作原理。

---

## HelloAgents 设计理念

### 1. 轻量级 + 教学友好

- 核心代码按章节区分，可读性强
- 极简依赖（仅 OpenAI SDK + 基础库）
- 问题定位直接到框架代码，无需在复杂依赖中排查

### 2. 基于标准 API

- 基于 OpenAI API 标准构建
- 兼容任何兼容 OpenAI 接口的服务商
- 掌握后迁移到其他框架成本低

### 3. 渐进式学习路径

- 每个版本可 pip 安装
- 每步升级自然渐进，无概念跳跃

### 4. 统一工具抽象

- 除核心 Agent 类，**一切皆为 Tools**
- Memory、RAG、RL、MCP 都统一为"工具"
- 消除不必要的抽象层

---

## 核心组件实现

### HelloAgentsLLM：多提供商支持

**自动检测机制**（优先级从高到低）：

1. **特定环境变量**：`MODELSCOPE_API_KEY` → modelscope，`OPENAI_API_KEY` → openai
2. **base_url 解析**：域名匹配 + 端口匹配（`:11434` → Ollama，`:8000` → VLLM）
3. **API Key 格式**：如 `ms-` 前缀 → ModelScope
4. **默认配置**

```python
# 零配置自动检测
llm = HelloAgentsLLM()  # 自动检测 provider
```

**本地模型支持**：

- **VLLM**：PagedAttention 高吞吐，通过 `--host 0.0.0.0 --port 8000` 启动
- **Ollama**：一条命令 `ollama run llama3`，默认 `:11434`

---

### Message 类

```python
class Message(BaseModel):
    content: str
    role: Literal["user", "assistant", "system", "tool"]
    timestamp: datetime = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:  # 转为 OpenAI API 格式
```

**设计要点**：
- `role` 用 `Literal` 严格限制四种类型
- `timestamp` + `metadata` 预留扩展空间
- `to_dict()` 体现"对内丰富，对外兼容"

---

### Config 类

```python
class Config(BaseModel):
    default_model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_history_length: int = 100
    
    @classmethod
    def from_env(cls) -> "Config":  # 从环境变量读取
```

---

### Agent 抽象基类

```python
class Agent(ABC):
    @abstractmethod
    def run(self, input_text: str) -> str:
        pass
    
    def add_message(self, message: Message):
        self._history.append(message)
    
    def get_history(self) -> list[Message]:
        return self._history.copy()
```

**设计要点**：
- 抽象类无法直接实例化
- `@abstractmethod` 强制子类实现 `run` 方法
- 统一的历史管理接口

---

## Agent 范式框架化

### SimpleAgent

- 基础对话 Agent
- 支持可选工具调用（`enable_tool_calling`）
- 流式响应（`stream_run`）
- 动态工具管理（`add_tool`, `remove_tool`）

**工具调用格式**：
```
[TOOL_CALL:tool_name:parameters]
```

### ReActAgent

- 继承 Agent 基类
- 提示词模板：Thought → Action → Observation
- `max_steps` 防止无限循环
- `ToolRegistry` 统一管理工具

**核心循环**：
```
while current_step < max_steps:
    1. 构建提示词（含工具描述 + 执行历史）
    2. 调用 LLM
    3. 解析输出（Thought + Action）
    4. 检查 Finish 条件
    5. 执行工具，收集 Observation
```

### ReflectionAgent

- 执行 → 反思 → 优化 → 重复
- 用额外调用换准确率
- 适合"不容有错"场景

---

## 面试高频问题

**Q: 为什么要自建框架而不是直接用 LangChain？**
> "学习原理时手写能深度理解。生产环境用成熟框架省维护成本。关键看场景——简单任务用框架，深度定制或教学场景自建更合适。"

**Q: HelloAgents 的"万物皆工具"设计好处？**
> "消除不必要的抽象层。Memory、RAG、工具在调用方式上统一，开发者只需理解'Agent 调用工具'这一核心逻辑，降低学习成本。"

**Q: 如何实现多服务商切换？**
> "三层自动检测：1. 特定环境变量（MODELSCOPE_API_KEY）；2. base_url 解析（域名/端口）；3. API Key 格式。检测到后用对应默认值配置客户端。"

**Q: Agent 基类为什么用抽象类？**
> "强制所有具体 Agent 实现必须实现 run 方法，保证统一接口。同时提供历史管理等通用实现，子类直接继承。"

---

## 一句话总结

自建框架的本质是**把"如何使用 Agent"的共性逻辑抽象成可复用组件**，同时保持代码轻量、可读、可定制。HelloAgents 通过"一切皆工具"的统一抽象和渐进式学习路径，让开发者在构建过程中真正理解 Agent 的每个核心组件。
