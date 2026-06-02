"""
query_journal.py
----------------
调用 EasyScholar 开放 API 批量查询期刊标签信息。
若 CDUT 未收录，自动提交评级数据到控制台。

依赖：
    pip install requests

环境变量：
    EASYSCHOLAR_SECRET_KEY  — 在 EasyScholar 开放平台申请的密钥

用法：
    # 批量查询 A1~B2 文件，CDUT 未收录则自动提交
    python query_journal.py

    # 查询单个期刊（不自动提交）
    python query_journal.py --journal "中国图书馆学报"

    # 指定期刊列表文件
    python query_journal.py --file A1.txt A2.txt
"""

import os
import argparse
import requests


# ── 查询 API 封装 ──────────────────────────────────────────────────────────────

def query_journal_tags(journal_name: str, secret_key: str) -> dict:
    """调用 EasyScholar 开放 API 查询期刊标签信息。"""
    url = "https://www.easyscholar.cc/open/getPublicationRank"
    params = {
        "secretKey":       secret_key,
        "publicationName": journal_name,
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# ── 提交 API 封装 ──────────────────────────────────────────────────────────────

SUBMIT_URL = "https://www.easyscholar.cc/api/console/rankData/create"
COOKIE_DICT = {
    "userName":  os.environ.get("EASYSCHOLAR_USERNAME", ""),
    "password":  os.environ.get("EASYSCHOLAR_PASSWORD", ""),
    "JSESSIONID": os.environ.get("EASYSCHOLAR_SESSION", ""),
}
SUBMIT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://www.easyscholar.cc",
    "Pragma": "no-cache",
    "Referer": "https://www.easyscholar.cc/console/rank/edit",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
    ),
    "sec-ch-ua": '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

RANK_MAP = {
    "A1": "1",
    "A2": "2",
    "B1": "3",
    "B2": "4",
    "C":  "5",
}


