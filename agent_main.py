#!/usr/bin/env python3
"""
Unified planner/router entrypoint.

Examples:
  python agent_main.py "分析 600519.SH" --user my_user --name 贵州茅台
  python agent_main.py "今日哪些板块强？"
  python agent_main.py "记住我持有半导体ETF，风险偏好中等"
"""
import argparse

from workflow.router import run_agent_request


def main():
    parser = argparse.ArgumentParser(description="多智能体投研系统统一入口")
    parser.add_argument("query", help="自然语言任务，例如：分析 600519.SH / 今日哪些板块强")
    parser.add_argument("--user", default="default_user", help="用户ID，用于长期记忆")
    parser.add_argument("--name", default="", help="公司名称，可选")
    args = parser.parse_args()

    result = run_agent_request(args.query, user_id=args.user, company_name=args.name)
    print(result)


if __name__ == "__main__":
    main()
