import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet


def make_pdf(data) -> str:
    # Настройка шрифта
    pdfmetrics.registerFont(TTFont("TimesNewRoman", "times.ttf"))
    pdfmetrics.registerFont(TTFont("TimesNewRoman-Bold", "timesbd.ttf"))

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

    # with open("data.json", encoding="utf-8") as f:
    #     data = json.load(f)

    risk_labels = {
        "significant": "Существенный риск",
        "high": "Высокий риск",
        "medium": "Средний риск",
        "low": "Незначительный риск"
    }

    # Создание графиков
    img_dir = Path("pdf_images")
    img_dir.mkdir(exist_ok=True)

    risk_type_df = pd.DataFrame({
        "Тип риска": [risk_labels[k] for k in data["by_risk_type"]],
        "Количество": [v["count"] for v in data["by_risk_type"].values()]
    })
    plt.figure(figsize=(5, 5))
    plt.pie(risk_type_df["Количество"], labels=risk_type_df["Тип риска"],
            colors=["#FF0000", "#FF9900", "#FFFF00", "#66CC66"], startangle=140)
    plt.savefig(img_dir / "risk_pie.png", bbox_inches="tight")
    plt.close()

    category_totals = {k: v["total"] for k, v in data["by_category"].items()}
    plt.figure(figsize=(6, 6))
    plt.pie(category_totals.values(), labels=category_totals.keys(), startangle=140)
    plt.savefig(img_dir / "category_pie.png", bbox_inches="tight")
    plt.close()

    category_df = pd.DataFrame(data["by_category"]).T[["low", "medium", "high"]]
    category_df.plot(kind="bar", stacked=False, figsize=(10, 5),
                    color=["#66CC66", "#FFFF00", "#FF9900"])
    plt.xlabel("Категории")
    plt.ylabel("Количество")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(img_dir / "category_bar.png")
    plt.close()

    # Генерация PDF
    pdf_path = "risk_report.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
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
    img = Image(str(img_dir / "risk_pie.png"))
    img._restrictSize(14 * cm, 10 * cm)
    elements.append(img)
    elements.append(Spacer(1, 1 * cm))
    elements.append(PageBreak())

    # Остальные графики
    charts = [
        ("Распределение по категориям", img_dir / "category_pie.png"),
        ("Распределение рисков по категориям (без существенных рисков)", img_dir / "category_bar.png"),
    ]

    for title, path in charts:
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * cm))
        img = Image(str(path))
        img._restrictSize(14 * cm, 10 * cm)
        elements.append(img)
        elements.append(Spacer(1, 1 * cm))

    # Рекомендации
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
            recs = ", ".join([r.strip() for r in d["recommendations"]])
            block = f"<b>Вопрос:</b> {q}<br/><b>Ответ:</b> {a}<br/><b>Рекомендации:</b> {recs}"
            elements.append(Paragraph(block, styles["Normal"]))
            elements.append(Spacer(1, 0.5 * cm))

    doc.build(elements)
    return pdf_path
