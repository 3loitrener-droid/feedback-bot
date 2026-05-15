import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.feedback import Feedback, FeedbackCriterionMapping
from app.models.employee import Employee
from app.models.period import Period
from app.models.criteria import CriteriaMatrix
from app.models.summary import Summary
from app.llm.analyzer import SummaryGenerator
from app.config import settings


class SummaryService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.generator = SummaryGenerator()

    async def generate(self, employee_id: uuid.UUID, period_id: uuid.UUID, manager_id: uuid.UUID):
        # Получаем данные
        emp_result = await self.db.execute(select(Employee).where(Employee.employee_id == employee_id))
        employee = emp_result.scalar_one_or_none()
        if not employee:
            return

        period_result = await self.db.execute(select(Period).where(Period.period_id == period_id))
        period = period_result.scalar_one_or_none()
        if not period:
            return

        fb_result = await self.db.execute(
            select(Feedback)
            .where(
                Feedback.employee_id == employee_id,
                Feedback.period_id == period_id,
                Feedback.manager_id == manager_id,
                Feedback.is_deleted == False,
            )
            .options(selectinload(Feedback.mappings).selectinload(FeedbackCriterionMapping.criterion))
        )
        feedbacks = fb_result.scalars().all()

        criteria_result = await self.db.execute(
            select(CriteriaMatrix).where(CriteriaMatrix.is_active == True, CriteriaMatrix.is_key_criterion == True)
        )
        key_criteria = [c.criterion_name for c in criteria_result.scalars().all()]

        total = len(feedbacks)
        no_criterion = sum(1 for f in feedbacks if f.status == "no_criterion")
        mapped = total - no_criterion

        # Готовим данные для LLM
        feedbacks_data = []
        needs_attention = []
        for fb in feedbacks:
            mappings_data = []
            for m in fb.mappings:
                if m.manager_confirmed or m.confirmed_rating:
                    mappings_data.append({
                        "criterion_name": m.criterion.criterion_name if m.criterion else "Неизвестно",
                        "original_fragment": m.original_fragment,
                        "confirmed_rating": m.confirmed_rating,
                        "suggested_rating": m.suggested_rating,
                    })

            feedbacks_data.append({
                "feedback_id": str(fb.feedback_id),
                "original_text": fb.original_text,
                "feedback_date": str(fb.feedback_date),
                "mappings": mappings_data,
            })

            if fb.status == "no_criterion":
                needs_attention.append({
                    "feedback_id": str(fb.feedback_id),
                    "original_text": fb.original_text,
                    "reason": "Без критерия — не размечен",
                })

        # Вызываем LLM
        llm_result = await self.generator.generate(
            employee_name=employee.full_name,
            period_name=period.period_name,
            feedbacks=feedbacks_data,
            key_criteria=key_criteria,
        )

        # Добавляем needs_attention из незамеченных комментариев
        existing_attention = {na["feedback_id"] for na in llm_result.get("needs_attention", [])}
        for na in needs_attention:
            if na["feedback_id"] not in existing_attention:
                llm_result.setdefault("needs_attention", []).append(na)

        # Помечаем предыдущие summary устаревшими
        old_summaries_result = await self.db.execute(
            select(Summary).where(
                Summary.employee_id == employee_id,
                Summary.period_id == period_id,
                Summary.manager_id == manager_id,
                Summary.is_current == True,
            )
        )
        for old in old_summaries_result.scalars().all():
            old.is_current = False

        recommendation = llm_result.get("recommendation", {})
        summary = Summary(
            employee_id=employee_id,
            manager_id=manager_id,
            period_id=period_id,
            generated_at=datetime.utcnow(),
            total_feedback_count=total,
            mapped_feedback_count=mapped,
            unmapped_feedback_count=no_criterion,
            strengths=llm_result.get("strengths"),
            growth_areas=llm_result.get("growth_areas"),
            criterion_breakdown=llm_result.get("criterion_breakdown"),
            top_criteria=llm_result.get("top_criteria"),
            repeating_patterns=llm_result.get("repeating_patterns"),
            rating_recommendation=recommendation.get("rating"),
            arguments_for=recommendation.get("arguments_for"),
            arguments_against=recommendation.get("arguments_against"),
            risks=recommendation.get("risks"),
            disputed_areas=llm_result.get("disputed_areas"),
            needs_attention=llm_result.get("needs_attention"),
            evidence_comments=llm_result.get("criterion_breakdown"),
            llm_model_version=settings.llm_model,
            is_current=True,
        )
        self.db.add(summary)
        await self.db.commit()
        return summary
