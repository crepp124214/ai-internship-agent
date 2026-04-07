"""AI 面试官 Agent — 基于 AgentExecutor 的多轮面试对练"""
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry


class InterviewCoachAgent:
    """
    AI 面试官 Agent
    使用 LLM 生成开场白、问题列表，对每条回答评分。
    独立于 AgentExecutor（不走 ReAct 循环，直接调用 LLM）。
    """

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tool_registry: ToolRegistry | None = None,
        memory: MemoryStore | None = None,
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._memory = memory
        self._system_prompt = (
            "你是一位资深技术面试官，擅长评估候选人的技术深度、逻辑思维和沟通能力。\n"
            "你的任务是：\n"
            "1. 生成贴合岗位 JD 的面试问题\n"
            "2. 对候选人的回答给出客观评分和改进建议\n"
            "评分标准：0-100，60分以下为不及格，60-75为一般，75-90为良好，90+为优秀"
        )

    async def generate_coach_flow(
        self,
        job_title: str,
        jd_text: str,
        count: int = 5,
    ) -> dict:
        """
        生成面试开场白和问题列表。
        """
        prompt = (
            f"{self._system_prompt}\n\n"
            f"请为以下岗位生成{count}个技术面试问题：\n"
            f"岗位：{job_title}\n"
            f"岗位描述：{jd_text}\n\n"
            "输出格式：\n"
            "【开场白】你好，我是...（简短自我介绍）\n"
            "【问题1】xxx\n"
            "【问题2】xxx\n"
            "...\n"
            "每个问题要贴合 JD，不要问过于通用的题目。"
        )
        response = await self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        # 解析开场白和问题
        opening = ""
        questions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("【开场白】"):
                opening = line.replace("【开场白】", "").strip()
            elif line.startswith("【问题"):
                q = line.split("】", 1)[-1].strip() if "】" in line else line
                if q:
                    questions.append(q)
            elif line.startswith("Q") and ":" in line:
                q = line.split(":", 1)[-1].strip()
                if q and q not in questions:
                    questions.append(q)

        return {
            "opening": opening or f"你好，我是{job_title}的面试官，我们开始吧。",
            "questions": questions[:count],
        }

    async def evaluate_single_answer(
        self,
        question: str,
        answer: str,
        job_context: str | None = None,
    ) -> dict:
        """
        对单条回答评分。
        """
        context = f"\n岗位参考：{job_context}" if job_context else ""
        prompt = (
            f"{self._system_prompt}\n\n"
            f"面试问题：{question}\n"
            f"候选人回答：{answer}{context}\n\n"
            "请给出评分和改进建议，格式如下：\n"
            "Score: <0-100>\n"
            "Feedback: <简短评估和改进建议>"
        )
        response = await self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        # 解析 score
        import re
        score_match = re.search(r"score:\s*(\d+)", content, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 60

        # 解析 feedback
        fb_match = re.search(r"feedback:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
        feedback = fb_match.group(1).strip() if fb_match else "评分暂不可用"

        return {"score": max(0, min(100, score)), "feedback": feedback}

    async def generate_followup_questions(
        self,
        question: str,
        answer: str,
        job_context: str | None = None,
    ) -> list[str]:
        """
        生成追问问题列表。
        """
        context = f"\n岗位参考：{job_context}" if job_context else ""
        prompt = (
            f"{self._system_prompt}\n\n"
            f"主问题：{question}\n"
            f"候选人回答：{answer}{context}\n\n"
            "根据以上回答，生成1-2个追问问题，深入考察候选人。\n"
            "输出格式（每行一个问题）：\n"
            "追问1: xxx\n"
            "追问2: xxx"
        )
        response = await self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        questions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("追问") and ":" in line:
                q = line.split(":", 1)[-1].strip()
                if q:
                    questions.append(q)
            elif line and not line.startswith("#"):
                questions.append(line)
        return questions[:2]