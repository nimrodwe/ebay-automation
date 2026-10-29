import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class CartPage(BasePage):
    URL = "https://cart.ebay.com/"

    def __init__(self, page: Page):
        super().__init__(page)
        self.cart_items = page.locator("xpath=//*[@data-test-id='cart-item-link']")
        self.items_total = page.locator("xpath=//*[@data-test-id='ITEM_TOTAL']")
        self.remove_buttons = page.get_by_text("Remove", exact=True)

    @allure.step("Empty the cart")
    def empty_cart(self):
        if not self.open():
            self.raise_blocked("the cart")
        while self.remove_buttons.count() > 0:
            items_left = self.remove_buttons.count()
            self.click(self.remove_buttons.first)
            expect(self.remove_buttons).to_have_count(items_left - 1)
        self.logger.info("Cart is empty")

    @allure.step("Check the cart total is not more than {budget_per_item} x {items_count}")
    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int):
        if not self.open():
            self.raise_blocked("the cart")
        self.check_visible(self.items_total, required=True)
        items_total = self.parse_price(self.items_total.inner_text())
        limit = budget_per_item * items_count
        self.logger.info(
            f"Cart: {self.cart_items.count()} items | items total without shipping {items_total} | "
            f"limit {budget_per_item} x {items_count} = {limit}"
        )
        self.take_screenshot("Cart page")
        assert self.cart_items.count() == items_count, f"Cart has {self.cart_items.count()} items, expected {items_count}"
        assert items_total <= limit, f"Cart items total {items_total} exceeds budget {limit}"
