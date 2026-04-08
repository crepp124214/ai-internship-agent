"""
SearchJobsTool — 搜索公司招聘官网

该工具将关键词转换为公司招聘官网搜索，
而不是搜索本地数据库。
"""
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class SearchJobsInput(BaseModel):
    """Input schema for search_jobs tool."""
    keyword: str
    location: str = ""
    limit: int = 5


# 常见公司校招官网映射（关键词 → 官网 URL）
KNOWN_COMPANY_RECRUITMENT_PAGES = {
    "字节跳动": "https://jobs.bytedance.com/campus",
    "字节": "https://jobs.bytedance.com/campus",
    "bytedance": "https://jobs.bytedance.com/campus",
    "腾讯": "https://careers.qq.com",
    "腾讯云": "https://careers.qq.com",
    "阿里": "https://campus.aliyun.com",
    "阿里巴巴": "https://campus.aliyun.com",
    "阿里云": "https://campus.aliyun.com",
    "华为": "https://career.huawei.com",
    "shopee": "https://careers.shopee.cn",
    "虾皮": "https://careers.shopee.cn",
    "虾皮信息": "https://careers.shopee.cn",
    "美团": "https://campus.meituan.com",
    "京东": "https://careers.jd.com",
    "快手": "https://careers.kuaishou.cn",
    "百度": "https://talent.baidu.com",
    "网易": "https://campus.163.com",
    "bilibili": "https://job.bilibili.com",
    "b站": "https://job.bilibili.com",
    "小红书": "https://job.xiaohongshu.com",
    "米哈游": "https://careers.mihoyo.com",
    "shein": "https://careers.shein.com",
    "希音": "https://careers.shein.com",
}


class SearchJobsTool(BaseTool):
    """根据关键词搜索公司招聘官网"""

    name: str = "search_jobs"
    description: str = "搜索公司招聘官网 URL，帮助用户找到该公司校园招聘或实习招聘页面"
    args_schema: Type[BaseModel] = SearchJobsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.business_logic.common.tools.web_search import WebSearchTool

        keyword = tool_input.get("keyword", "")
        location = tool_input.get("location", "")
        limit = tool_input.get("limit", 5)

        if not keyword:
            return {"error": "keyword is required", "results": []}

        if context is None:
            raise ValueError("ToolContext is required")

        # 优先从已知公司映射中查找
        matched_companies = []
        keyword_lower = keyword.lower()
        for company, url in KNOWN_COMPANY_RECRUITMENT_PAGES.items():
            if keyword_lower in company.lower():
                matched_companies.append({
                    "company": company,
                    "url": url,
                    "type": "direct",
                    "snippet": f"{company} 招聘官网，包含校园招聘和实习招聘信息",
                })

        # 如果有关键词匹配的公司，直接返回
        if matched_companies:
            return {
                "keyword": keyword,
                "location": location,
                "count": len(matched_companies),
                "results": matched_companies[:limit],
                "source": "known_companies",
            }

        # 否则使用 web_search 搜索
        search_query = f"{keyword} {location} 2026 校招 实习 招聘官网".strip()
        web_search_tool = WebSearchTool()
        web_results = web_search_tool._execute_sync(
            tool_input={"query": search_query, "limit": limit},
            context=context,
        )

        # 格式化 web_search 结果，提取公司招聘官网
        formatted_results = []
        seen_companies = set()

        for result in web_results.get("results", []):
            url = result.get("url", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # 提取公司名（从标题中）
            company = self._extract_company_name(title, keyword)

            if company and company not in seen_companies:
                seen_companies.add(company)
                formatted_results.append({
                    "company": company,
                    "url": url,
                    "type": "search",
                    "snippet": snippet[:200] if snippet else "",
                })

        return {
            "keyword": keyword,
            "location": location,
            "count": len(formatted_results),
            "results": formatted_results[:limit],
            "source": "web_search",
        }

    def _extract_company_name(self, title: str, keyword: str) -> str:
        """从搜索结果标题中提取公司名"""
        import re
        # 尝试从已知的公司名列表中匹配
        for company in KNOWN_COMPANY_RECRUITMENT_PAGES.keys():
            if company in title:
                return company
        # 尝试提取第一个词作为公司名
        match = re.match(r'^([^\s]+)', title)
        if match:
            return match.group(1)
        return keyword
