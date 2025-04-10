import json
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pathlib import Path

# === Настройка шрифта Arial ===
pdfmetrics.registerFont(TTFont("Arial", "Arial.ttf"))

# === Загрузка данных ===
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

risk_labels = {
    "significant": "Существенный риск",
    "high": "Высокий риск",
    "medium": "Средний риск",
    "low": "Незначительный риск"
}

# === Создание графиков ===
img_dir = Path("pdf_images")
img_dir.mkdir(exist_ok=True)

risk_type_df = pd.DataFrame({
    "Тип риска": [risk_labels[k] for k in data["by_risk_type"]],
    "Количество": [v["count"] for v in data["by_risk_type"].values()]
})
plt.figure(figsize=(5, 5))
plt.pie(risk_type_df["Количество"], labels=risk_type_df["Тип риска"], autopct="%1.1f%%",
        colors=["#FF0000", "#FF9900", "#FFFF00", "#66CC66"], startangle=140)
plt.title("Распределение рисков по типам")
plt.savefig(img_dir / "risk_pie.png", bbox_inches="tight")
plt.close()

category_totals = {k: v["total"] for k, v in data["by_category"].items()}
plt.figure(figsize=(6, 6))
plt.pie(category_totals.values(), labels=category_totals.keys(), autopct="%1.1f%%", startangle=140)
plt.title("Распределение рисков по категориям")
plt.savefig(img_dir / "category_pie.png", bbox_inches="tight")
plt.close()

category_df = pd.DataFrame(data["by_category"]).T[["low", "medium", "high"]]
category_df.plot(kind="bar", stacked=False, figsize=(10, 5),
                 color=["#66CC66", "#FFFF00", "#FF9900"])
plt.title("Распределение по категориям (без существенных рисков)")
plt.xlabel("Категории")
plt.ylabel("Количество")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig(img_dir / "category_bar.png")
plt.close()

# === Генерация PDF ===
pdf_path = "risk_report.pdf"
c = canvas.Canvas(pdf_path, pagesize=A4)
width, height = A4
margin = 2 * cm
y = height - margin

c.setFont("Arial", 16)
c.drawString(margin, y, "Анализ рисков по данным")
y -= 1.5 * cm

# Вставка графиков
for title, path in [
    ("Распределение рисков по типам", "risk_pie.png"),
    ("Распределение по категориям", "category_pie.png"),
    ("Категории без существенных рисков", "category_bar.png")
]:
    c.setFont("Arial", 12)
    c.drawString(margin, y, title)
    y -= 0.5 * cm
    c.drawImage(str(img_dir / path), margin, y - 8 * cm, width=16 * cm, height=8 * cm)
    y -= 9 * cm
    if y < margin + 10 * cm:
        c.showPage()
        y = height - margin

# Вставка рекомендаций
for level in ["significant", "high", "medium", "low"]:
    details = data["by_risk_type"][level]["details"]
    if not details:
        continue
    c.setFont("Arial", 14)
    c.drawString(margin, y, f"{risk_labels[level]}:")
    y -= 1 * cm
    c.setFont("Arial", 10)
    for d in details:
        text = f"Вопрос: {d['question']}\nОтвет: {d['answer']}\nРекомендации: {', '.join([r.strip() for r in d['recommendations']])}"
        for line in text.split("\n"):
            if y < margin + 2 * cm:
                c.showPage()
                y = height - margin
                c.setFont("Arial", 10)
            c.drawString(margin, y, line)
            y -= 0.5 * cm
        y -= 0.5 * cm

c.save()
print(f"PDF-файл сохранён как: {pdf_path}")
