# 安全沙箱

> 适用场景：技术面试、安全架构、生产部署

---

## 为什么需要沙箱

Agent 的核心特性是**自主行动**——它可以调用工具、执行代码、访问数据。但自主性意味着风险：

- 执行恶意代码
- 过度调用 API 导致经济损失
- 泄露敏感数据
- 行为越界无法恢复

**沙箱的核心目标**：在保证 Agent 能力的前提下，限制其破坏范围。

---

## 沙箱多层防御

### 1. 权限控制

```python
class ToolPermissions:
    def __init__(self):
        # 白名单：只有明确允许的工具才能调用
        self.allowed_tools = {"search", "calculator", "fetch_data"}
        self.denied_tools = {"exec", "delete_db", "send_email"}
    
    def can_execute(self, tool_name):
        if tool_name in self.denied_tools:
            return False, "敏感工具，禁止调用"
        if tool_name not in self.allowed_tools:
            return False, "未授权工具"
        return True, "允许"
```

### 2. 资源限制

| 限制项 | 说明 | 示例 |
|--------|------|------|
| **调用频率** | 单位时间最大调用次数 | 每分钟最多 10 次搜索 |
| **调用总量** | 单任务最大调用次数 | 单次任务最多 50 次调用 |
| **资源配额** | API 成本或数据量限制 | 每次任务最多花费 $1 |

```python
class RateLimiter:
    def __init__(self, max_per_minute=10, max_per_task=50):
        self.minute_limit = max_per_minute
        self.task_limit = max_per_task
    
    def check(self, tool_name):
        if self.minute_counter >= self.minute_limit:
            return False, "频率超限"
        if self.task_counter >= self.task_limit:
            return False, "任务配额用尽"
        return True, "允许"
```

### 3. 执行隔离

**代码执行**：
- 绝不能直接在宿主环境执行用户提供的代码
- 使用容器化（Docker）或沙箱环境

```python
def execute_code_sandbox(code):
    # ❌ 危险
    eval(code)
    
    # ✅ 安全：隔离环境
    container = create_sandbox_container()
    result = container.run(code, timeout=5)
    return result
```

**网络访问**：
- 限制可访问的域名/IP
- 禁止内网访问

### 4. 输出过滤

```python
class OutputGuard:
    def __init__(self):
        self.sensitive_patterns = [
            r"\d{16}",  # 信用卡号
            r"sk-\w+",  # API Key
            r"password[:\s]\S+",  # 密码
        ]
    
    def filter(self, output):
        for pattern in self.sensitive_patterns:
            output = re.sub(pattern, "[已过滤]", output)
        return output
```

---

## Heartbeat：心跳机制

Heartbeat 是 Agent 的"健康检查"机制，确保 Agent 在预期范围内运行：

### 超时控制

```python
async def run_with_heartbeat(agent, task, timeout=300):
    start = time.time()
    while not agent.is_done():
        if time.time() - start > timeout:
            agent.stop()
            return "任务超时，已终止"
        await asyncio.sleep(1)  # 心跳间隔
```

### 人工介入（Human-in-the-loop）

关键节点暂停，等待确认：

```python
def run_with_approval(agent, task, approval_points):
    for step in agent.plan(task):
        if step in approval_points:
            # 暂停，等待人类确认
            user_confirm = wait_for_human(f"确认执行: {step}?")
            if not user_confirm:
                return "用户取消"
        agent.execute(step)
```

---

## Guardrails：内容安全

### 输入 Guardrails

- 恶意指令检测
- 敏感词过滤
- Prompt 注入防御

### 输出 Guardrails

- 有害内容检测
- 敏感信息脱敏
- 格式校验

```python
class Guardrails:
    def check_input(self, user_input):
        if self.contains_malicious_prompt(user_input):
            raise SecurityError("检测到恶意指令")
    
    def check_output(self, model_output):
        if self.contains_harmful_content(model_output):
            return self.sanitize(model_output)
```

---

## 面试高频问题

**Q: Agent 安全要考虑哪些方面？**
> "1. 工具权限控制——白名单而非黑名单；2. 资源限制——频率、配额、成本；3. 执行隔离——代码必须在沙箱运行；4. 输出过滤——敏感信息脱敏；5. 心跳机制——超时控制和人工介入。"

**Q: 怎么防止 Agent 调用过度？**
> "三层防护：1. 单轮 max_steps 限制；2. 单任务总调用次数限制；3. 单位时间频率限制。加上每次调用的成本监控。"

**Q: Human-in-the-loop 适用场景？**
> "1. 敏感操作（删除、支付）；2. 高风险决策（法律、医疗）；3. 不确定情况——当 Agent 置信度低于阈值时触发。"

**Q: 代码执行为什么需要沙箱？**
> "Agent 可能被诱导执行恶意代码。必须隔离：1. 容器化运行；2. 超时限制；3. 资源配额；4. 网络隔离。绝不能 eval() 直接执行。"

---

## 一句话总结

沙箱的本质是**在保证能力的前提下限制破坏范围**：权限控制定边界、资源限制防过度、执行隔离保安全、心跳机制兜底。完全自主是理想，"可控的自主"才是工程现实。
