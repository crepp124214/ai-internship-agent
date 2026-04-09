"""任务路由服务 — 根据用户任务路由到对应 Agent"""

from dataclasses import dataclass


@dataclass
class TaskContext:
    """任务上下文"""
    resume_id: int | None = None
    jd_id: int | None = None
    session_id: str | None = None
    task_type: str = "generic"


class AgentChatService:
    """根据任务内容路由到对应的 Agent 或处理逻辑"""

    # 路由关键词映射
    ROUTE_KEYWORDS = {
        "jd_customizer": ["简历", "jd", "定制", "匹配度", "岗位"],
        "interview_coach": ["面试", "对练", "练习", "问题", "评分"],
    }

    def route_task(self, task: str) -> str:
        """
        根据任务描述返回目标 Agent 标识符。
        """
        task_lower = task.lower()
        for agent, keywords in self.ROUTE_KEYWORDS.items():
            if any(kw in task_lower for kw in keywords):
                return agent
        return "generic"

    def build_context(
        self,
        resume_id: int | None = None,
        jd_id: int | None = None,
        session_id: str | None = None,
    ) -> dict:
        """
        构建任务上下文。
        """
        task_type = "generic"  # 后续根据参数推导
        if resume_id and jd_id:
            task_type = "jd_customizer"
        elif resume_id:
            task_type = "interview_coach"
        return TaskContext(
            resume_id=resume_id,
            jd_id=jd_id,
            session_id=session_id,
            task_type=task_type,
        ).__dict__

    def get_system_prompt(self, task_type: str) -> str:
        """
        根据任务类型返回系统提示词。
        """
        prompts = {
            "jd_customizer": "你是一个简历定制专家，擅长根据岗位分析简历并给出优化建议。",
            "interview_coach": "你是一个资深面试官，擅长评估候选人的技术能力和沟通表达。",
            "generic": "你是一个求职助手，擅长回答各类求职相关问题。",
        }
        return prompts.get(task_type, prompts["generic"])
