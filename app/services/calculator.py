import math

# Константы для нормализации данных
TRAFFIC_CONSTANTS = {
    'PEDESTRIAN': {'MAX': 300000, 'MIN': 500, 'AVG': 150000},    # 300 тыс / 1 тыс человек в день
    'CAR': {'MAX': 500000, 'MIN': 1000, 'AVG': 250000},          # 500 тыс / 1 тыс машин в день
    'QUERIES': {'MAX': 1500000, 'MIN': 1000, 'AVG': 750000}     # 1.5 млн / 100 тыс запросов
}

# Финансовые константы
FINANCIAL_CONSTANTS = {
    'MONTHS_IN_YEAR': 12,
    'INVESTMENT': {'AVG': 3000000, 'DISP': 2000000}, #стартовые инвестиции
    'ROYALTY': {'AVG': 3.6, 'DISP': 1.0}, #роялти
    'PAY_PERIOD': {'AVG': 10, 'DISP': 4}, #период окупаемости (мес)
    'TURNOVER': {'AVG': 1800000, 'DISP': 1000000}, #оборот в месяц
    'PAYMENT': {'AVG': 500000, 'DISP': 150000}, #паушальный взнос
    'ATTRACTIVENESS_WEIGHTS': {'PEDESTRIAN': 0.8, 'CAR': 0.2},
    'RISK_WEIGHTS': {
        'high_start_investment': 0.1,
        'high_operational_expenses': 0.2,
        'cash_flow_instability': 0.5,
        'franchisor_dependence': 0.2
    }
}

def normalize(value, min_val, max_val):
    """Нормализация значения в диапазон [0, 1]"""
    if max_val <= min_val:
        return 0
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))

def calculate_annual_revenue(monthly_turnover):
    """Расчет годовой выручки"""
    return monthly_turnover * FINANCIAL_CONSTANTS['MONTHS_IN_YEAR']

def calculate_ebitda(annual_revenue, operational_expenses_percent):
    """Расчет EBITDA (прибыль до вычета налогов, процентов и амортизации)"""
    operational_expenses_amount = annual_revenue * (operational_expenses_percent / 100)
    return annual_revenue - operational_expenses_amount

def calculate_mandatory_payments(annual_revenue, royalty_percent, additional_payments_percent):
    """Расчет обязательных платежей (роялти + дополнительные платежи)"""
    royalty = annual_revenue * (royalty_percent / 100)
    additional_payments = annual_revenue * (additional_payments_percent / 100)
    return royalty + additional_payments

def sigmoid_risk(value, mean, deviation, inverse=False):
    if deviation == 0:
        return 0.5  # Если отклонение нулевое, считаем нейтральным
    
    normalized_diff = (value - mean) / deviation
    if inverse:
        normalized_diff = -normalized_diff  # Инвертируем для случаев, где меньше = рискованнее
    
    risk = 1 / (1 + math.exp(-normalized_diff))
    return risk

def calculate_operational_expenses(monthly_turnover, royalty_percent, lump_sum_fee, payback_period, operational_expenses_percent):
    """
    Расчет операционных расходов:
    - Основные операционные расходы = процент от оборота
    - Роялти = процент от оборота
    - Паушальный взнос = размазанный на срок окупаемости
    """
    annual_revenue = calculate_annual_revenue(monthly_turnover)
    main_operational_expenses = annual_revenue * (operational_expenses_percent / 100) / FINANCIAL_CONSTANTS['MONTHS_IN_YEAR']
    royalty_expense = monthly_turnover * (royalty_percent / 100)
    lump_sum_monthly = lump_sum_fee / max(1, payback_period)  # Защита от деления на 0
    return main_operational_expenses + royalty_expense + lump_sum_monthly

