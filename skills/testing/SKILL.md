---
name: testing
description: "测试技能 - 编写和执行各种类型的测试。用于单元测试、集成测试、端到端测试等任务。"
version: "1.0.0"
metadata:
  nanobot:
    emoji: "🧪"
    keywords: ["测试", "test", "单元测试", "测试用例", "coverage"]
---

# Testing Skill

测试技能 - 编写和执行各种类型的测试。

## 何时使用此技能

当任务涉及以下内容时使用：
- 编写测试用例
- 执行单元测试
- 集成测试
- 端到端测试
- 测试覆盖率分析
- 测试报告生成

## 测试类型

### 1. 单元测试

针对最小代码单元（函数、方法、类）：
- 独立运行
- 快速执行
- 覆盖边界条件
- 使用测试框架（pytest, unittest, jest）

### 2. 集成测试

测试多个组件或模块的协作：
- 测试接口和依赖
- 验证数据流
- 检查系统集成

### 3. 端到端测试

测试完整的应用程序流程：
- 用户场景模拟
- 浏览器/UI 自动化
- 真实环境测试

## 测试框架

### Python 测试

**pytest**（推荐）：
```python
import pytest

def test_addition():
    assert 2 + 2 == 4

def test_subtraction():
    assert 5 - 3 == 2

class TestMathOperations:
    def test_multiplication(self):
        assert 3 * 4 == 12

    def test_division(self):
        assert 10 / 2 == 5
```

**unittest**：
```python
import unittest

class TestMathOperations(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(2 + 2, 4)
    
    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)
```

### JavaScript 测试

**Jest**（推荐）：
```javascript
test('加法测试', () => {
  expect(2 + 2).toBe(4);
});

test('减法测试', () => {
  expect(5 - 3).toBe(2);
});

describe('数学运算', () => {
  test('乘法', () => {
    expect(3 * 4).toBe(12);
  });
  
  test('除法', () => {
    expect(10 / 2).toBe(5);
  });
});
```

## 测试编写原则

### 1. 清晰性

- 测试名称应描述测试内容
- 使用简单、直接的断言
- 避免复杂逻辑

### 2. 独立性

- 每个测试应独立运行
- 不依赖其他测试的状态
- 避免共享数据

### 3. 可读性

- 使用有意义的变量名
- 添加必要的注释
- 保持测试代码简洁

### 4. 边界条件

测试边界条件：
```python
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        10 / 0
```

## Mock 和 Stub

### Python - unittest.mock

```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_obj = Mock()
    mock_obj.some_method.return_value = "test"
    
    result = some_function(mock_obj)
    assert result == "test"
    mock_obj.some_method.assert_called_once()
```

### JavaScript - Jest Mock

```javascript
jest.mock('./api');

test('使用 mock 测试', async () => {
  const mockData = { name: 'Test' };
  const api = require('./api');
  api.fetchData.mockResolvedValue(mockData);
  
  const result = await fetchDataFromAPI();
  expect(result).toEqual(mockData);
  expect(api.fetchData).toHaveBeenCalled();
});
```

## 测试覆盖率

### Python - Coverage.py

```bash
pip install coverage
coverage run -m pytest tests/
coverage report -m
```

### JavaScript - Istanbul

```bash
npm install --save-dev nyc
nyc npm test
```

## 常见测试模式

### 参数化测试

**pytest**：
```python
@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
])
def test_addition(a, b, expected):
    assert a + b == expected
```

**Jest**：
```javascript
test.each([
  [1, 2, 3],
  [0, 0, 0],
  [-1, 1, 0],
])('加法测试: %i + %i = %i', (a, b, expected) => {
  expect(a + b).toBe(expected);
});
```

## 测试最佳实践

1. **TDD（测试驱动开发）**：先写测试，再写代码
2. **高频运行**：自动化运行测试
3. **快速失败**：测试应该快速失败
4. **文档化**：测试是代码的最佳文档
5. **持续集成**：每次代码更改都运行测试

## 测试检查清单

创建测试时，检查：
- [ ] 测试名称是否描述清楚测试内容
- [ ] 是否覆盖边界条件
- [ ] 每个测试是否独立
- [ ] 断言是否简单明确
- [ ] 是否使用了适当的 Mock/Stub
- [ ] 测试覆盖率是否足够

## 性能测试

### Python - pytest-benchmark

```python
def test_performance(benchmark):
    result = benchmark(lambda: some_function())
    assert result is not None
```

### JavaScript - Benchmark.js

```javascript
import Benchmark from 'benchmark';

const suite = new Benchmark.Suite;

suite.add('测试名称', () => {
  someFunction();
})
.on('cycle', event => {
  console.log(String(event.target));
})
.run({ 'async': true });
```

## 参考资源

详见 [TESTING_PATTERNS.md](references/TESTING_PATTERNS.md) 了解常见测试模式。
详见 [COVERAGE_GUIDE.md](references/COVERAGE_GUIDE.md) 了解测试覆盖最佳实践。

## 工具使用

此技能通常配合以下工具使用：
- `ReadFileTool` - 读取代码文件
- `WriteFileTool` - 写入测试文件
- `ExecTool` - 运行测试命令
- `WebSearchTool` - 查找测试示例

记住：好的测试是代码质量的守护者。
