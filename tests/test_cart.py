import allure
import pytest

from pages.cart_page import CartPage
from pages.item_page import ItemPage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage
from utils.config import SEARCH_DATA


@allure.epic("ebay")
@allure.feature("Login, search, cart, budget")
@pytest.mark.parametrize("data", SEARCH_DATA, ids=lambda data: data["query"])
def test_search_add_to_cart_budget(page, credentials, data):
    if LoginPage(page).login(credentials):
        CartPage(page).empty_cart()
    search_page = SearchResultsPage(page)
    urls = search_page.search_items_by_name_under_price(data["query"], data["max_price"], data["limit"])
    assert len(urls) <= data["limit"], f"Got {len(urls)} items, limit is {data['limit']}"
    if len(urls) < data["limit"]:
        assert not search_page.next_page_link.is_visible(), f"Got only {len(urls)} items but more result pages exist"
    items_added = ItemPage(page).add_items_to_cart(urls)
    CartPage(page).assert_cart_total_not_exceeds(data["max_price"], items_added)