def calculate_risk_factors(input_data):
    # Фиксированное среднее значение для операционных расходов (30%)
    mean_operational_expenses = (
        FINANCIAL_CONSTANTS['TURNOVER']['AVG'] * (FINANCIAL_CONSTANTS['ROYALTY']['AVG'] / 100) +
        FINANCIAL_CONSTANTS['PAYMENT']['AVG'] / FINANCIAL_CONSTANTS['PAY_PERIOD']['AVG'] +
        FINANCIAL_CONSTANTS['TURNOVER']['AVG'] * 0.3  # 30% от среднего оборота
    )

    # Рассчитываем operational_expenses
    operational_expenses = calculate_operational_expenses(
        monthly_turnover=input_data["monthly_turnover"],
        royalty_percent=input_data["royalty_percent"],
        lump_sum_fee=input_data.get("franchise_fee", FINANCIAL_CONSTANTS['PAYMENT']['AVG']),
        payback_period=input_data.get("payback_period", FINANCIAL_CONSTANTS['PAY_PERIOD']['AVG']),
        operational_expenses_percent=input_data["operational_expenses"]
    )

    # Оцениваем риски
    risk_factors = {
        "high_start_investment": sigmoid_risk(
            input_data["start_investment"],
            FINANCIAL_CONSTANTS['INVESTMENT']['AVG'],
            FINANCIAL_CONSTANTS['INVESTMENT']['DISP']
        ),
        "high_operational_expenses": sigmoid_risk(
            operational_expenses,
            mean_operational_expenses,  # Фиксированное среднее
            FINANCIAL_CONSTANTS['TURNOVER']['DISP'] * 0.5  # Примерное отклонение
        ),
        "cash_flow_instability": sigmoid_risk(
            input_data["monthly_turnover"],
            FINANCIAL_CONSTANTS['TURNOVER']['AVG'],
            FINANCIAL_CONSTANTS['TURNOVER']['DISP'],
            inverse=True
        ),
        "franchisor_dependence": sigmoid_risk(
            input_data["royalty_percent"],
            FINANCIAL_CONSTANTS['ROYALTY']['AVG'],
            FINANCIAL_CONSTANTS['ROYALTY']['DISP']
        )
    }
    return risk_factors

def calculate_total_risk(risk_factors):
    """Общий риск как взвешенная сумма факторов."""
    total = 0.0
    weights = FINANCIAL_CONSTANTS['RISK_WEIGHTS']
    
    for factor, risk in risk_factors.items():
        total += risk * weights.get(factor, 0)
    
    return max(0.0, min(1.0, total))

def calculate_attractiveness_index(input_data):
    """Улучшенный расчёт индекса привлекательности локации"""
    pedestrian_norm = normalize(
        input_data["pedestrian_traffic"], 
        TRAFFIC_CONSTANTS['PEDESTRIAN']['MIN'], 
        TRAFFIC_CONSTANTS['PEDESTRIAN']['MAX']
    )

    car_norm = normalize(
        input_data["car_traffic"], 
        TRAFFIC_CONSTANTS['CAR']['MIN'],
        TRAFFIC_CONSTANTS['CAR']['MAX']
    )

    queries_norm = normalize(
        input_data["search_queries"], 
        TRAFFIC_CONSTANTS['QUERIES']['MIN'], 
        TRAFFIC_CONSTANTS['QUERIES']['MAX']
    )

    traffic_score = (
        FINANCIAL_CONSTANTS['ATTRACTIVENESS_WEIGHTS']['PEDESTRIAN'] * pedestrian_norm +
        FINANCIAL_CONSTANTS['ATTRACTIVENESS_WEIGHTS']['CAR'] * car_norm
    )

    competition_raw = 1 - math.log1p(input_data["competitors_count"]) / 10
    competition_factor = max(0.1, min(1.0, competition_raw))
    if input_data["competitors_count"]>=400:
        competition_factor = 0.1
    elif input_data["competitors_count"]<=10:
        competition_factor = 1

    index = traffic_score * queries_norm * competition_factor * 300

    return index

def calculate_results(input_data):
    """Основная функция расчета всех показателей"""
    # Финансовые расчеты
    annual_revenue = calculate_annual_revenue(input_data["monthly_turnover"])
    ebitda = calculate_ebitda(annual_revenue, input_data["operational_expenses"])
    mandatory_payments = calculate_mandatory_payments(
        annual_revenue,
        input_data["royalty_percent"],
        input_data["additional_payments"]
    )
    net_income = ebitda - mandatory_payments
    
    # Оценка рисков
    risk_factors = calculate_risk_factors(input_data)
    total_risk = calculate_total_risk(risk_factors)*10
    
    # Геоаналитика
    attractiveness_index = calculate_attractiveness_index(input_data)
    
    return {
        "finance": {
            "ebitda": round(ebitda, 2),
            "net_income": round(net_income, 2),
            "annual_revenue": round(annual_revenue, 2),
            "mandatory_payments": round(mandatory_payments, 2),
            "operational_expenses_amount": round(annual_revenue * (input_data["operational_expenses"] / 100), 2),
            "additional_payments_amount": round(annual_revenue * (input_data["additional_payments"] / 100), 2)
        },
        "risk": {
            "total_risk": round(total_risk, 2),
            "risk_factors": {k: round(v, 2) for k, v in risk_factors.items()},
        },
        "geo": {
            "attractiveness_index": round(attractiveness_index, 4),
        },
        "input_data": input_data,
    }