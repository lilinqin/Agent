# 工具系统

> 适用场景：技术架构设计、工具平台建设、技术选型

---

## 工具的本质

很多人问：工具到底是什么？

**工具是 Agent 与外部世界交互的桥梁。** LLM 本身的知识是静态的、训练截止的，但现实世界是动态的——天气会变、股票会涨、数据库会更新。工具让 Agent 能够获取实时信息、执行具体操作。

我们把工具定位为：**Agent 能力的延伸。** LLM 负责"脑"，工具负责"手"。

---

## 工具定义三要素

```json
{
  "name": "search",
  "description": "当你需要查询实时信息时使用",  // 触发场景
  "parameters": { ... }
}
```

这个设计的精髓在于：**工具描述的重点是"什么时候用"，而不是"怎么用"。**

我们踩过的坑：之前有工程师写工具描述喜欢写"调用 SerpApi，传入 query 参数返回搜索结果"——这是给开发者看的，不是给 LLM 看的。

正确写法是："当你需要查询实时信息、新闻或网络数据时使用此工具"

---

## Function Calling vs. ReAct

我们在技术选型时的核心考量：

### Function Calling（原生支持）

模型直接输出结构化的函数调用参数：
```json
{"name": "search", "arguments": {"query": "北京天气"}}
```

- **优点**：格式可靠，无需解析
- **缺点**：需要模型支持 function calling

### ReAct 格式

模型输出自然语言格式：
```
Action: search[北京天气]
```

- **优点**：通用性强，任何模型都能用
- **缺点**：需要正则解析，可能格式错误

**我们目前的实践**：生产环境优先选 Function Calling，原生支持更稳定。ReAct 作为降级方案，支持那些不支持 Function Calling 的模型。

> 参考论文：[Toolformer](https://arxiv.org/abs/2302.04761)

---

## 工具注册与管理

### ToolRegistry 模式

本质是一个"工具字典"：

```python
class ToolRegistry:
    def register(self, tool):
        self._tools[tool.name] = tool
    
    def execute(self, name, params):
        return self._tools[name].run(params)
```

### 动态工具添加

我们支持 Agent 运行时动态添加工具，实现"遇山开路"的能力。

---

## 工具类型

| 类型 | 示例 | 场景 |
|------|------|------|
| **查询型** | 搜索、数据库查询、API 调用 | 获取外部信息 |
| **执行型** | 发送邮件、执行代码、调用 API | 执行具体操作 |
| **计算型** | 计算器、公式解析 | 精确计算 |
| **检索型** | 向量搜索、知识库查询 | RAG 场景 |

---

## 工程实践

### 1. 描述即提示词

```python
# ❌ 错误：描述实现细节
"调用 SerpApi，传入 query 参数返回搜索结果"

# ✅ 正确：描述使用场景
"当你需要查询实时信息、新闻或网络数据时使用此工具"
```

### 2. 错误处理

```python
def execute(self, params):
    try:
        return self._tool.run(params)
    except ToolExecutionError as e:
        return f"工具执行失败: {str(e)}"
    except RateLimitError:
        return "调用频率受限，请稍后重试"
```

### 3. 重试机制

- 临时错误：自动重试 2-3 次
- 永久错误：返回明确错误信息，让 LLM 决定下一步

### 4. 工具状态缓存

避免重复调用，缓存相同参数的请求结果。

---

## MCP 协议

Anthropic 提出的标准化工具调用协议，本质是解决"工具定义的碎片化"问题：

- **标准化**：统一工具定义和调用格式
- **可发现**：工具可以动态注册和发现
- **安全**：明确的权限边界

**我们的判断**：MCP 是未来方向，但目前生态还在建设中。

---

## 技术战略思考

我们为什么要投入建设工具平台？

**第一，工具是 Agent 产生实际价值的关键。** 只有接入真实业务系统——CRM、ERP、数据仓库——Agent 才能帮我们解决真实问题。

**第二，工具质量决定 Agent 能力上限。** LLM 再强，工具不好用，Agent 也不行。

**第三，工具生态是竞争壁垒。** 谁拥有更丰富的工具生态，谁的 Agent 就更有竞争力。

---

## 参考

- [Toolformer](https://arxiv.org/abs/2302.04761)
- MCP 规范：https://modelcontextprotocol.io

---

## 一句话总结

工具是 Agent 能力的延伸。设计工具的核心是**清晰的场景触发描述** + **健壮的执行容错** + **标准化的注册管理**。
