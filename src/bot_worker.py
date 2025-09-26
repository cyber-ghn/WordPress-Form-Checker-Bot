import pytest
import smtplib
import utils
import random
import time
from dotenv import load_dotenv
from urllib.parse import urlparse
from os import getenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from faker import Faker
from os.path import abspath, join, dirname
from filelock import FileLock, Timeout

load_dotenv()

CONTACT_PAGES = utils.str_to_list(getenv("CONTACT_PAGES", ""))
USE_HEADLESS = utils.str_to_bool(getenv("USE_HEADLESS", "True"))

fake = Faker()
lock_file = join(dirname(abspath(__file__)), ".lock")

def load_urls():
    if not CONTACT_PAGES:
        raise ValueError("CONTACT_PAGES environment variable is not set or empty.")
    return CONTACT_PAGES

# Fixture to provide URLs to pytest
@pytest.fixture(scope="module")
def urls():
    return load_urls()

@pytest.fixture(autouse=True)
def _track_reruns(request):
    # Ajoute des infos utiles sur chaque test
    reruns = request.config.getoption("--reruns", default=0)
    exec_count = getattr(request.node, "execution_count", 1)
    request.node.is_last_try = (exec_count == reruns + 1)
    yield

class Bot:
    def __init__(self, sb, contact_page_url):
        self.sb = sb
        self.contact_page_url = contact_page_url

    def send_mail_on_failure(self, title, message):
        smtp_host = getenv("SMTP_HOST")
        smtp_port = int(getenv("SMTP_PORT", 587))
        smtp_user = getenv("SMTP_USERNAME")
        smtp_pass = getenv("SMTP_PASSWORD")
        email_from = getenv("EMAIL_FROM")
        email_to = utils.str_to_list(getenv("EMAIL_TO", ""))

        if not (smtp_host and smtp_user and smtp_pass and email_from and email_to):
            print("Missing SMTP or email configuration.")
            return

        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = ", ".join(email_to)
        msg['Subject'] = "[FORM-CHECK] " + title

        msg.attach(MIMEText(message, 'plain'))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(email_from, email_to, msg.as_string())
            print("✅ Email sent.")
        except Exception as e:
            print("❌ Failed to send email:", str(e))

    def _human_type(self, element, text):
        for char in text:
            element.send_keys(char)
            self.sb.sleep(random.uniform(0.05, 0.25))

    def check_contact_form(self):
        try:
            if not USE_HEADLESS:
                with FileLock(lock_file, timeout=150):
                    try:
                        self.sb.uc_open_with_reconnect(self.contact_page_url, reconnect_time=12)
                    except Timeout:
                        print("Could not acquire lock for UC browser.")
            else:
                self.sb.open(self.contact_page_url)
            self.sb.wait_for_ready_state_complete()
            self.sb.sleep(random.uniform(1, 4))  # Random delay to mimic human behavior

            if not self.sb.wait_for_element(".wpcf7.js", timeout=10):
                raise Exception("Contact form was not found.")
            else:
                print("Contact form was found.")

                # Try to deny cookie banner if present
                try:
                    self.sb.wait_for_element(".cmplz-btn.cmplz-deny", timeout=5)
                    self.sb.click(".cmplz-btn.cmplz-deny")
                    self.sb.sleep(random.uniform(1, 1.2))  # Wait for banner to disappear
                except Exception:
                    pass

                container = self.sb.find_element(".wpcf7.js")
                
                # Ensure form is fully loaded and visible
                self.sb.wait_for_ready_state_complete()
                self.sb.sleep(2)  # Allow dynamic content to settle

                # Fill visible inputs only (avoid honeypots)
                try:
                    # Name field
                    name_selector = '[data-name="your-name"] input'
                    if self.sb.is_element_present(name_selector) and self.sb.is_element_visible(name_selector):
                        # Scroll to element using CSS selector
                        self.sb.scroll_to(name_selector)
                        self.sb.sleep(random.uniform(0.45, 0.65))
                        
                        # Get the element after scrolling
                        name_input = container.find_element("css selector", name_selector)
                        
                        # Try clicking with JavaScript if normal click fails
                        try:
                            self.sb.click(name_selector)
                        except Exception:
                            self.sb.execute_script("arguments[0].focus(); arguments[0].click();", name_input)
                        self.sb.sleep(random.uniform(0.45, 0.65))
                        self._human_type(name_input, fake.name())

                    # Email field
                    email_selector = '[data-name="your-email"] input'
                    if self.sb.is_element_present(email_selector) and self.sb.is_element_visible(email_selector):
                        self.sb.scroll_to(email_selector)
                        self.sb.sleep(random.uniform(0.45, 0.65))
                        
                        email_input = container.find_element("css selector", email_selector)
                        
                        try:
                            self.sb.click(email_selector)
                        except Exception:
                            self.sb.execute_script("arguments[0].focus(); arguments[0].click();", email_input)
                        self.sb.sleep(random.uniform(0.45, 0.65))
                        self._human_type(email_input, fake.email())

                    # Subject field
                    try:
                        subject_selector = '[data-name="your-subject"] input'
                        if self.sb.is_element_present(subject_selector) and self.sb.is_element_visible(subject_selector):
                            self.sb.scroll_to(subject_selector)
                            self.sb.sleep(random.uniform(0.45, 0.65))
                            
                            subject_input = container.find_element("css selector", subject_selector)
                            
                            try:
                                self.sb.click(subject_selector)
                            except Exception:
                                self.sb.execute_script("arguments[0].focus(); arguments[0].click();", subject_input)
                            self.sb.sleep(random.uniform(0.45, 0.65))
                            self._human_type(subject_input, f"[FORM-CHECK] Test {fake.word()} {random.randint(100, 999)}")
                    except Exception:
                        # Subject field might not exist on all forms
                        print("Subject field not found or not accessible, continuing...")

                    # Message field (if exists)
                    try:
                        message_selector = '[data-name="your-message"] textarea'
                        if self.sb.is_element_present(message_selector) and self.sb.is_element_visible(message_selector):
                            self.sb.scroll_to(message_selector)
                            self.sb.sleep(random.uniform(0.45, 0.65))
                            
                            message_input = container.find_element("css selector", message_selector)
                            
                            try:
                                self.sb.click(message_selector)
                            except Exception:
                                self.sb.execute_script("arguments[0].focus(); arguments[0].click();", message_input)
                            self.sb.sleep(random.uniform(0.45, 0.65))
                            self._human_type(message_input, f"Test message from form checker. ID: {random.randint(1000, 9999)}")
                    except Exception:
                        # Message field might not exist on all forms
                        print("Message field not found or not accessible, continuing...")

                except Exception as e:
                    raise Exception(f"Could not fill the form properly: {str(e)}")

                # Handle Turnstile CAPTCHA
                if self.sb.is_element_present('.wpcf7-turnstile.cf-turnstile'):
                    print("Turnstile CAPTCHA detected, waiting for completion...")
                    timeout = 150  # seconds
                    start_time = time.time()
                    
                    # Scroll to Turnstile to make sure it's visible
                    self.sb.scroll_to('.wpcf7-turnstile.cf-turnstile')
            
                    while time.time() - start_time < timeout:
                        try:
                            if not USE_HEADLESS:
                                self.sb.switch_to_default_window()
                                # Click on the title bar area (safe from any web content)
                                window_info = self.sb.execute_script("""
                                    return {
                                        x: window.screenX,
                                        y: window.screenY,
                                        width: window.outerWidth,
                                        height: window.outerHeight,
                                        innerHeight: window.innerHeight
                                    };
                                """)
                                safe_x = window_info['x'] + window_info['width'] // 2
                                safe_y = window_info['y'] + 100  # Title bar area, well above content
                                
                                print(f"🖱️ Clicking at safe coordinates ({safe_x}, {safe_y}) to focus window...")
                                
                                # Use SeleniumBase's PyAutoGUI click method
                                with FileLock(lock_file, timeout=150):
                                    try:
                                        self.sb.uc_gui_click_x_y_right_button(safe_x, safe_y, timeframe=0.25)
                                        import pyautogui
                                        pyautogui.press("esc")
                                        self.sb.uc_gui_handle_captcha()
                                    except Timeout:
                                        print("Could not acquire lock for UC browser.")

                            # Check if Turnstile is resolved
                            result = self.sb.execute_script("""
                                const input = document.querySelector('input[name="_wpcf7_turnstile_response"]');
                                return input && input.value.trim() !== "";
                            """)
                            
                            if result:
                                print("✅ Turnstile validated!")
                                break
                                
                            # Show remaining time every 5 seconds
                            elapsed = time.time() - start_time
                            if int(elapsed) % 5 == 0:
                                remaining = int(timeout - elapsed)
                                print(f"⏳ Time remaining: {remaining}s")
                            
                            self.sb.sleep(1)

                        except Exception as e:
                            raise Exception(f"Error checking for turnstile response: {e}")
                    
                    if not result:
                        raise Exception(f"Turnstile response was not completed after {timeout} seconds.")

                # Submit the form
                print("Filled the form. Now submitting...")
                submit_selector = "input.wpcf7-submit"
                
                # Ensure submit button is visible and clickable
                self.sb.scroll_to(submit_selector)
                self.sb.sleep(random.uniform(0.85, 1.05))
                
                # Get submit button element for JavaScript fallback
                submit_button = self.sb.find_element(submit_selector)
                
                # Try multiple approaches to click the submit button
                try:
                    self.sb.click(submit_selector)
                except Exception:
                    try:
                        # Use JavaScript click as fallback
                        self.sb.execute_script("arguments[0].focus(); arguments[0].click();", submit_button)
                    except Exception:
                        # Last resort - direct JavaScript click
                        self.sb.execute_script("document.querySelector('input.wpcf7-submit').click();")

                # Wait for the response
                self.sb.wait_for_element(".wpcf7-response-output", timeout=15)
                response_message = self.sb.get_text(".wpcf7-response-output").lower().strip()
                print("Response message:", response_message)

                if "merci" in response_message and ("envoyé" in response_message or "envoye" in response_message):
                    print("✅ Form submitted successfully!")
                    return
                else:
                    raise Exception(f"Form submission failed: {response_message}")

        except Exception as e:
            # Save diagnostic info
            try:
                self.sb.save_screenshot("error.png")
                html = self.sb.get_page_source()
                with open("error.html", "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception:
                pass
            raise e

@pytest.mark.parametrize("url", load_urls())
def test_multi_threaded(sb, url, request):
    bot = Bot(sb, url)
    try:
        bot.check_contact_form()
    except Exception as e:
        if getattr(request.node, "is_last_try", True):
            bot.send_mail_on_failure("Erreur WordPress (Contact Form)", 
                                        f"L'envoi du formulaire de contact a échoué sur le site {urlparse(url).netloc}.\nErreur: {str(e)}")
        raise
