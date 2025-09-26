import pytest
import types

from seleniumbase_extensions import uc_gui_click_x_y_right_button

@pytest.fixture(autouse=True)
def _patch_sb_right_click(request):
    """
    Autouse fixture that only patches sb when the test requests the sb fixture.
    This avoids instantiating a browser unnecessarily for unrelated tests.
    """
    if "sb" in request.fixturenames:
        # fetch the real sb fixture value (created by SeleniumBase)
        sb = request.getfixturevalue("sb")

        # Do not override if SeleniumBase later provides the method natively
        if not hasattr(sb, "uc_gui_click_x_y_right_button"):
            def _method(self, x, y, timeframe=0.25):
                # Optional guard: don't call GUI code in deliberately headless environments.
                return uc_gui_click_x_y_right_button(self.driver, x, y, timeframe=timeframe)

            sb.uc_gui_click_x_y_right_button = types.MethodType(_method, sb)
    yield