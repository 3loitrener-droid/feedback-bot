"""Seed: creates demo users, team, employees, active period, and full criteria matrix."""
import asyncio
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.user import User, Team
from app.models.employee import Employee, ManagerEmployeeVisibility
from app.models.criteria import CriteriaMatrix
from app.models.period import Period

CRITERIA_DATA = [
    {
        "criterion_name": "Эффективный администратор",
        "below_description": "Теряет задачи, не отслеживает выполнение, meetings без результата, артефакты не создаются или создаются некачественно.",
        "meet_description": "Отслеживает задачи и дедлайны, встречи эффективны, базовые артефакты создаются вовремя.",
        "exceeds_description": "Выстраивает системы трекинга на команду, минимизирует административный overhead, артефакты высокого качества, встречи — образцовые по структуре.",
        "is_key_criterion": False, "weight": 1.0, "sort_order": 1,
    },
    {
        "criterion_name": "Адепт эффективного внедрения ИИ",
        "below_description": "Не использует ИИ-инструменты или использует их неэффективно, не экспериментирует с новыми инструментами.",
        "meet_description": "Регулярно использует ИИ-инструменты для повышения продуктивности, делится лучшими практиками.",
        "exceeds_description": "Системно внедряет ИИ в процессы команды, измеряет и демонстрирует impact, является ролевой моделью для других.",
        "is_key_criterion": False, "weight": 1.0, "sort_order": 2,
    },
    {
        "criterion_name": "Персональные качества",
        "below_description": "Демонстрирует поведение, которое вредит команде: избегает конфликтов, нечестен, не выполняет обязательства.",
        "meet_description": "Честен, держит слово, работает конструктивно, принимает критику.",
        "exceeds_description": "Является ролевой моделью по ценностям, создаёт психологическую безопасность, открыто говорит о проблемах и ошибках.",
        "is_key_criterion": False, "weight": 1.2, "sort_order": 3,
    },
    {
        "criterion_name": "Принимает решения как ко-фаундер",
        "below_description": "Принимает решения только в рамках своей области, избегает ответственности за компанию в целом.",
        "meet_description": "Думает о влиянии решений на бизнес за пределами своей области, участвует в стратегических дискуссиях.",
        "exceeds_description": "Инициирует важные решения на уровне компании, берёт ответственность за результат, мыслит как собственник.",
        "is_key_criterion": True, "weight": 1.5, "sort_order": 4,
    },
    {
        "criterion_name": "Маркетирование продукта",
        "below_description": "Не занимается продвижением продукта, нет понимания целевой аудитории и каналов.",
        "meet_description": "Участвует в создании маркетинговых материалов, понимает аудиторию, работает с командой маркетинга.",
        "exceeds_description": "Системно выстраивает go-to-market стратегию, самостоятельно создаёт demand, измеряет результат.",
        "is_key_criterion": False, "weight": 1.0, "sort_order": 5,
    },
    {
        "criterion_name": "Продукт для клиента",
        "below_description": "Решения принимаются без учёта клиентских потребностей, нет регулярного исследования пользователей.",
        "meet_description": "Регулярно общается с клиентами, принимает решения на основе данных и feedback.",
        "exceeds_description": "Выстраивает систему постоянного изучения клиента, приносит инсайты, которые меняют стратегию продукта.",
        "is_key_criterion": True, "weight": 1.4, "sort_order": 6,
    },
    {
        "criterion_name": "Сколачивание сильной команды",
        "below_description": "Не занимается развитием людей, высокая текучка, команда не растёт в компетенциях.",
        "meet_description": "Нанимает хороших людей, проводит 1:1, работает над развитием сотрудников.",
        "exceeds_description": "Строит команду A-players, создаёт среду для роста, люди в команде продвигаются на более высокие роли.",
        "is_key_criterion": True, "weight": 1.4, "sort_order": 7,
    },
    {
        "criterion_name": "Визионерство",
        "below_description": "Нет чёткого видения направления, реагирует на события вместо того, чтобы их создавать.",
        "meet_description": "Формулирует понятное видение для команды, согласует его с компанией.",
        "exceeds_description": "Создаёт убедительное видение, которое вдохновляет команду и стейкхолдеров, способен защитить его на уровне компании.",
        "is_key_criterion": False, "weight": 1.2, "sort_order": 8,
    },
    {
        "criterion_name": "Концептуальное мышление",
        "below_description": "Работает с задачами тактически, не видит паттернов и системных связей.",
        "meet_description": "Выявляет паттерны, умеет обобщать, формулирует концепции для объяснения сложных явлений.",
        "exceeds_description": "Создаёт концептуальные фреймворки, которые команда использует для принятия решений, влияет на мышление всей организации.",
        "is_key_criterion": False, "weight": 1.0, "sort_order": 9,
    },
    {
        "criterion_name": "Ясность стратегии",
        "below_description": "Стратегия размыта или отсутствует, команда не понимает приоритетов.",
        "meet_description": "Стратегия сформулирована, команда понимает направление и приоритеты.",
        "exceeds_description": "Стратегия кристально ясна, согласована с компанией, регулярно коммуницируется, адаптируется на основе данных.",
        "is_key_criterion": True, "weight": 1.3, "sort_order": 10,
    },
    {
        "criterion_name": "Качество приоритизации",
        "below_description": "Берётся за всё сразу, не умеет отказывать, фокус размыт.",
        "meet_description": "Приоритизирует задачи на основе impact, говорит «нет» неприоритетному.",
        "exceeds_description": "Приоритизация системная, основана на данных, прозрачна для команды и стейкхолдеров, обновляется регулярно.",
        "is_key_criterion": True, "weight": 1.3, "sort_order": 11,
    },
    {
        "criterion_name": "Выполнение продуктовых OKR",
        "below_description": "OKR регулярно не выполняются, нет анализа причин.",
        "meet_description": "OKR выполняются на уровне 70-90%, анализирует причины отклонений.",
        "exceeds_description": "OKR выполняются стабильно, команда понимает связь своих задач с OKR, результаты измеримо влияют на бизнес.",
        "is_key_criterion": True, "weight": 1.5, "sort_order": 12,
    },
    {
        "criterion_name": "Предсказуемость execution",
        "below_description": "Дедлайны регулярно срываются, риски подсвечиваются поздно, план-факт расходится системно.",
        "meet_description": "Основные дедлайны выдерживаются, риски коммуницируются заблаговременно, отклонения объясняются.",
        "exceeds_description": "Дедлайны выдерживаются стабильно, риски подсвечиваются и управляются проактивно, план-факт прозрачен для всех стейкхолдеров.",
        "is_key_criterion": True, "weight": 1.5, "sort_order": 13,
    },
    {
        "criterion_name": "Зрелость процессов и функции",
        "below_description": "Процессы хаотичны, нет повторяемости, каждая задача решается заново.",
        "meet_description": "Основные процессы задокументированы и работают, команда следует им.",
        "exceeds_description": "Процессы масштабируемы, постоянно улучшаются, служат примером для других функций.",
        "is_key_criterion": False, "weight": 1.1, "sort_order": 14,
    },
    {
        "criterion_name": "Работа со стейкхолдерами",
        "below_description": "Плохо управляет ожиданиями стейкхолдеров, встречи проходят неэффективно, нет проактивной коммуникации.",
        "meet_description": "Регулярно коммуницирует со стейкхолдерами, управляет ожиданиями, приходит на встречи подготовленным.",
        "exceeds_description": "Выстраивает доверительные отношения со стейкхолдерами, управляет сложными ситуациями, является связующим звеном.",
        "is_key_criterion": True, "weight": 1.3, "sort_order": 15,
    },
    {
        "criterion_name": "Ответственность",
        "below_description": "Избегает ответственности, ищет внешние причины провалов, не доводит до конца.",
        "meet_description": "Берёт ответственность за результат своей области, признаёт ошибки, исправляет их.",
        "exceeds_description": "Берёт ответственность выше своего уровня, создаёт культуру ответственности в команде.",
        "is_key_criterion": True, "weight": 1.4, "sort_order": 16,
    },
    {
        "criterion_name": "Фокусы",
        "below_description": "Нет чётких фокусов на период, внимание распылено по множеству направлений.",
        "meet_description": "Определены 2-3 фокуса на квартал, команда знает о них, прогресс отслеживается.",
        "exceeds_description": "Фокусы чёткие, измеримые, согласованы с компанией, регулярно коммуницируются, прогресс виден.",
        "is_key_criterion": False, "weight": 1.1, "sort_order": 17,
    },
    {
        "criterion_name": "Артефакты",
        "below_description": "Артефакты создаются нерегулярно, низкого качества или отсутствуют, нет структуры.",
        "meet_description": "Ключевые артефакты создаются вовремя, качество достаточное для принятия решений.",
        "exceeds_description": "Артефакты высокого качества, структурированы, используются командой и стейкхолдерами как референс.",
        "is_key_criterion": False, "weight": 1.0, "sort_order": 18,
    },
]

