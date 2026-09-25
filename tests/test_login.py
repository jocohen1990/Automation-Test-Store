from playwright.sync_api import Page, expect  # type: ignore[reportMissingImports]

def test_valid_login(page: Page):
    # Navigate to the login page
    page.goto("https://automationteststore.com/index.php?rt=account/login")

    # Fill in the username and password fields
    page.locator("#loginFrm").locator("#loginFrm_loginname").fill("Testuser123098567")
    page.locator("#loginFrm").locator("#loginFrm_password").fill("Testuser1*")

    # Click the login button
    page.locator("#loginFrm").locator("button[type='submit']").click()

    # Assert that the user is redirected to the dashboard
    expect(page).to_have_url("https://automationteststore.com/index.php?rt=account/account")