import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from pages.home_page import HomePage
from utils.config import BASE_URL


class SearchResultsPage(BasePage):
    ITEM_PRICE = "xpath=.//span[contains(@class, 's-card__price')]"

    def __init__(self, page: Page):
        super().__init__(page)
        self.max_price_box = page.get_by_role("textbox", name="Maximum Value")
        self.submit_price_button = page.get_by_role("button", name="Submit price range")
        self.next_page_link = page.get_by_role("link", name="Go to next search page")
        self.items = page.locator("xpath=//li[@data-listingid][not(.//*[text()='Shop on eBay'])]")

    @allure.step("Search '{query}' for up to {limit} items priced up to {max_price}")
    def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5) -> list[str]:
        HomePage(self.page).search(query)
        self.set_max_price(max_price)
        urls = self.item_urls_under(max_price)
        while len(urls) < limit and self.next_page_link.is_visible():
            self.click_and_wait(self.next_page_link)
            urls += [url for url in self.item_urls_under(max_price) if url not in urls]
        urls = urls[:limit]
        self.logger.info(f"Found {len(urls)} items: {urls}")
        return urls

    @allure.step("Set max price to {max_price}")
    def set_max_price(self, max_price: float):
        if self.check_visible(self.max_price_box):
            self.type_into(self.max_price_box, str(max_price))
            self.click_and_wait(self.submit_price_button)

    def item_urls_under(self, max_price: float) -> list[str]:
        urls = []
        for item in self.items.all():
            price = self.parse_price(item.locator(self.ITEM_PRICE).first.inner_text())
            url = f"{BASE_URL}/itm/{item.get_attribute('data-listingid')}"
            if price is not None and price <= max_price and url not in urls:
                urls.append(url)
        self.logger.info(f"{len(urls)} items on this page cost up to {max_price}")
        return urls
