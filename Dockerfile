# מתחילים מ-image רשמי של Python 3.11 — גרסה קלה (slim)
FROM python:3.11-slim

# מגדירים את תיקיית העבודה בתוך ה-container
WORKDIR /app

# מעתיקים קודם רק את requirements.txt
# למה? כי Docker שומר cache לכל שלב — אם הקוד השתנה אבל
# הדפנדנסיז לא, Docker לא יריץ pip install מחדש
COPY requirements.txt .

# מתקינים את כל הספריות
RUN pip install --no-cache-dir -r requirements.txt

# עכשיו מעתיקים את שאר הקוד
COPY . .

# פותחים פורט 8000 לתקשורת עם העולם החיצוני
EXPOSE 8000

# הפקודה שרצה כשה-container עולה
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]