DEMO_USERS = [
    {"full_name": "Алексей Смирнов", "email": "alexey@company.com", "role": "manager"},
    {"full_name": "Мария Иванова", "email": "maria@company.com", "role": "hrbp"},
    {"full_name": "Дмитрий Козлов", "email": "dmitry@company.com", "role": "admin"},
]

DEMO_EMPLOYEES = [
    {"full_name": "Иванов Иван", "position": "Senior Product Manager", "level": "Senior"},
    {"full_name": "Петрова Мария", "position": "Product Manager", "level": "Middle"},
    {"full_name": "Сидоров Алексей", "position": "Product Manager", "level": "Middle"},
    {"full_name": "Козлова Елена", "position": "Junior PM", "level": "Junior"},
]


async def run_seed(db: AsyncSession):
    """Seed called from within an existing session (e.g. from startup event)."""
    team = Team(team_id=uuid.uuid4(), team_name="Product Team")
    db.add(team)
    await db.flush()

    users = []
    for u_data in DEMO_USERS:
        user = User(user_id=uuid.uuid4(), team_id=team.team_id, **u_data)
        db.add(user)
        users.append(user)
    await db.flush()

    manager = users[0]

    for e_data in DEMO_EMPLOYEES:
        emp = Employee(
            employee_id=uuid.uuid4(),
            team_id=team.team_id,
            manager_id=manager.user_id,
            status="active",
            **e_data,
        )
        db.add(emp)
        vis = ManagerEmployeeVisibility(
            manager_id=manager.user_id,
            employee_id=emp.employee_id,
            granted_by=users[2].user_id,
        )
        db.add(vis)

    for c_data in CRITERIA_DATA:
        db.add(CriteriaMatrix(criterion_id=uuid.uuid4(), is_active=True, **c_data))

    db.add(Period(
        period_id=uuid.uuid4(),
        period_name="Q2 2026",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 6, 30),
        is_active=True,
    ))

    await db.commit()


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(CriteriaMatrix).limit(1))
        if existing.scalar_one_or_none():
            print("[seed] Already seeded, skipping.")
            return
        print("[seed] Seeding database...")
        await run_seed(db)
        print(f"[seed] Done! {len(DEMO_USERS)} users, {len(DEMO_EMPLOYEES)} employees, {len(CRITERIA_DATA)} criteria.")
        print("\nDemo credentials:")
        for u in DEMO_USERS:
            print(f"  {u['role']:10} | {u['email']}")


if __name__ == "__main__":
    asyncio.run(seed())
