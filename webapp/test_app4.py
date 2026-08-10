import pathlib
from playwright.sync_api import sync_playwright

html_path = pathlib.Path("/home/claude/tagndice/webapp/index.html").resolve()
url = html_path.as_uri()
portrait_path = str(pathlib.Path("/home/claude/tagndice/test_portrait.jpg").resolve())

def main():
    errors = []
    native_dialogs = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1800, "height": 1400})
        page.on("pageerror", lambda exc: errors.append(f"PAGEERROR: {exc}"))
        page.on("dialog", lambda d: (native_dialogs.append((d.type, d.message)), d.dismiss()))
        page.route("**://fonts.googleapis.com/**", lambda route: route.abort())
        page.route("**://cdnjs.cloudflare.com/**", lambda route: route.abort())

        page.goto(url)
        page.wait_for_timeout(400)

        # ---- 0. logo actually rendered as an image (data URI), on both pages
        front_logo_src = page.locator(".paper.front .head img.logo").get_attribute("src")
        back_logo_src = page.locator(".paper.back .head2 img.logo").get_attribute("src")
        assert front_logo_src and front_logo_src.startswith("data:image/png;base64,"), "front logo not embedded"
        assert back_logo_src and back_logo_src.startswith("data:image/png;base64,"), "back logo not embedded"
        print("logos OK, length:", len(front_logo_src))

        # ---- 1. front page: name typing focus retention (regression, table/paper restructure)
        name_input = page.locator("#name")
        name_input.fill("")
        name_input.click()
        name_input.press_sequentially("모험가라나", delay=50)
        page.wait_for_timeout(120)
        assert page.evaluate("() => document.activeElement === document.getElementById('name')")
        assert name_input.input_value() == "모험가라나"

        # ---- 2. 태생 태그 fields work
        page.locator("#race").fill("엘프")
        page.locator("#background").fill("떠돌이 상인")
        page.locator("#instinct").fill("호기심")
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().race") == "엘프"

        # ---- 3. experience table: 10 rows present, typing focus retained
        exp_rows = page.locator("#experience tr")
        assert exp_rows.count() == 10, f"expected 10 experience rows, got {exp_rows.count()}"
        first_tag_input = exp_rows.nth(0).locator("input")
        first_tag_input.click()
        first_tag_input.press_sequentially("그림자베기숙련자", delay=50)
        page.wait_for_timeout(120)
        assert page.evaluate("() => document.activeElement === document.querySelectorAll('#experience input')[0]"), "experience input lost focus"
        assert page.evaluate("() => current().experience[0].name") == "그림자베기숙련자"
        exp_rows.nth(0).locator("select").nth(1).select_option("3")
        exp_rows.nth(1).locator("input").fill("두번째태그"); exp_rows.nth(1).locator("select").nth(1).select_option("3")
        exp_rows.nth(2).locator("input").fill("세번째태그"); exp_rows.nth(2).locator("select").nth(1).select_option("3")
        page.wait_for_timeout(120)
        assert page.locator("#tagSum").inner_text() == "9"
        assert page.locator("#level").inner_text() == "Ⅱ", "level formula regressed (no +3 expected)"

        # ---- 4. erosion e-cards: hexbadge + input + 정화 button
        e_cards = page.locator("#erosion .e-card")
        assert e_cards.count() == 3
        ero_input = e_cards.nth(0).locator("input")
        ero_input.click(); ero_input.press_sequentially("속삭임", delay=50)
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().erosion[0]") == "속삭임"
        e_cards.nth(0).locator("button.mini").click()
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().erosion[0]") == ""
        assert ero_input.input_value() == ""

        # ---- 5. resources: hexbadge icons + box click + -/+ buttons (ReferenceError regression)
        res_rows = page.locator("#resources .res-row")
        assert res_rows.count() == 3
        for i in range(3):
            hexicon = res_rows.nth(i).locator(".hexbadge .hb-fg").inner_text()
            assert hexicon in ("♥", "✦", "●"), f"missing resource hex icon: {hexicon!r}"
        minus_btn = res_rows.nth(0).locator(".resource-actions button").nth(0)
        plus_btn = res_rows.nth(0).locator(".resource-actions button").nth(1)
        before = page.evaluate("() => current().health")
        minus_btn.click(); page.wait_for_timeout(80)
        after_minus = page.evaluate("() => current().health")
        plus_btn = page.locator("#resources .res-row").nth(0).locator(".resource-actions button").nth(1)
        plus_btn.click(); page.wait_for_timeout(80)
        after_plus = page.evaluate("() => current().health")
        assert after_minus == before - 1, f"minus button failed: {before} -> {after_minus}"
        assert after_plus == before, f"plus button failed to restore: {before} -> {after_plus}"
        assert not errors, f"resource +/- buttons threw JS errors: {errors}"
        box3 = res_rows.nth(0).locator(".track .box").nth(2)
        box3.click(); page.wait_for_timeout(80)
        assert page.evaluate("() => current().health") == 3, "clicking a track box should set current value directly"

        # ---- 6. dice roll works
        page.click("text=🎲 2d6 굴리기")
        page.wait_for_timeout(100)
        assert "—" not in page.locator("#dice").inner_text()

        # ---- 7. magic item: name/tag inputs + form radio + uses toggle
        page.locator("#magicItem").fill("서리검")
        page.locator("#dedicatedTag").fill("서리베기")
        page.locator('input[name="magicForm"][value="무기류"]').check()
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().magicItem") == "서리검"
        assert page.evaluate("() => current().magicForm") == "무기류"
        page.locator("#magicUses button").nth(0).click()
        page.wait_for_timeout(80)
        assert page.evaluate("() => current().magicUses[0]") == True

        # ---- 8. inventory table 10 rows + gear-foot 6 fields
        inv_rows = page.locator("#inventory tr")
        assert inv_rows.count() == 10
        inv_rows.nth(0).locator("input").fill("낡은 지도")
        page.locator("#weapon").fill("단검"); page.locator("#armor").fill("가죽갑옷")
        page.locator("#gold").fill("12"); page.locator("#silver").fill("5"); page.locator("#copper").fill("30"); page.locator("#shard").fill("1")
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().inventory[0]") == "낡은 지도"
        assert page.evaluate("() => current().gold") == "12"

        # ---- 9. back page: info fields incl new look1/look2, backstory, nameMirror
        page.locator("#value").fill("정의")
        page.locator("#age").fill("27")
        page.locator("#body").fill("175cm / 68kg")
        page.locator("#look1").fill("왼쪽 뺨의 흉터")
        page.locator("#look2").fill("은발")
        page.locator("#backstory").fill("긴 여정 끝에...")
        page.wait_for_timeout(100)
        assert page.evaluate("() => current().look1") == "왼쪽 뺨의 흉터"
        assert page.evaluate("() => current().look2") == "은발"
        assert page.locator("#nameMirror").inner_text() == "모험가라나", "back-page name mirror not synced"

        # ---- 10. portrait upload -> canvas resize -> stored as data URL, then remove
        page.locator("#portraitFile").set_input_files(portrait_path)
        page.wait_for_timeout(400)
        portrait_val = page.evaluate("() => current().portrait")
        assert portrait_val.startswith("data:image/jpeg;base64,"), "portrait not stored as data URL"
        assert page.locator("#portraitImg").is_visible(), "portrait image should be visible after upload"
        assert not page.locator("#portraitPlaceholder").is_visible(), "placeholder should hide after upload"
        page.locator("#portraitRemoveBtn").click()
        page.wait_for_timeout(150)
        assert page.evaluate("() => current().portrait") == "", "portrait should be cleared after remove"
        assert page.locator("#portraitPlaceholder").is_visible(), "placeholder should reappear after remove"

        # ---- 11. GM secret box must NOT exist anywhere inside playerView (security)
        secret_in_player = page.locator("#playerView #secret").count()
        assert secret_in_player == 0, "GM secret textarea leaked into player view!"
        gmnote_count = page.locator("#playerView .gmnote").count()
        assert gmnote_count == 0, "decorative GM-note box should be fully removed from the player sheet (19차)"

        # ---- 12. rule cheat sheet: 10 items present on back page
        cheat_items = page.locator("#playerView .cheat ul li")
        assert cheat_items.count() == 10, f"expected 10 rule-summary items, got {cheat_items.count()}"

        # ---- 13. character delete/reset still via custom modal (regression)
        page.click("text=＋ 새 캐릭터")
        page.wait_for_timeout(150)
        count_before_delete = page.locator("#charSelect option").count()
        page.click("button.tbtn.danger:has-text('삭제')")
        page.wait_for_timeout(150)
        assert page.locator("#modalOverlay").is_visible()
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(200)
        assert page.locator("#charSelect option").count() == count_before_delete - 1

        page.click("button.tbtn:has-text('초기화')")
        page.wait_for_timeout(150)
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(150)
        assert page.locator("#tagSum").inner_text() == "0", "reset should clear tag sum"
        assert page.locator("#portraitPlaceholder").is_visible(), "reset should also clear portrait"

        # ---- 14. GM PIN lock still enforced across reload
        page.click("#navGM")
        page.wait_for_timeout(150)
        page.click("text=🔒 GM 잠금")
        page.wait_for_timeout(150)
        page.fill("#modalInput", "9911")
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(150)
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(150)
        page.reload()
        page.wait_for_timeout(400)
        page.click("#navGM")
        page.wait_for_timeout(150)
        page.fill("#modalInput", "wrong")
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(150)
        blocked = "active" not in (page.locator("#gmView").get_attribute("class") or "")
        if page.locator("#modalOverlay").is_visible():
            page.click("#modalButtons button:has-text('확인')")
            page.wait_for_timeout(100)
        assert blocked, "GM view should stay blocked on wrong PIN after reload"
        page.click("#navGM"); page.wait_for_timeout(100)
        page.fill("#modalInput", "9911")
        page.click("#modalButtons button:has-text('확인')")
        page.wait_for_timeout(150)
        assert "active" in (page.locator("#gmView").get_attribute("class") or "")

        # ---- 15. print media emulation (sanity screenshot, both pages should be block-visible)
        page.click("#navPlayer")
        page.wait_for_timeout(150)
        page.emulate_media(media="print")
        page.wait_for_timeout(150)
        front_visible_print = page.locator(".paper.front").is_visible()
        back_visible_print = page.locator(".paper.back").is_visible()
        page.screenshot(path="/home/claude/tagndice/webapp/v3_print.png", full_page=True)
        # must read the print transform BEFORE switching back to screen media --
        # otherwise this silently re-checks the on-screen (scaled) transform instead
        # of the print one, which is exactly the bug that let this slip through once.
        print_transform = page.evaluate("getComputedStyle(document.getElementById('papersScroll')).transform")
        # 26차: the screen layout was rebuilt from scratch, and the one thing
        # that absolutely had to survive untouched was the printed sheet. Lock
        # the real A4 geometry down here so a future screen-side change can
        # never quietly drag print along with it. These are the measured
        # values from before the rewrite; 210mm = 793.69px at 96dpi.
        print_geom = page.evaluate("""() => {
          const g = s => { const e = document.querySelector(s); if (!e) return null;
            const r = e.getBoundingClientRect();
            return {w: +r.width.toFixed(2), h: +r.height.toFixed(2)}; };
          const c = (s, p) => getComputedStyle(document.querySelector(s))[p];
          return {front: g('.paper.front'), back: g('.paper.back'),
                  main: g('.main'), origin: g('.origin'),
                  mainCols: c('.main','gridTemplateColumns'),
                  originCols: c('.origin','gridTemplateColumns'),
                  cheatCols: c('.cheat ul','columnCount'),
                  paperW: c('.paper','width')};
        }""")
        page.emulate_media(media="screen")
        assert front_visible_print and back_visible_print, "both pages should render under print media"
        assert print_transform in ("none", "matrix(1, 0, 0, 1, 0, 0)"), f"print output must ignore any on-screen transform: {print_transform!r}"

        PRINT_EXPECTED = {
            "front": {"w": 793.69, "h": 1219.42},
            "back":  {"w": 793.69, "h": 1122.52},
            "main":  {"w": 727.22, "h": 476.34},
            "origin": {"w": 727.22, "h": 67.89},
            "mainCols": "419.172px 295.188px",
            "originCols": "236.359px 236.359px 236.359px",
            "cheatCols": "2",
            "paperW": "793.688px",
        }
        for k, want in PRINT_EXPECTED.items():
            got = print_geom[k]
            if isinstance(want, dict):
                for dim in want:
                    assert abs(got[dim] - want[dim]) < 0.6, \
                        f"print geometry drifted: {k}.{dim} = {got[dim]}, expected {want[dim]}"
            else:
                assert got == want, f"print geometry drifted: {k} = {got!r}, expected {want!r}"
        print("print A4 geometry locked OK (210mm pages, 2-col body, 2-col rule summary)")

        # ---- 16. desktop: front (left) / back (right) shown side by side (19차)
        front_box = page.locator(".paper.front").bounding_box()
        back_box = page.locator(".paper.back").bounding_box()
        same_row = abs(front_box["y"] - back_box["y"]) < 5
        back_is_right_of_front = back_box["x"] >= front_box["x"] + front_box["width"] - 5
        assert same_row and back_is_right_of_front, f"front/back should sit side by side on desktop: {front_box} vs {back_box}"

        # ---- 17. narrow/mobile viewport: front/back fall back to stacked (vertical)
        page.set_viewport_size({"width": 480, "height": 900})
        page.wait_for_timeout(200)
        front_box_m = page.locator(".paper.front").bounding_box()
        back_box_m = page.locator(".paper.back").bounding_box()
        assert back_box_m["y"] >= front_box_m["y"] + front_box_m["height"] - 5, "narrow viewport should stack front/back vertically"
        page.set_viewport_size({"width": 1800, "height": 1400})
        page.wait_for_timeout(200)

        # ---- 17b. responsive layout contract (26차 rewrite).
        #
        # 20~25차 shrank the whole print sheet with transform:scale() to make
        # it fit, so the tests here asserted things about a scale FACTOR
        # (exact ratios, floors, ceilings, no-scrollbar-in-either-direction).
        # 26차 removed scaling entirely: on screen the sheet is an ordinary
        # responsive page. So the contract being tested changed, and these
        # assertions are rewritten around what actually has to hold now:
        #
        #   1. never any HORIZONTAL overflow, at any viewport (this is the
        #      invariant that survived every round -- clipping is the one
        #      failure the user reported more than once)
        #   2. no transform is applied to the sheet at all, ever
        #   3. text size does NOT depend on viewport size -- the whole point
        #      of dropping scale() is that a narrow window makes the layout
        #      reflow, not the type shrink
        #   4. two pages side by side when there is room, stacked when not
        #   5. leftover width is shared evenly (content stays centred), which
        #      is the 25차 "빈 공간" guarantee, now via plain margin:auto
        #
        # Vertical scrolling is expected and no longer a failure: the sheet is
        # rendered at readable size rather than squeezed into the window.
        def layout_probe(pg):
            return pg.evaluate("""() => {
              const de = document.documentElement;
              const f = document.querySelector('.paper.front').getBoundingClientRect();
              const b = document.querySelector('.paper.back').getBoundingClientRect();
              const sc = document.querySelector('.papers-scroll');
              const td = document.querySelector('table.grid td');
              return {
                hOverflow: de.scrollWidth - de.clientWidth,
                clientW: de.clientWidth,
                front: {x: f.x, y: f.y, w: f.width, r: f.x + f.width},
                back: {x: b.x, y: b.y, w: b.width, r: b.x + b.width},
                twoUp: Math.abs(f.y - b.y) < 5,
                transform: getComputedStyle(sc).transform,
                tdFont: getComputedStyle(td).fontSize,
                secFont: getComputedStyle(document.querySelector('h2.sec')).fontSize,
              };
            }""")

        SIZES = [
            (2560, 1400), (1920, 1080), (1760, 1200), (1440, 900),
            (1280, 800), (1100, 900), (1024, 768), (900, 650),
            (768, 1024), (620, 900), (480, 800), (360, 740),
        ]
        fonts_seen = set()
        for w, h in SIZES:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(260)
            pr = layout_probe(page)

            # (1) no horizontal overflow, and neither page clipped off-screen
            assert pr["hOverflow"] <= 1, f"{w}x{h}: horizontal overflow of {pr['hOverflow']}px"
            for side in ("front", "back"):
                bx = pr[side]
                assert bx["x"] >= -1, f"{w}x{h}: {side} page starts off-screen at x={bx['x']}"
                assert bx["r"] <= pr["clientW"] + 1, f"{w}x{h}: {side} page right edge {bx['r']} exceeds {pr['clientW']}"

            # (2) no scaling machinery anywhere
            assert pr["transform"] in ("none", "matrix(1, 0, 0, 1, 0, 0)"), \
                f"{w}x{h}: sheet should never be transformed, got {pr['transform']}"

            # (3) type size is viewport-independent
            fonts_seen.add((pr["tdFont"], pr["secFont"]))

            # (4) side-by-side only when two pages genuinely fit
            if w >= 1280:
                assert pr["twoUp"], f"{w}x{h}: expected front/back side by side"
            elif w <= 1024:
                assert not pr["twoUp"], f"{w}x{h}: expected front/back stacked"

            # (5) leftover width shared evenly, never dumped on one side
            left = pr["front"]["x"]
            right = pr["clientW"] - (pr["back"]["r"] if pr["twoUp"] else pr["front"]["r"])
            assert abs(left - right) < 3, \
                f"{w}x{h}: content not centred -- left={left:.1f} right={right:.1f}"

        assert len(fonts_seen) == 1, \
            f"font sizes must not vary with viewport (that was the scale() behaviour), saw {fonts_seen}"
        print("responsive layout OK across", len(SIZES), "viewports; type fixed at", fonts_seen)

        # (6) interaction still lands correctly with no transform in play, at
        # both a wide and a narrow viewport (hit-testing regression guard kept
        # from the 23차 tests, which caught coordinate problems under scale).
        for w, h in ((1920, 1080), (480, 800)):
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(260)
            nm = page.locator("#name")
            nm.scroll_into_view_if_needed()
            nm.fill("")
            nm.click()
            nm.press_sequentially("좌표확인", delay=30)
            page.wait_for_timeout(120)
            assert nm.input_value() == "좌표확인", f"{w}x{h}: typing did not land in #name"
            btn = page.locator(".rollcard button.primary")
            btn.scroll_into_view_if_needed()
            btn.click()
            page.wait_for_timeout(160)
            assert page.locator("#result").inner_text().strip() not in ("", "2d6을 굴려보세요."), \
                f"{w}x{h}: dice roll did not register"
        page.locator("#name").fill("모험가라나")
        page.wait_for_timeout(120)

        page.set_viewport_size({"width": 1800, "height": 1400})
        page.wait_for_timeout(220)

        # ---- 18. hexbadge icons are large enough to be legible on screen (19차 fix
        # for the "icon looks squished" report -- at the old 5.6mm/6.2pt/weight:900
        # size the ♥/✦/●/☠ glyphs rendered as an illegible blob on a normal 96dpi
        # screen even though print output was fine; regression-guard the fix here.)
        hb_box = page.locator(".hexbadge.sm").first.bounding_box()
        assert hb_box["width"] >= 28, f"hexbadge icons regressed back to an illegibly small screen size: {hb_box}"

        # full-page screenshots for visual review
        page.wait_for_timeout(100)
        page.screenshot(path="/home/claude/tagndice/webapp/v3_screen_full.png", full_page=True)

        print("\n--- native dialogs (should be EMPTY) ---")
        for d in native_dialogs: print(d)
        print("--- page errors (should be EMPTY) ---")
        for e in errors: print(e)

        browser.close()

        assert not native_dialogs, f"native dialogs used: {native_dialogs}"
        if errors:
            raise SystemExit("JS PAGE ERRORS DETECTED")
        print("\nALL CHECKS PASSED")

main()
