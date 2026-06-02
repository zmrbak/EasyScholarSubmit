# query_journal.py 使用说明

EasyScholar 期刊标签批量查询与 CDUT 评级自动提交工具。

## 功能

- 调用 EasyScholar 开放 API 查询期刊标签（CSSCI、北大核心、CDUT 等）
- CDUT 未收录时，自动向 EasyScholar 控制台提交评级数据
- 按文件名自动识别等级（A1/A2/B1/B2/C）

## 环境准备

```bash
pip install requests
```

## 环境变量

| 变量名 | 说明 |
|--------|------|
| `EASYSCHOLAR_SECRET_KEY` | 开放平台查询密钥（必需） |
| `EASYSCHOLAR_UUID` | CDUT 评级体系 UUID（提交时必需） |
| `EASYSCHOLAR_USERNAME` | 控制台 userName Cookie（提交时必需） |
| `EASYSCHOLAR_PASSWORD` | 控制台 password Cookie（提交时必需） |
| `EASYSCHOLAR_SESSION` | 控制台 JSESSIONID Cookie（提交时必需） |

`EASYSCHOLAR_SECRET_KEY`
来自于： https://www.easyscholar.cc/console/user/open

`EASYSCHOLAR_UUID`
在https://www.easyscholar.cc/console/rank/edit 从负载中获取（rankInfoUuid）。

`EASYSCHOLAR_USERNAME`
在https://www.easyscholar.cc/console/rank/edit 从Cookie中获取(userName)。

`EASYSCHOLAR_PASSWORD`
在https://www.easyscholar.cc/console/rank/edit 从Cookie中获取(password)。

`EASYSCHOLAR_SESSION`
在https://www.easyscholar.cc/console/rank/edit 从Cookie中获取(JSESSIONID)。


设置示例：

```bash
# Windows CMD
set EASYSCHOLAR_SECRET_KEY=你的密钥
set EASYSCHOLAR_UUID=评级体系UUID
set EASYSCHOLAR_USERNAME=控制台userName
set EASYSCHOLAR_PASSWORD=控制台password
set EASYSCHOLAR_SESSION=控制台JSESSIONID

# PowerShell
$env:EASYSCHOLAR_SECRET_KEY='你的密钥'
$env:EASYSCHOLAR_UUID='评级体系UUID'
$env:EASYSCHOLAR_USERNAME='控制台userName'
$env:EASYSCHOLAR_PASSWORD='控制台password'
$env:EASYSCHOLAR_SESSION='控制台JSESSIONID'

# Linux/macOS
export EASYSCHOLAR_SECRET_KEY='你的密钥'
export EASYSCHOLAR_UUID='评级体系UUID'
export EASYSCHOLAR_USERNAME='控制台userName'
export EASYSCHOLAR_PASSWORD='控制台password'
export EASYSCHOLAR_SESSION='控制台JSESSIONID'
```


## 用法

### 批量查询（默认）

自动匹配当前目录下的 A1/A2/B1/B2/C.txt（不区分大小写），CDUT 未收录则自动提交。

```bash
python query_journal.py
```

### 指定文件

```bash
python query_journal.py -f A1.txt B2.txt
```

### 查询单个期刊（不自动提交）

```bash
python query_journal.py -j "中国图书馆学报"
```

### 调试模式（输出 API 原始 JSON）

```bash
python query_journal.py -j "马克思主义研究" -d
```

## 参数说明

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--journal` | `-j` | 查询单个期刊（不触发自动提交） |
| `--file` | `-f` | 指定期刊列表文件（默认自动匹配） |
| `--debug` | `-d` | 输出 API 原始 JSON 用于调试 |

## 期刊列表文件格式

文件名即等级（A1/A2/B1/B2/C，不区分大小写），内容支持两种分隔方式：

**换行分隔：**
```
马克思主义研究
求是
思想理论教育
```

**顿号分隔：**
```
马克思主义研究、求是、思想理论教育
```

两种方式可混用，期刊名为 "/" 的条目会被自动忽略。

## 等级映射

| 等级 | 数字 |
|------|------|
| A1 | 1 |
| A2 | 2 |
| B1 | 3 |
| B2 | 4 |
| C | 5 |

## 输出示例

```
=== [1/4] 处理文件：A1.txt （等级 A1） ===
读取到 3 个期刊：
  1. 马克思主义研究
  2. 求是
  3. 思想理论教育

  [1/3] 正在查询「马克思主义研究」...
  CSSCI: CSSCI
  北大核心: 1
  CDUT: A1

  [2/3] 正在查询「求是」...
  CSSCI: CSSCI
  北大核心: 1
  CDUT: 未收录
  → CDUT 未收录，正在提交 A1 ...
    [提交成功] 求是 → A1
```

## 注意事项

- Cookie 有过期时间，控制台提交失败时需更新对应环境变量
- 单个期刊查询模式（`-j`）不会触发自动提交
- 批量模式下，文件名必须为 A1/A2/B1/B2/C 才能识别等级并自动提交
- 非期刊实体（如出版社）在 API 端可能返回空数据，脚本会跳过
