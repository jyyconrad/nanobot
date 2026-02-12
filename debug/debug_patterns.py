#!/usr/bin/env python3
import re

text = '你好，请问明天的天气怎么样？'

greeting_pattern1 = re.compile(r'^(你好|您好|哈喽|嗨|早|早上好|晚上好|下午好)', re.IGNORECASE)
greeting_pattern2 = re.compile(r'^.*(问候|打招呼).*$', re.IGNORECASE)

query_pattern1 = re.compile(r'^.*(查询|查找|搜索|问|请问|想知道|了解).*$', re.IGNORECASE)
query_pattern2 = re.compile(r'^.*(\?|\？)$')

print('消息:', text)
print()
print('Greeting 模式:')
print('  模式1:', greeting_pattern1.pattern)
print('  匹配结果:', greeting_pattern1.search(text))
print('  模式2:', greeting_pattern2.pattern)
print('  匹配结果:', greeting_pattern2.search(text))
print()
print('Query 模式:')
print('  模式1:', query_pattern1.pattern)
print('  匹配结果:', query_pattern1.search(text))
print('  模式2:', query_pattern2.pattern)
print('  匹配结果:', query_pattern2.search(text))
