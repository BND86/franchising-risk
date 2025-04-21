import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from html import escape

from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet


def make_pdf(data: dict, session_id: str) -> str:
    # Настройка шрифта
    pdfmetrics.registerFont(TTFont("TimesNewRoman", "app/fonts/TIMES.TTF"))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", "app/fonts/TIMESBD.TTF"))

    pdfmetrics.registerFontFamily("TimesNewRoman", normal="TimesNewRoman", bold="TimesNewRoman-Bold")

    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "TimesNewRoman"
    styles["Normal"].fontSize = 14
    styles["Normal"].leading = 18

    styles["Heading1"].fontName = "TimesNewRoman-Bold"
    styles["Heading1"].fontSize = 18
    styles["Heading1"].alignment = TA_CENTER

    styles["Heading2"].fontName = "TimesNewRoman-Bold"
    styles["Heading2"].fontSize = 16
    styles["Heading2"].alignment = TA_CENTER
    styles["Heading2"].leading = 18

    risk_labels = {
        "significant": "Существенный риск",
        "high": "Высокий риск",
        "medium": "Средний риск",
        "low": "Незначительный риск"
    }

    # Создание графиков
    plt.style.use('bmh')

    img_dir = Path("app/temp/pdf_images")
    report_dir = Path("app/temp/pdf_reports")

    img_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    risk_type_df = pd.DataFrame({
        "Тип риска": [risk_labels[k] for k in data["by_risk_type"]],
        "Количество": [v["count"] for v in data["by_risk_type"].values()]
    })
    plt.figure(figsize=(6, 6))
    plt.pie(risk_type_df["Количество"],
            colors=['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71'], startangle=140)
    plt.legend(labels=risk_type_df["Тип риска"], title="Тип риска", loc="center left", bbox_to_anchor=(1, 0.5))
    plt.savefig(img_dir / f"risk_pie_{session_id}.png", bbox_inches="tight")
    plt.close()

    category_totals = {k: v["total"] for k, v in data["by_category"].items()}
    plt.figure(figsize=(6, 6))
    plt.pie(category_totals.values(), startangle=140)
    plt.legend(labels=category_totals.keys(), title="Категория риска", loc="center left", bbox_to_anchor=(1, 0.5))
    plt.savefig(img_dir / f"category_pie_{session_id}.png", bbox_inches="tight")
    plt.close()

    category_df = pd.DataFrame(data["by_category"]).T[["low", "medium", "high"]]

    ax = category_df.plot(kind="bar", stacked=False, figsize=(10, 5),
                        color=['#2ecc71', '#f1c40f', '#e67e22'])

    # Bar labels
    for container in ax.containers:
        ax.bar_label(container, label_type='edge', fontsize=9)

    # Grid and styling
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Labels and title
    plt.xlabel("Категории", fontsize=12)
    plt.ylabel("Количество", fontsize=12)
    plt.title("Распределение уровней риска по категориям", fontsize=14)
    plt.xticks(rotation=45, ha="right", fontsize=10)
    plt.yticks(fontsize=10)

    # Legend
    plt.legend(["Низкий", "Средний", "Высокий"], title="Уровень риска", fontsize=10, title_fontsize=11)

    plt.tight_layout()
    plt.savefig(img_dir / f"category_bar_{session_id}.png")
    plt.close()
    # Генерация PDF
    pdf_path = report_dir / f"risk_report_{session_id}.pdf"
    doc = SimpleDocTemplate(pdf_path.as_posix(), pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    elements = []

    # Заголовок
    elements.append(Paragraph("<b>Анализ рисков</b>", styles["Heading1"]))
    elements.append(Spacer(1, 1 * cm))

    # Таблица по типам риска
    elements.append(Paragraph("Распределение рисков по типам", styles["Heading2"]))
    table_data = [["Тип риска", "Количество"]]
    for key in ["significant", "high", "medium", "low"]:
        label = risk_labels[key]
        count = data["by_risk_type"][key]["count"]
        table_data.append([label, str(count)])

    table = Table(table_data, colWidths=[8 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "TimesNewRoman"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 1 * cm))

    # 1 Страница (таблица и piechart)
    elements.append(Spacer(1, 0.3 * cm))
    img = Image(str(img_dir / f"risk_pie_{session_id}.png"))
    img._restrictSize(14 * cm, 10 * cm)
    elements.append(img)
    elements.append(Spacer(1, 1 * cm))
    elements.append(PageBreak())

    # Остальные графики
    charts = [
        ("Распределение по категориям", img_dir / f"category_pie_{session_id}.png"),
        ("Распределение рисков по категориям (без существенных рисков)", img_dir / f"category_bar_{session_id}.png"),
    ]

    for title, path in charts:
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * cm))
        img = Image(str(path))
        img._restrictSize(14 * cm, 10 * cm)
        elements.append(img)
        elements.append(Spacer(1, 1 * cm))


    # === Итоговый результат оценки рисков ===
    # Цвета
    red = HexColor("#e53935")
    purple = HexColor("#3f51b5")
    light_red_bg = HexColor("#fceaea")

    # Итоги рисков
    significant = data["by_risk_type"]["significant"]["count"]
    high = data["by_risk_type"]["high"]["count"]
    medium = data["by_risk_type"]["medium"]["count"]
    low = data["by_risk_type"]["low"]["count"]
    total_risk = significant + high + medium + low

    elements.append(PageBreak())
    elements.append(Paragraph("Результат оценки рисков", styles["Heading2"]))
    elements.append(Spacer(1, 0.3 * cm))

    # Блок предупреждения
    if significant > 0:
        warning_style = ParagraphStyle(
                name="Warning",
                parent=styles["Normal"],
                textColor=red,
                backColor=light_red_bg,
                borderColor=colors.red,
                fontSize=16,
                leading=16,
                borderWidth=1,
                borderPadding=6,
                spaceBefore=6,
                spaceAfter=6,
            )
        elements.append(Paragraph(
                "<b>Внимание! Договор не может быть заключен, так как отсутствуют существенные условия.</b>",
                warning_style
            ))

    # Определение уровня риска
    if total_risk == 0:
        title = "Риски не обнаружены"
        message = "Договор соответствует установленным критериям безопасности. Нарушений и потенциально опасных положений не выявлено."
    elif high >= 3 or (total_risk > 0 and (high / total_risk) >= 0.4):
        title = "Высокий уровень рисков"
        message = "Количество критичных условий превышает допустимый порог. Договор не соответствует требованиям безопасного заключения."
    elif medium >= 3 or (total_risk > 0 and (medium / total_risk) >= 0.5):
        title = "Значительные риски"
        message = "Условия договора содержат отклонения, требующие дополнительной правовой и экономической проверки."
    elif low == total_risk:
        title = "Незначительные риски"
        message = "Обнаруженные риски не превышают минимального порога. Договор может считаться условно допустимым после устранения выявленных технических замечаний."
    else:
        title = "Смешанный уровень рисков"
        message = "Договор содержит условия различной степени риска. Требуется комплексная правовая и финансовая экспертиза."

    # Стиль заголовка и описания
    summary_style = ParagraphStyle(
        name="Recommendation",
        parent=styles["Normal"],
        backColor=colors.whitesmoke,
        borderColor=colors.blue,
        borderWidth=1,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=6,
        leading=18
        )

    # Обертка в таблицу для рамки и фона
    summary_block = f"<b>{title}</b><br/>{message}"
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(summary_block, summary_style))


    # Рекомендации
    recommendation_style = ParagraphStyle(
    name="Recommendation",
    parent=styles["Normal"],
    backColor=colors.lavender,
    borderColor=colors.purple,
    borderWidth=1,
    borderPadding=6,
    spaceBefore=6,
    spaceAfter=6,
    leading=18
    )

    for level in ["significant", "high", "medium", "low"]:
        details = data["by_risk_type"][level]["details"]
        if not details:
            continue
        elements.append(PageBreak())
        elements.append(Paragraph(risk_labels[level], styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * cm))

        for d in details:
            q = d["question"]
            a = d["answer"]
            recs = d.get("recomendations", [])
            article = d.get("article", [])
            link = d.get("link", [])

            # Вопрос и ответ
            block = f"<b>Вопрос:</b> {escape(q)}<br/><b>Ответ:</b> {escape(a)}"
            elements.append(Paragraph(block, styles["Normal"]))
            elements.append(Spacer(1, 0.3 * cm))

            # Если есть рекомендации
            if recs:
                full_rec_text = ", ".join([r.strip() for r in recs if r and r != "None"])
                if full_rec_text:
                    rec_block = f"<b>Рекомендация</b><br/>{escape(full_rec_text)}"

                    if article and article[0] != "None" and link:
                        full_links = f"<br/><a href='{escape(link[0])}' color='#0000FF'>{article[0]}</a>"
                        rec_block += f"<br/>{full_links}"

                    elements.append(Paragraph(rec_block, recommendation_style))
                    elements.append(Spacer(1, 0.5 * cm))

    doc.build(elements)

    # Удаление временных файлов
    for filename in [f"category_bar_{session_id}.png", f"category_pie_{session_id}.png", f"risk_pie_{session_id}.png"]:
        file_path = img_dir / filename
        try:
            file_path.unlink()
        except Exception as e:
            print(f"Deleting file {file_path}. An error occurred: {e}")
    return pdf_path.as_posix()
