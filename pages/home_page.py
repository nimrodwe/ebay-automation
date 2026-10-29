import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.config import BASE_URL


class HomePage(BasePage):
    URL = BASE_URL

    def __init__(self, page: Page):
        super().__init__(page)
        self.search_box = page.locator("#gh-ac")
        self.search_button = page.locator("#gh-search-btn")

    @allure.step("Search for '{query}'")
    def search(self, query: str):
        if not self.search_box.is_visible() and not self.open():
            self.raise_blocked("the home page")
        self.type_into(self.search_box, query)
        self.click_and_wait(self.search_button)
