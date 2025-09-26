from seleniumbase.core.browser_launcher import install_pyautogui_if_missing, get_configured_pyautogui, fasteners, constants, time, sys, IS_WINDOWS, sb_config,__is_cdp_swap_needed, suppress, page_actions

def uc_gui_click_x_y_right_button(driver, x, y, timeframe=0.25):
    gui_lock = fasteners.InterProcessLock(
        constants.MultiBrowser.PYAUTOGUILOCK
    )
    with gui_lock:  # Prevent issues with multiple processes
        install_pyautogui_if_missing(driver)
        import pyautogui
        pyautogui = get_configured_pyautogui(pyautogui)
        connected = True
        width_ratio = 1.0
        if IS_WINDOWS:
            connected = driver.is_connected()
            if (
                not connected
                and (
                    not hasattr(sb_config, "_saved_width_ratio")
                    or not sb_config._saved_width_ratio
                )
                and not __is_cdp_swap_needed(driver)
            ):
                driver.reconnect(0.1)
        if IS_WINDOWS and not __is_cdp_swap_needed(driver):
            window_rect = driver.get_window_rect()
            width = window_rect["width"]
            height = window_rect["height"]
            win_x = window_rect["x"]
            win_y = window_rect["y"]
            scr_width = pyautogui.size().width
            driver.maximize_window()
            win_width = driver.get_window_size()["width"]
            width_ratio = round(float(scr_width) / float(win_width), 2) + 0.01
            if width_ratio < 0.45 or width_ratio > 2.55:
                width_ratio = 1.01
            sb_config._saved_width_ratio = width_ratio
            driver.minimize_window()
            driver.set_window_rect(win_x, win_y, width, height)
        elif IS_WINDOWS and __is_cdp_swap_needed(driver):
            window_rect = driver.cdp.get_window_rect()
            width = window_rect["width"]
            height = window_rect["height"]
            win_x = window_rect["x"]
            win_y = window_rect["y"]
            scr_width = pyautogui.size().width
            driver.cdp.maximize()
            win_width = driver.cdp.get_window_size()["width"]
            width_ratio = round(float(scr_width) / float(win_width), 2) + 0.01
            if width_ratio < 0.45 or width_ratio > 2.55:
                width_ratio = 1.01
            sb_config._saved_width_ratio = width_ratio
            driver.cdp.minimize()
            driver.cdp.set_window_rect(win_x, win_y, width, height)
        if IS_WINDOWS:
            x = x * width_ratio
            y = y * width_ratio
            _uc_gui_click_x_y_right_button(driver, x, y, timeframe=timeframe, uc_lock=False)
            return
        with suppress(Exception):
            page_actions.switch_to_window(
                driver, driver.current_window_handle, 2, uc_lock=False
            )
        _uc_gui_click_x_y_right_button(driver, x, y, timeframe=timeframe, uc_lock=False)

def _uc_gui_click_x_y_right_button(driver, x, y, timeframe=0.25, uc_lock=False):
    install_pyautogui_if_missing(driver)
    import pyautogui
    pyautogui = get_configured_pyautogui(pyautogui)
    screen_width, screen_height = pyautogui.size()
    if x < 0 or y < 0 or x > screen_width or y > screen_height:
        raise Exception(
            "PyAutoGUI cannot click on point (%s, %s)"
            " outside screen. (Width: %s, Height: %s)"
            % (x, y, screen_width, screen_height)
        )
    if uc_lock:
        gui_lock = fasteners.InterProcessLock(
            constants.MultiBrowser.PYAUTOGUILOCK
        )
        with gui_lock:  # Prevent issues with multiple processes
            pyautogui.moveTo(x, y, timeframe, pyautogui.easeOutQuad)
            if timeframe >= 0.25:
                time.sleep(0.056)  # Wait if moving at human-speed
            if "--debug" in sys.argv:
                print(" <DEBUG> pyautogui.click(%s, %s)" % (x, y))
            pyautogui.click(x=x, y=y, button='right')
    else:
        # Called from a method where the gui_lock is already active
        pyautogui.moveTo(x, y, timeframe, pyautogui.easeOutQuad)
        if timeframe >= 0.25:
            time.sleep(0.056)  # Wait if moving at human-speed
        if "--debug" in sys.argv:
            print(" <DEBUG> pyautogui.click(%s, %s)" % (x, y))
        pyautogui.click(x=x, y=y, button='right')
