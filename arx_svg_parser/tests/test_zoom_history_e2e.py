"""
E2E Tests for SVG Zoom History using Selenium WebDriver
Tests undo/redo functionality for zoom operations
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class TestZoomHistoryE2E:
    """E2E tests for zoom history undo/redo functionality"""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome WebDriver with headless option"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Auto-download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        yield driver
        driver.quit()
    
    def test_zoom_history_undo_redo_buttons(self, driver):
        """Test zoom history undo/redo using UI buttons"""
        print("Testing zoom history undo/redo with UI buttons...")
        
        # Navigate to SVG viewer
        driver.get("http://localhost:8080/svg_view.html")
        wait = WebDriverWait(driver, 10)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "zoom-level")))
        
        # Get initial zoom level
        initial_zoom = driver.find_element(By.ID, "zoom-level").text
        assert initial_zoom.strip() == "100%", f"Initial zoom should be 100%, got {initial_zoom}"
        
        # Zoom in twice
        zoom_in_btn = driver.find_element(By.ID, "zoom-in")
        zoom_in_btn.click()
        time.sleep(0.2)
        zoom_in_btn.click()
        time.sleep(0.2)
        
        # Check zoom changed
        zoom_after_zoom_in = driver.find_element(By.ID, "zoom-level").text
        assert zoom_after_zoom_in != initial_zoom, "Zoom should have changed after zoom in"
        
        # Undo zoom (button)
        undo_btn = driver.find_element(By.ID, "zoom-undo")
        undo_btn.click()
        time.sleep(0.2)
        
        zoom_after_undo = driver.find_element(By.ID, "zoom-level").text
        assert zoom_after_undo != zoom_after_zoom_in, "Undo should have changed zoom"
        
        # Redo zoom (button)
        redo_btn = driver.find_element(By.ID, "zoom-redo")
        redo_btn.click()
        time.sleep(0.2)
        
        zoom_after_redo = driver.find_element(By.ID, "zoom-level").text
        assert zoom_after_redo == zoom_after_zoom_in, "Redo should restore previous zoom"
        
        print("✓ Zoom history undo/redo with UI buttons test passed")
    
    def test_zoom_history_keyboard_shortcuts(self, driver):
        """Test zoom history undo/redo using keyboard shortcuts"""
        print("Testing zoom history undo/redo with keyboard shortcuts...")
        
        # Navigate to SVG viewer
        driver.get("http://localhost:8080/svg_view.html")
        wait = WebDriverWait(driver, 10)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "zoom-level")))
        
        # Get initial zoom level
        initial_zoom = driver.find_element(By.ID, "zoom-level").text
        
        # Zoom in twice
        zoom_in_btn = driver.find_element(By.ID, "zoom-in")
        zoom_in_btn.click()
        time.sleep(0.2)
        zoom_in_btn.click()
        time.sleep(0.2)
        
        zoom_after_zoom_in = driver.find_element(By.ID, "zoom-level").text
        
        # Undo zoom (Ctrl+Z)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.CONTROL + "z")
        time.sleep(0.2)
        
        zoom_after_undo_key = driver.find_element(By.ID, "zoom-level").text
        assert zoom_after_undo_key != zoom_after_zoom_in, "Keyboard undo should have changed zoom"
        
        # Redo zoom (Ctrl+Y)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.CONTROL + "y")
        time.sleep(0.2)
        
        zoom_after_redo_key = driver.find_element(By.ID, "zoom-level").text
        assert zoom_after_redo_key == zoom_after_zoom_in, "Keyboard redo should restore previous zoom"
        
        print("✓ Zoom history undo/redo with keyboard shortcuts test passed")
    
    def test_zoom_history_button_states(self, driver):
        """Test that undo/redo buttons are properly enabled/disabled"""
        print("Testing zoom history button states...")
        
        # Navigate to SVG viewer
        driver.get("http://localhost:8080/svg_view.html")
        wait = WebDriverWait(driver, 10)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "zoom-undo")))
        
        # Initially, undo should be disabled, redo should be disabled
        undo_btn = driver.find_element(By.ID, "zoom-undo")
        redo_btn = driver.find_element(By.ID, "zoom-redo")
        
        # Check initial state (should be disabled)
        assert undo_btn.get_attribute("disabled") is not None, "Undo button should be disabled initially"
        assert redo_btn.get_attribute("disabled") is not None, "Redo button should be disabled initially"
        
        # Zoom in to enable undo
        zoom_in_btn = driver.find_element(By.ID, "zoom-in")
        zoom_in_btn.click()
        time.sleep(0.2)
        
        # Now undo should be enabled, redo should be disabled
        assert undo_btn.get_attribute("disabled") is None, "Undo button should be enabled after zoom"
        assert redo_btn.get_attribute("disabled") is not None, "Redo button should be disabled"
        
        # Undo to go back to initial state
        undo_btn.click()
        time.sleep(0.2)
        
        # Back to initial state
        assert undo_btn.get_attribute("disabled") is not None, "Undo button should be disabled after undo"
        assert redo_btn.get_attribute("disabled") is not None, "Redo button should be disabled after undo"
        
        print("✓ Zoom history button states test passed")
    
    def test_complex_zoom_history_sequence(self, driver):
        """Test complex zoom history sequence with multiple operations"""
        print("Testing complex zoom history sequence...")
        
        # Navigate to SVG viewer
        driver.get("http://localhost:8080/svg_view.html")
        wait = WebDriverWait(driver, 10)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.ID, "zoom-level")))
        
        # Record zoom levels through sequence
        zoom_levels = []
        
        # Initial zoom
        zoom_levels.append(driver.find_element(By.ID, "zoom-level").text)
        
        # Zoom in
        driver.find_element(By.ID, "zoom-in").click()
        time.sleep(0.2)
        zoom_levels.append(driver.find_element(By.ID, "zoom-level").text)
        
        # Zoom in again
        driver.find_element(By.ID, "zoom-in").click()
        time.sleep(0.2)
        zoom_levels.append(driver.find_element(By.ID, "zoom-level").text)
        
        # Zoom out
        driver.find_element(By.ID, "zoom-out").click()
        time.sleep(0.2)
        zoom_levels.append(driver.find_element(By.ID, "zoom-level").text)
        
        # Reset view
        driver.find_element(By.ID, "reset-view").click()
        time.sleep(0.2)
        zoom_levels.append(driver.find_element(By.ID, "zoom-level").text)
        
        # Now test undo sequence
        undo_btn = driver.find_element(By.ID, "zoom-undo")
        redo_btn = driver.find_element(By.ID, "zoom-redo")
        
        # Undo reset view (should go back to zoom out state)
        undo_btn.click()
        time.sleep(0.2)
        current_zoom = driver.find_element(By.ID, "zoom-level").text
        assert current_zoom == zoom_levels[3], f"Undo should restore zoom level {zoom_levels[3]}, got {current_zoom}"
        
        # Undo zoom out (should go back to second zoom in state)
        undo_btn.click()
        time.sleep(0.2)
        current_zoom = driver.find_element(By.ID, "zoom-level").text
        assert current_zoom == zoom_levels[2], f"Undo should restore zoom level {zoom_levels[2]}, got {current_zoom}"
        
        # Redo zoom out
        redo_btn.click()
        time.sleep(0.2)
        current_zoom = driver.find_element(By.ID, "zoom-level").text
        assert current_zoom == zoom_levels[3], f"Redo should restore zoom level {zoom_levels[3]}, got {current_zoom}"
        
        print("✓ Complex zoom history sequence test passed")


if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"]) 