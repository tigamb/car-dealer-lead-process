
import re
from typing import Optional
from src.models import BranchInfo, CarInfo
from src.logger import get_logger

logger = get_logger("file_loader")


DEFAULT_BRANCH = BranchInfo(
    branch_id="400",
    name="Default Showroom",
    manager="General Manager",
    region="Center",
)



#========================================================================
#
#========================================================================
def load_branch_config(path: str) -> dict[str, BranchInfo]:
    """
    קורא את branch_config.xlsx ומחזיר dict עם key=branch_id.
    במקרה של שגיאה — מחזיר את ברירת המחדל.
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active

        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise ValueError("Excel file is empty")

        # שורה ראשונה = headers — ממפה שם עמודה למיקום שלה
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]

        def col(name: str) -> int:
            """מחזיר את האינדקס של עמודה לפי שמה"""
            return headers.index(name)

        branches: dict[str, BranchInfo] = {}

        for row in rows[1:]:  # מדלג על שורת ה-headers
            if not any(row):  # שורה ריקה — מדלג
                continue
            try:
                branch_id = str(row[col("BranchID")]).strip()
                branch = BranchInfo(
                    branch_id=branch_id,
                    name=str(row[col("Name")]).strip(),
                    manager=str(row[col("Manager")]).strip(),
                    region=str(row[col("Region")]).strip(),
                )
                branches[branch_id] = branch
            except (IndexError, ValueError) as e:
                logger.warning("Skipping malformed branch row", row=row, error=str(e))

        logger.info("Branch config loaded", count=len(branches), path=path)
        return branches

    except Exception as e:
        logger.error("Failed to load branch config", path=path, error=str(e))
        return {DEFAULT_BRANCH.branch_id: DEFAULT_BRANCH}
    

#========================================================================
#
#========================================================================
def parse_car_models(path: str) -> dict[str, CarInfo]:
    """
    קורא את car_models.txt ומחזיר dict עם key=model_id.
    הקובץ בנוי מבלוקים — כל בלוק = רכב אחד, מופרד בקווים.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        cars: dict[str, CarInfo] = {}

        # מפצל את הקובץ לבלוקים לפי שורות של מקפים
        blocks = re.split(r"-{10,}", content)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # מחלץ key:value מכל שורה בבלוק
            data: dict[str, str] = {}
            for line in block.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    data[key.strip()] = value.strip()

            # אם אין Model ID — זה לא בלוק של רכב (למשל כותרת)
            model_id = data.get("Model ID", "")
            if not model_id:
                continue

            cars[model_id] = CarInfo(
                model_id=model_id,
                model_name=data.get("Model", "Unknown"),
                category=data.get("Category", "Unknown"),
                price_range=data.get("Price Range", "N/A"),
                availability=data.get("Availability", "Unknown"),
            )

        logger.info("Car models loaded", count=len(cars), path=path)
        return cars

    except Exception as e:
        logger.error("Failed to load car models", path=path, error=str(e))
        return {}    



#========================================================================
#
#========================================================================
def get_branch_info(branches: dict[str, BranchInfo], branch_id: str) -> BranchInfo:
    """
    מחפש סניף לפי ID.
    אם לא נמצא — מחזיר branch 400 כברירת מחדל.
    """
    if branch_id in branches:
        return branches[branch_id]

    fallback = branches.get("400", DEFAULT_BRANCH)
    logger.warning(
        "BranchID not found, using fallback",
        requested=branch_id,
        fallback=fallback.branch_id,
    )
    return fallback


def get_car_info(cars: dict[str, CarInfo], model_id: str) -> Optional[CarInfo]:
    """
    מחפש רכב לפי model ID.
    מחזיר None אם לא נמצא — הפייפליין ממשיך עם car_info=null.
    """
    return cars.get(model_id)
