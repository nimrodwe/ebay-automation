import allure
import pytest
from playwright.sync_api import sync_playwright

from utils.config import HEADLESS, TRACES_DIR, get_credentials


@pytest.fixture
def credentials():
    return get_credentials()


@pytest.fixture
def page(request):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        context.tracing.start(screenshots=True, snapshots=True)
        page = context.new_page()
        console_messages = []
        page.on("console", lambda message: console_messages.append(f"[{message.type}] {message.text}"))
        request.node.console_messages = console_messages

        yield page

        if getattr(request.node, "test_failed", True):
            trace_path = TRACES_DIR / f"{request.node.name}.zip"
            context.tracing.stop(path=trace_path)
            allure.attach.file(trace_path, name="playwright trace", extension="zip")
        else:
            context.tracing.stop()
        browser.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    item.test_failed = report.failed
    page = item.funcargs.get("page")
    if page is None:
        return
    page = page.context.pages[-1]
    page.bring_to_front()
    status = "failed" if report.failed else "passed"
    allure.attach(
        page.screenshot(full_page=True),
        name=f"screenshot - {status}",
        attachment_type=allure.attachment_type.PNG,
    )
    console = getattr(item, "console_messages", []) or ["no browser console messages"]
    allure.attach(
        "\n".join([f"page: {page.url}", *console]),
        name=f"browser log - {status}",
        attachment_type=allure.attachment_type.TEXT,
    )


@pytest.hookimpl(tryfirst=True)
def pytest_report_teststatus(report):
    if report.outcome == "rerun":
        return "", "", ""
