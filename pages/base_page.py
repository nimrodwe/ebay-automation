import re

import allure
from playwright.sync_api import Locator, Page, expect

from utils.config import SCREENSHOTS_DIR
from utils.logger import get_logger


class BasePage:
    URL = ""
    ERROR_PAGE_RETRIES = 2

    def __init__(self, page: Page):
        self.page = page
        self.logger = get_logger(self.__class__.__name__)
        self.gdpr_accept_button = page.locator("#gdpr-banner-accept")
        self.onetrust_accept_button = page.locator("#onetrust-accept-btn-handler")
        self.stay_on_ebay_button = page.get_by_role("button", name="Stay on eBay.com")
        self.maybe_later_button = page.get_by_role("button", name="Maybe later")

    def open(self, url: str | None = None) -> bool:
        url = url or self.URL
        with allure.step(f"Open {url}"):
            self.logger.info(f"Open {url}")
            self.page.goto(url)
            self.reload_error_page()
            self.wait_for_ebay_check()
            if self.captcha_shown():
                self.logger.info(f"eBay asked for a CAPTCHA: {self.page.url}")
                return False
            if "Error Page" in self.page.title():
                self.logger.info(f"eBay kept returning its Error Page for {url}")
                return False
            self.close_popups()
            return True

    def wait_for_ebay_check(self) -> bool:
        if "/splashui/challenge" in self.page.url:
            self.logger.info("eBay is running its automatic check - waiting for it to finish")
            self.page.wait_for_url(lambda current: "/splashui/challenge" not in current)
        return not self.captcha_shown() and "Error Page" not in self.page.title()

    def reload_error_page(self):
        for attempt in range(1, self.ERROR_PAGE_RETRIES + 1):
            if "Error Page" not in self.page.title():
                return
            self.logger.info(f"eBay served an Error Page - retry {attempt}/{self.ERROR_PAGE_RETRIES} in {attempt * 2}s")
            self.page.wait_for_timeout(attempt * 2000)
            self.page.reload()

    def captcha_shown(self) -> bool:
        return "/splashui/captcha" in self.page.url

    def click(self, element: Locator):
        with allure.step(f"Click {element}"):
            self.logger.info(f"Click {element}")
            element.click()

    def click_and_wait(self, element: Locator):
        with self.page.expect_navigation():
            self.click(element)
        self.reload_error_page()
        if not self.wait_for_ebay_check():
            raise RuntimeError(f"eBay did not load the next page: '{self.page.title()}' at {self.page.url}")

    def type_into(self, element: Locator, text: str):
        with allure.step(f"Type into {element}"):
            self.logger.info(f"Type into {element}")
            element.fill(text)

    def check_visible(self, element: Locator, required: bool = False) -> bool:
        try:
            expect(element).to_be_visible()
            return True
        except AssertionError:
            if required:
                self.logger.error(f"Not visible: {element}")
                raise
            return False

    def take_screenshot(self, name: str):
        file_name = re.sub(r"[^\w-]+", "_", name).strip("_")[:80]
        path = SCREENSHOTS_DIR / f"{file_name}.png"
        self.page.screenshot(path=path, full_page=True)
        allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)
        self.logger.info(f"Screenshot '{name}' saved to {path}")

    def close_popups(self):
        for button in (
            self.gdpr_accept_button,
            self.onetrust_accept_button,
            self.stay_on_ebay_button,
            self.maybe_later_button,
        ):
            if button.is_visible():
                self.click(button)

    @staticmethod
    def parse_price(text: str) -> float | None:
        numbers = re.findall(r"\d[\d,]*\.?\d*", text)
        if not numbers:
            return None
        return float(numbers[-1].replace(",", ""))
