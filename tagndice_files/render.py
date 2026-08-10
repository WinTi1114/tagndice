from playwright.sync_api import sync_playwright
import pathlib

html_path = pathlib.Path("/home/claude/tagndice/character_sheet.html").resolve()
url = html_path.as_uri()

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium/chrome-linux/chrome" if False else None)
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(300)

    # Full PDF (both pages via CSS page-break)
    page.pdf(
        path="/home/claude/tagndice/character_sheet.pdf",
        print_background=True,
        prefer_css_page_size=True,
    )

    # Individual high-res PNG screenshots of each .page for visual QA
    page.set_viewport_size({"width": 900, "height": 1300})
    front = page.locator(".page.front")
    back = page.locator(".page.back")
    front.screenshot(path="/home/claude/tagndice/qa_front.png", scale="css")
    back.screenshot(path="/home/claude/tagndice/qa_back.png", scale="css")

    browser.close()

print("done")
