import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


# Parametrize for Chrome and Edge
@pytest.mark.parametrize("browser", ["chrome", "edge"])
def test_svg_zoom_pan_undo_redo(browser):
    # Set up driver
    if browser == "chrome":
        driver = webdriver.Chrome()  # Assumes chromedriver is in PATH
    elif browser == "edge":
        driver = webdriver.Edge()  # Assumes msedgedriver is in PATH
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    try:
        driver.get("http://localhost:8080/svg_view.html")
        time.sleep(1)

        # --- Test Zoom In ---
        zoom_in = driver.find_element(By.ID, "zoom-in")
        zoom_in.click()
        time.sleep(0.2)
        zoom_level = driver.find_element(By.ID, "zoom-level").text
        assert zoom_level != "100%", "Zoom in did not change zoom level"

        # --- Test Zoom Out ---
        zoom_out = driver.find_element(By.ID, "zoom-out")
        zoom_out.click()
        time.sleep(0.2)
        zoom_level_after = driver.find_element(By.ID, "zoom-level").text
        assert zoom_level_after != zoom_level, "Zoom out did not change zoom level"

        # --- Test Pan (simulate arrow keys) ---
        svg_area = driver.find_element(By.ID, "svg-canvas")
        svg_area.click()
        svg_area.send_keys(Keys.ARROW_RIGHT)
        svg_area.send_keys(Keys.ARROW_DOWN)
        time.sleep(0.2)
        # No direct assertion, but should not error

        # --- Test Undo/Redo (buttons) ---
        undo_btn = driver.find_element(By.ID, "zoom-undo")
        redo_btn = driver.find_element(By.ID, "zoom-redo")
        undo_btn.click()
        time.sleep(0.2)
        redo_btn.click()
        time.sleep(0.2)
        # No direct assertion, but should not error

        # --- Test Undo/Redo (keyboard) ---
        svg_area.send_keys(Keys.CONTROL, "z")
        time.sleep(0.2)
        svg_area.send_keys(Keys.CONTROL, "y")
        time.sleep(0.2)
        # No direct assertion, but should not error

        # --- Test Symbol Placement (if available) ---
        try:
            symbol_btn = driver.find_element(By.CSS_SELECTOR, "[data-symbol-id]")
            symbol_btn.click()
            time.sleep(0.2)
            # Click on SVG to place symbol
            svg_area.click()
            time.sleep(0.2)
        except Exception:
            pass  # Symbol placement optional

    finally:
        driver.quit()
