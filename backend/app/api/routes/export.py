from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from jinja2 import Environment, BaseLoader
import uuid

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.employee import Employee
from app.models.period import Period
from app.models.summary import Summary
from app.models.feedback import Feedback, FeedbackCriterionMapping
router = APIRouter(prefix="/export", tags=["export"])

SUMMARY_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: Arial, sans-serif; font-size: 13px; color: #1a1a1a; max-width: 900px; margin: 40px auto; padding: 0 20px; }
  h1 { font-size: 22px; margin-bottom: 4px; }
  .meta { color: #666; font-size: 12px; margin-bottom: 28px; }
  h2 { font-size: 15px; font-weight: 600; border-bottom: 1px solid #e5e5e5; padding-bottom: 6px; margin-top: 28px; }
  h3 { font-size: 13px; font-weight: 600; margin: 16px 0 6px; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid; }
  .below { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
  .meet { background: #fffbeb; color: #92400e; border-color: #fde68a; }
  .exceeds { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
  .insufficient { background: #f9fafb; color: #6b7280; border-color: #e5e7eb; }
  .quote { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 8px 12px; font-style: italic; margin: 4px 0; font-size: 12px; }
  .stats { display: flex; gap: 24px; margin: 16px 0; }
  .stat { background: #f9fafb; padding: 12px 20px; border-radius: 8px; }
  .stat-n { font-size: 22px; font-weight: 700; }
  .stat-l { font-size: 11px; color: #6b7280; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th { background: #f9fafb; text-align: left; padding: 8px 12px; font-size: 11px; color: #6b7280; text-transform: uppercase; }
  td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; font-size: 12px; }
  .red { color: #ef4444; font-weight: 600; }
  .amber { color: #f59e0b; font-weight: 600; }
  .green { color: #22c55e; font-weight: 600; }
  .section-note { font-size: 11px; color: #9ca3af; margin-bottom: 4px; }
  .systemic { display: inline-block; background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; border-radius: 4px; padding: 1px 6px; font-size: 10px; }
  .key { display: inline-block; background: #f5f3ff; color: #6d28d9; border: 1px solid #ddd6fe; border-radius: 4px; padding: 1px 6px; font-size: 10px; }
  footer { margin-top: 48px; font-size: 11px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 12px; }
</style>
</head>
<body>
<h1>{{ employee_name }}</h1>
<div class="meta">{{ period_name }} · Performance Review Summary · Сгенерировано: {{ generated_at }}</div>

<div class="stats">
  <div class="stat">
    <div class="stat-n">{{ total }}</div>
    <div class="stat-l">Всего комментариев</div>
  </div>
  <div class="stat">
    <div class="stat-n">{{ mapped }}</div>
    <div class="stat-l">Размечено</div>
  </div>
  <div class="stat">
    <div class="stat-n">{{ unmapped }}</div>
    <div class="stat-l">Без критерия</div>
  </div>
  <div class="stat">
    <div class="stat-n">
      <span class="badge {{ rec_class }}">{{ rec_label }}</span>
    </div>
    <div class="stat-l">Рекомендация системы</div>
  </div>
</div>

{% if top_criteria %}
<h2>Топ критериев по упоминаниям</h2>
<table>
  <thead><tr><th>#</th><th>Критерий</th><th>Упоминаний</th></tr></thead>
  <tbody>
  {% for c in top_criteria %}
  <tr>
    <td>{{ loop.index }}</td>
    <td>{{ c.criterion_name }}</td>
    <td>{{ c.mention_count }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}

{% if strengths %}
<h2>Сильные зоны</h2>
{% for s in strengths %}
<h3>{{ s.criterion_name }}</h3>
<p style="color:#555; font-size:12px;">{{ s.pattern_description }}</p>
<p class="section-note">Evidence (оригинальные слова руководителя):</p>
{% for q in s.evidence_quotes %}
<div class="quote">«{{ q }}»</div>
{% endfor %}
{% endfor %}
{% endif %}

{% if growth_areas %}
<h2>Зоны роста</h2>
{% for g in growth_areas %}
<h3>
  {{ g.criterion_name }}
  {% if g.is_systemic %}<span class="systemic">Системная проблема</span>{% endif %}
  {% if g.is_key_criterion %}<span class="key">Ключевой критерий</span>{% endif %}
</h3>
<p style="color:#555; font-size:12px;">{{ g.pattern_description }}</p>
<p class="section-note">Evidence:</p>
{% for q in g.evidence_quotes %}
<div class="quote">«{{ q }}»</div>
{% endfor %}
{% endfor %}
{% endif %}

{% if criterion_breakdown %}
<h2>Матрица оценок</h2>
<table>
  <thead><tr><th>Критерий</th><th>Below</th><th>Meet</th><th>Exceeds</th></tr></thead>
  <tbody>
  {% for c in criterion_breakdown %}
  <tr>
    <td>{{ c.criterion_name }}</td>
    <td>{% if c.below_count %}<span class="red">{{ c.below_count }}</span>{% else %}—{% endif %}</td>
    <td>{% if c.meet_count %}<span class="amber">{{ c.meet_count }}</span>{% else %}—{% endif %}</td>
    <td>{% if c.exceeds_count %}<span class="green">{{ c.exceeds_count }}</span>{% else %}—{% endif %}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}

{% if arguments_for or arguments_against %}
<h2>Аргументы к оценке</h2>
{% if arguments_for %}
<h3>За оценку:</h3>
<ul>{% for a in arguments_for %}<li>{{ a }}</li>{% endfor %}</ul>
{% endif %}
{% if arguments_against %}
<h3>Риски:</h3>
<ul>{% for a in arguments_against %}<li>{{ a }}</li>{% endfor %}</ul>
{% endif %}
{% endif %}

{% if needs_attention %}
<h2>⚠️ Требует проверки</h2>
{% for n in needs_attention %}
<div style="background:#fffbeb; border:1px solid #fde68a; border-radius:6px; padding:8px 12px; margin-bottom:8px;">
  <div style="font-size:11px; color:#92400e;">{{ n.reason }}</div>
  <div class="quote" style="background:transparent; border:0; margin:4px 0 0;">«{{ n.original_text }}»</div>
</div>
{% endfor %}
{% endif %}

{% if feedbacks %}
<h2>Все оригинальные комментарии</h2>
<p class="section-note">Хранятся точь-в-точь, без изменений.</p>
{% for fb in feedbacks %}
<div style="margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #f3f4f6;">
  <div style="font-size:11px; color:#9ca3af; margin-bottom:4px;">{{ fb.feedback_date }} · {{ fb.status }}</div>
  <div class="quote">«{{ fb.original_text }}»</div>
  {% if fb.mappings %}
  <div style="margin-top:6px; display:flex; gap:8px; flex-wrap:wrap;">
    {% for m in fb.mappings %}
    <span style="font-size:11px; background:#f3f4f6; border-radius:4px; padding:2px 8px;">
      {{ m.criterion_name }}{% if m.confirmed_rating %} · {{ m.confirmed_rating[:5] }}{% endif %}
    </span>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endfor %}
{% endif %}

<footer>
  Feedback Assistant · {{ generated_at }} · LLM: {{ llm_model }}<br>
  Оригинальные комментарии руководителя хранятся в неизменном виде. Рекомендация системы носит информационный характер — финальную оценку принимает руководитель.
</footer>
</body>
</html>"""

_jinja_env = Environment(loader=BaseLoader())
_template = _jinja_env.from_string(SUMMARY_HTML_TEMPLATE)


@router.get("/summary")
async def export_summary_html(
    employee_id: uuid.UUID,
    period_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    emp_result = await db.execute(select(Employee).where(Employee.employee_id == employee_id))
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    period_result = await db.execute(select(Period).where(Period.period_id == period_id))
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Период не найден")

    sum_result = await db.execute(
        select(Summary).where(
            Summary.employee_id == employee_id,
            Summary.period_id == period_id,
            Summary.manager_id == current_user.user_id,
            Summary.is_current == True,
        ).order_by(Summary.generated_at.desc()).limit(1)
    )
    summary = sum_result.scalar_one_or_none()

    fb_result = await db.execute(
        select(Feedback)
        .where(
            Feedback.employee_id == employee_id,
            Feedback.period_id == period_id,
            Feedback.manager_id == current_user.user_id,
            Feedback.is_deleted == False,
        )
        .options(selectinload(Feedback.mappings).selectinload(FeedbackCriterionMapping.criterion))
        .order_by(Feedback.feedback_date.desc())
    )
    feedbacks = fb_result.scalars().all()

    rec = summary.rating_recommendation if summary else None
    rec_class_map = {
        "Below expectations": "below",
        "Meet expectations": "meet",
        "Exceeds expectations": "exceeds",
    }
    rec_label_map = {
        "Below expectations": "Below",
        "Meet expectations": "Meet",
        "Exceeds expectations": "Exceeds",
        "insufficient_data": "Нет данных",
    }

    feedbacks_data = [
        {
            "feedback_date": str(fb.feedback_date),
            "original_text": fb.original_text,
            "status": fb.status,
            "mappings": [
                {
                    "criterion_name": m.criterion.criterion_name if m.criterion else "?",
                    "confirmed_rating": m.confirmed_rating or m.suggested_rating,
                }
                for m in fb.mappings
            ],
        }
        for fb in feedbacks
    ]

    from datetime import datetime
    html = _template.render(
        employee_name=employee.full_name,
        period_name=period.period_name,
        generated_at=datetime.utcnow().strftime("%d.%m.%Y %H:%M"),
        total=summary.total_feedback_count if summary else len(feedbacks),
        mapped=summary.mapped_feedback_count if summary else 0,
        unmapped=summary.unmapped_feedback_count if summary else 0,
        rec_label=rec_label_map.get(rec or "", "—"),
        rec_class=rec_class_map.get(rec or "", "insufficient"),
        top_criteria=summary.top_criteria or [] if summary else [],
        strengths=summary.strengths or [] if summary else [],
        growth_areas=summary.growth_areas or [] if summary else [],
        criterion_breakdown=summary.criterion_breakdown or [] if summary else [],
        arguments_for=summary.arguments_for or [] if summary else [],
        arguments_against=summary.arguments_against or [] if summary else [],
        needs_attention=summary.needs_attention or [] if summary else [],
        feedbacks=feedbacks_data,
        llm_model=summary.llm_model_version if summary else "—",
    )

    filename = f"summary_{employee.full_name.replace(' ', '_')}_{period.period_name.replace(' ', '_')}.html"
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
