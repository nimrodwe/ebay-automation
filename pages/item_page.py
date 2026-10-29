import random

import allure
from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class ItemPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_role("heading", level=1)
        self.price = page.get_by_test_id("x-price-primary")
        self.converted_price = page.get_by_test_id("x-price-approx")
        self.add_to_cart_button = page.locator("#atcBtn_btn_1")
        self.added_to_cart_dialog = page.get_by_role("dialog", name="Added to cart")
        self.ebay_error_message = page.get_by_text("Something went wrong on our end")
        self.continue_without_personalizing_button = page.get_by_role("button", name="Yes, continue")
        self.ship_to_close_button = page.get_by_role("dialog", name="Are you shipping to").get_by_role("button", name="Dismiss")
        self.unselected_variants = page.get_by_role("button", name=": Select")
        self.open_variant_options = (
            page.get_by_role("option", disabled=False).filter(visible=True).filter(has_not_text="Select")
        )
        page.add_locator_handler(self.continue_without_personalizing_button, self.close_popup)
        page.add_locator_handler(self.ship_to_close_button, self.close_popup)

    def close_popup(self, button: Locator):
        self.logger.info(f"eBay showed a popup - closing it with {button}")
        self.click(button)

    def get_price(self) -> float | None:
        if self.converted_price.is_visible():
            return self.parse_price(self.converted_price.inner_text())
        if self.check_visible(self.price):
            return self.parse_price(self.price.inner_text())
        self.logger.info("eBay did not show a price on the item page")
        return None

    @allure.step("Add the items to the cart")
    def add_items_to_cart(self, urls: list[str]) -> int:
        search_tab = self.page
        added = 0
        total = 0
        for number, url in enumerate(urls, start=1):
            item_tab = search_tab.context.new_page()
            price = ItemPage(item_tab).add_to_cart(url, number, added + 1)
            item_tab.close()
            search_tab.bring_to_front()
            if price is not None:
                added += 1
                total += price
            self.logger.info(f"Back on the search tab - {added} items in the cart, total so far {round(total, 2)}")
        return added

    def add_to_cart(self, url: str, number: int, items_in_cart: int) -> float | None:
        if not self.open(url):
            self.raise_blocked(f"item {number}")
        name = self.title.inner_text()
        if not self.check_visible(self.add_to_cart_button):
            self.logger.info(f"Skipping item {number}: '{name}' has no Add to cart button (Buy It Now / offer only)")
            return None
        with allure.step(f"Add item {number} to the cart: {name}"):
            self.choose_random_variants()
            price = self.get_price()
            self.click(self.add_to_cart_button)
            cart_icon = self.page.get_by_role("link", name=f"Your shopping cart contains {items_in_cart} items")
            self.check_visible(self.added_to_cart_dialog.or_(cart_icon).or_(self.ebay_error_message).first, required=True)
            if self.ebay_error_message.is_visible():
                self.logger.info(f"Skipping item {number}: eBay could not add '{name}' (Something went wrong on our end)")
                self.take_screenshot(f"Not added {number} - {name}")
                return None
            self.logger.info(f"Added to cart {number}: {name} | price {price}")
            self.take_screenshot(f"Added to cart {number} - {name}")
        return price or 0.0

    def choose_random_variants(self):
        for _ in range(self.unselected_variants.count()):
            variant = self.unselected_variants.first
            variant_name = variant.inner_text().split(":")[0]
            self.click(variant)
            self.check_visible(self.open_variant_options.first, required=True)
            option = random.choice(self.open_variant_options.all())
            self.logger.info(f"{variant_name}: picked '{option.inner_text()}' at random")
            self.click(option)
            self.page.wait_for_load_state()