def submit_rank(journal_name: str, rank_label: str) -> bool:
    """
    向 EasyScholar 控制台提交期刊评级数据。

    Args:
        journal_name: 期刊名称
        rank_label: 等级标签（A1/A2/B1/B2），会自动映射为数字

    Returns:
        True 表示提交成功
    """
    rank_num = RANK_MAP.get(rank_label)
    if not rank_num:
        print(f"    [提交跳过] 未知等级标签：{rank_label}")
        return False

    files = {
        "name": (None, journal_name, "text/plain"),
        "rank": (None, rank_num, "text/plain"),
        "rankInfoUuid": (None, os.environ.get("EASYSCHOLAR_UUID", ""), "text/plain"),
    }
    headers = dict(SUBMIT_HEADERS)
    headers.pop("Content-Type", None)

    try:
        resp = requests.post(SUBMIT_URL, files=files, cookies=COOKIE_DICT,
                            headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if str(data.get("code")) == "200":
            print(f"    [提交成功] {journal_name} → {rank_label}")
            return True
        else:
            print(f"    [提交失败] code={data.get('code')}, msg={data.get('msg')}")
            return False
    except requests.RequestException as e:
        print(f"    [提交错误] {e}")
        return False


# ── 输出解析 ──────────────────────────────────────────────────────────────────

def parse_tags(data: dict, journal_name: str = "", debug: bool = False) -> dict:
    """
    解析并打印期刊标签信息。

    Returns:
        dict with key "cdut_status": actual rank text or "未收录"
    """
    if data.get("code") != 200:
        print(f"  [错误] API 返回异常：{data}")
        return {"cdut_status": "未收录"}

    publication = data.get("data", {})
    if not publication:
        print("  未查询到期刊信息，请确认期刊名称是否正确。")
        return {"cdut_status": "未收录"}

    # 官方收录标签
    official = publication.get("officialRank") or {}
    select = official.get("select") or {}

    cssci_val = select.get("cssci", "未收录")
    pku_val   = select.get("pku", "未收录")
    print(f"  CSSCI: {cssci_val}")
    print(f"  北大核心: {pku_val}")

    other_keys = [k for k in select if k not in ("cssci", "pku")]
    for key in other_keys:
        val = select.get(key)
        if val:
            print(f"  {key}: {val}")

    # 第三方评级标签
    custom = publication.get("customRank") or {}
    rank_info = custom.get("rankInfo") or []
    rank_list = custom.get("rank") or []

    info_map = {item["uuid"]: item for item in rank_info if "uuid" in item}

    if debug:
        import json
        print(f"  [DEBUG] API raw = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))}")
        print()

    level_to_key = {
        "1": "oneRankText",
        "2": "twoRankText",
        "3": "threeRankText",
        "4": "fourRankText",
        "5": "fiveRankText",
    }

    printed_names = set()
    cdut_status = "未收录"
    if rank_list:
        for entry in rank_list:
            parts = entry.split("&&&")
            uuid = parts[0]
            level = parts[1] if len(parts) > 1 else "?"
            info = info_map.get(uuid, {})
            name = info.get("abbName", uuid)
            rank_key = level_to_key.get(level)
            rank_text = info.get(rank_key, level) if rank_key else level
            print(f"  {name}: {rank_text}")
            printed_names.add(name)
            if name == "CDUT":
                cdut_status = rank_text

    if "CDUT" not in printed_names:
        cdut_entry = next((e for e in rank_list
                           if info_map.get(e.split("&&&")[0], {}).get("abbName") == "CDUT"),
                          None)
        if cdut_entry:
            parts = cdut_entry.split("&&&")
            uuid = parts[0]
            level = parts[1] if len(parts) > 1 else "?"
            info = info_map.get(uuid, {})
            rank_key = level_to_key.get(level)
            rank_text = info.get(rank_key, level) if rank_key else level
            print(f"  CDUT: {rank_text}")
            cdut_status = rank_text
        else:
            print("  CDUT: 未收录")

    return {"cdut_status": cdut_status}


# ── 读取期刊列表 ────────────────────────────────────────────────────────────────

def load_journals(filepath: str) -> list[str]:
    """从文本文件读取期刊名称，以「、」分隔，自动删除换行和多余空格。"""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()
    cleaned = raw.replace("\r", "").strip()
    journals = [name.strip() for name in cleaned.replace("\n", "、").split("、") if name.strip() and name.strip() != "/"]
    return journals


def filename_to_rank(filepath: str) -> str:
    """从文件名提取等级标签，如 A1.txt → A1。"""
    basename = os.path.splitext(os.path.basename(filepath))[0].upper()
    if basename in RANK_MAP:
        return basename
    return ""


# ── 主入口 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EasyScholar 期刊标签批量查询工具")
    parser.add_argument(
        "--journal", "-j",
        help="查询单个期刊（不指定则从文件批量读取）",
    )
    parser.add_argument(
        "--file", "-f",
        nargs="*",
        default=None,
        help="期刊列表文件，可指定多个（默认自动匹配 A1/A2/B1/B2/C.txt）",
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="输出 CDUT 相关原始数据用于调试",
    )
    args = parser.parse_args()

    # 从环境变量读取密钥
    secret_key = os.environ.get("EASYSCHOLAR_SECRET_KEY")
    if not secret_key:
        raise EnvironmentError(
            "未找到环境变量 EASYSCHOLAR_SECRET_KEY。\n"
            "请先设置：\n"
            "  Windows CMD : set EASYSCHOLAR_SECRET_KEY=你的密钥\n"
            "  PowerShell  : $env:EASYSCHOLAR_SECRET_KEY='你的密钥'\n"
            "  Linux/macOS : export EASYSCHOLAR_SECRET_KEY='你的密钥'"
        )

    if args.journal:
        # 单个查询模式
        print(f"正在查询期刊「{args.journal}」...\n")
        result = query_journal_tags(args.journal, secret_key)
        parse_tags(result, args.journal, debug=args.debug)
    else:
        # 批量查询模式：遍历所有文件
        if args.file is None:
            # 自动匹配当前目录下的 A1/A2/B1/B2/C.txt（不区分大小写）
            targets = {"a1", "a2", "b1", "b2", "c"}
            file_list = [
                f for f in os.listdir(".")
                if os.path.isfile(f)
                and os.path.splitext(f)[0].lower() in targets
                and os.path.splitext(f)[1].lower() == ".txt"
            ]
            file_list.sort(key=lambda x: targets.index(os.path.splitext(x)[0].lower()))
        else:
            file_list = args.file
        total_files = len(file_list)
        for fi, filepath in enumerate(file_list, 1):
            if not os.path.exists(filepath):
                print(f"[文件 {fi}/{total_files}] 不存在，跳过：{filepath}\n")
                continue

            rank_label = filename_to_rank(filepath)
            journals = load_journals(filepath)
            if not journals:
                print(f"[文件 {fi}/{total_files}] {filepath} 为空，跳过。\n")
                continue

            rank_display = f"（等级 {rank_label}）" if rank_label else ""
            print(f"=== [{fi}/{total_files}] 处理文件：{filepath} {rank_display} ===")
            print(f"读取到 {len(journals)} 个期刊：")
            for i, name in enumerate(journals, 1):
                print(f"  {i}. {name}")
            print()

            for idx, name in enumerate(journals, 1):
                print(f"  [{idx}/{len(journals)}] 正在查询「{name}」...")
                try:
                    result = query_journal_tags(name, secret_key)
                    info = parse_tags(result, name, debug=args.debug)

                    # CDUT 未收录且文件名对应有效等级 → 自动提交
                    if info["cdut_status"] == "未收录" and rank_label:
                        print(f"  → CDUT 未收录，正在提交 {rank_label} ...")
                        submit_rank(name, rank_label)
                except requests.RequestException as e:
                    print(f"  [网络错误] {e}")
                print()


if __name__ == "__main__":
    main()
