import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config import BASE_URL, Credentials


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Login page")
class LoginPage(BasePage):
    URL = "https://signin.ebay.com/signin/"
    captcha_seen = False

    def __init__(self, page: Page):
        super().__init__(page)
        self.username = page.locator("#userid")
        self.continue_button = page.locator("#signin-continue-btn")
        self.password = page.locator("#pass")
        self.sign_in_button = page.locator("#sgnBt")
        self.error_message = page.locator("#errmsg")
        self.sign_in_link = page.get_by_role("link", name="Sign in", exact=True)
        self.captcha_frame = page.get_by_title("hCaptcha security challenge")

    @allure.step("Sign in to eBay")
    def login(self, credentials: Credentials | None) -> bool:
        if credentials is None:
            self.logger.info("No credentials in .env - continuing as guest")
            return self.continue_as_guest()
        if LoginPage.captcha_seen:
            self.logger.info("eBay showed a CAPTCHA earlier in this run - skipping sign-in, continuing as guest")
            return self.continue_as_guest()
        if self.sign_in(credentials):
            return True
        self.logger.info("Sign-in did not complete - continuing as guest")
        return self.continue_as_guest()

    def sign_in(self, credentials: Credentials) -> bool:
        if not self.open():
            self.logger.info("eBay did not show the sign-in page")
            self.captcha_visible()
            return False
        self.type_into(self.username, credentials.username)
        self.click(self.continue_button)
        if not self.check_visible(self.password):
            self.logger.info("Password box did not show up")
            self.captcha_visible()
            return False
        self.type_into(self.password, credentials.password)
        self.click(self.sign_in_button)
        if self.captcha_visible():
            return False
        if self.check_visible(self.error_message):
            self.logger.info(f"eBay login failed: {self.error_message.inner_text()}")
            return False
        self.logger.info(f"Signed in as {credentials.username}")
        return True

    @allure.step("Check if the CAPTCHA is visible")
    def captcha_visible(self) -> bool:
        visible = self.captcha_shown() or self.check_visible(self.captcha_frame)
        self.logger.info(f"CAPTCHA visible: {visible}")
        if visible:
            LoginPage.captcha_seen = True
        return visible

    @allure.step("Continue as guest")
    def continue_as_guest(self) -> bool:
        if not self.open(BASE_URL):
            raise RuntimeError("eBay did not show the home page (CAPTCHA or Error Page), so the run can't continue as guest")
        self.check_visible(self.sign_in_link, required=True)
        self.logger.info("Guest confirmed: 'Sign in' link visible")
        return False
