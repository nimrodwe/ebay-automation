<div dir="rtl">

# ניתוח באגים בקוד שנכתב בעזרת AI

## הקוד המקורי

</div>

```python
from playwright.sync_api import sync_playwright
from selenium import webdriver
import time

def test_search_functionality():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")

    time.sleep(2)

    search_box = page.locator("#search")
    search_box.fill("playwright testing")

    page.locator(".button").click()

    time.sleep(3)

    results = page.locator(".result-item")

    browser.close()
```

---

<div dir="rtl">

## בעיה 1: אין בדיקה (Assertion) בכלל

### השורה הבעייתית

</div>

```python
results = page.locator(".result-item")
```

<div dir="rtl">

### מה הבעיה

בבדיקה אין אף שורת בדיקה, ולכן היא לא בודקת כלום.

השורה הזו לא מחפשת את האלמנט בדף. היא רק יוצרת Locator, כלומר "מצביע" שמחכה לשימוש, ובקוד הזה לא משתמשים בו.

### ההשפעה

גם אם החיפוש מחזיר אפס תוצאות, או שהדף מציג שגיאה, הבדיקה תעבור בהצלחה.

זה נקרא False Positive: בדיקה ירוקה שלא מוכיחה שהפיצ'ר עובד, ונותנת ביטחון מזויף.

### התיקון

להוסיף בדיקה שהתוצאות באמת מופיעות. הפונקציה expect של Playwright גם מחכה אוטומטית עד שהתוצאות נטענות, ורק אז בודקת:

</div>

```python
results = page.locator(".result-item")
expect(results.first).to_be_visible()
expect(results).not_to_have_count(0)
```

---

<div dir="rtl">

## בעיה 2: המתנה קבועה במקום המתנה חכמה

### השורות הבעייתיות

</div>

```python
time.sleep(2)
time.sleep(3)
```

<div dir="rtl">

### מה הבעיה

המתנה של מספר שניות קבוע לא קשורה למה שקורה באמת בדף. הקוד לא יודע אם הדף נטען, הוא פשוט מנחש.

### ההשפעה

- **כשהשרת איטי** (למשל בסביבת CI עמוסה): שתי שניות לא מספיקות, האלמנט עוד לא קיים, והבדיקה נכשלת סתם. זו בדיקה לא יציבה, Flaky Test.
- **כשהשרת מהיר:** הבדיקה מחכה חמש שניות לחינם בכל ריצה. על מאות בדיקות זה מצטבר לדקות של זמן מבוזבז.

בנוסף, Playwright כבר מחכה לבד. הפעולות fill ו-click מחכות עד שהאלמנט מוכן ללחיצה, כך שההמתנה מיותרת לגמרי.

### התיקון

למחוק את שתי שורות ההמתנה ואת ה-import של time. אם צריך לחכות למשהו, מחכים לתנאי ולא לזמן:

</div>

```python
expect(results.first).to_be_visible()
```

---

<div dir="rtl">

## בעיה 3: Playwright נפתח ולא נסגר

### השורה הבעייתית

</div>

```python
browser = sync_playwright().start().chromium.launch()
```

<div dir="rtl">

### מה הבעיה

הפקודה start מפעילה תהליך של Playwright ברקע, וצריך לסגור אותו בסוף עם stop.

כאן האובייקט לא נשמר במשתנה, ולכן אין שום דרך לסגור אותו. הפקודה browser.close סוגרת רק את הדפדפן, לא את Playwright עצמו.

בנוסף, אם הבדיקה נכשלת באמצע, הקוד לא מגיע לשורה של browser.close בכלל, והדפדפן נשאר פתוח.

### ההשפעה

כשמריצים הרבה בדיקות, נשארים ברקע תהליכים "יתומים" שתופסים זיכרון (Resource Leak). זה יכול גם לגרום לשגיאות בבדיקה הבאה שרצה.

### התיקון

להשתמש ב-with, שסוגר הכל אוטומטית בסוף, גם כשיש שגיאה:

</div>

```python
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    ...
    browser.close()
```

<div dir="rtl">

עדיף עוד יותר להעביר את הפתיחה והסגירה ל-fixture בקובץ conftest, כך שכל בדיקה תקבל דף מוכן. כך עשינו בפרויקט הזה.

</div>

---

<div dir="rtl">

## בעיה 4: ייבוא של Selenium שלא בשימוש

### השורה הבעייתית

</div>

```python
from selenium import webdriver
```

<div dir="rtl">

### מה הבעיה

כל הקוד כתוב ב-Playwright, ו-webdriver לא בשימוש באף מקום. זה סימן טיפוסי לקוד שנכתב ב-AI ומערבב שתי ספריות שונות.

### ההשפעה

- **אם Selenium לא מותקן** בסביבה (למשל ב-CI), הקובץ נופל כבר בשורה הראשונה עם שגיאת ModuleNotFoundError, והבדיקה לא רצה בכלל.
- **גם אם הוא מותקן**, זו תלות מיותרת שמבלבלת את מי שקורא את הקוד.

### התיקון

למחוק את השורה.

</div>

---

<div dir="rtl">

## בעיה 5: Locators שבירים

### השורות הבעייתיות

</div>

```python
page.locator(".button").click()
results = page.locator(".result-item")
```

<div dir="rtl">

### מה הבעיה

הסלקטור button. הוא class כללי מאוד, וכנראה יש בדף כמה כפתורים איתו.

בנוסף, class הוא פרט של עיצוב. מפתח שמשנה את העיצוב ישבור את הבדיקה, למרות שהפיצ'ר עצמו עובד.

### ההשפעה

ב-Playwright, אם Locator מוצא יותר מאלמנט אחד, הלחיצה נכשלת עם השגיאה הבאה:

</div>

```text
strict mode violation: locator(".button") resolved to N elements
```

<div dir="rtl">

### התיקון

להשתמש ב-Locators ש-Playwright ממליץ עליהם, לפי מה שהמשתמש רואה בדף (תפקיד ושם), או לפי ID אם יש:

</div>

```python
page.get_by_role("button", name="Search").click()
```

---

<div dir="rtl">

## הקוד המתוקן

</div>

```python
from playwright.sync_api import sync_playwright, expect


def test_search_functionality():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")

        page.locator("#search").fill("playwright testing")
        page.get_by_role("button", name="Search").click()

        results = page.locator(".result-item")
        expect(results.first).to_be_visible()
        expect(results).not_to_have_count(0)

        browser.close()
```

---

<div dir="rtl">

## סיכום

| # | הבעיה | ההשפעה | התיקון |
|---|-------|--------|--------|
| 1 | אין בדיקה | הבדיקה תמיד עוברת | הוספת expect |
| 2 | המתנה קבועה | בדיקה לא יציבה ואיטית | המתנה לתנאי |
| 3 | Playwright לא נסגר | דליפת משאבים | שימוש ב-with או fixture |
| 4 | ייבוא של Selenium | קריסה אם לא מותקן | מחיקת השורה |
| 5 | Locators כלליים | נשבר בשינוי עיצוב | get_by_role או ID |

</div>
