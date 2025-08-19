import os
import re
import time
import urllib.parse

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Load environment variables
load_dotenv()

# LinkedIn credentials
EMAIL = os.getenv("LINKEDIN_EMAIL")
PASSWORD = os.getenv("LINKEDIN_PASSWORD")
DELAY = int(os.getenv("DELAY_BETWEEN_REQUESTS", 3))
MAX_PAGES = int(os.getenv("MAX_PAGES", 5))


class LinkedInScraper:
    def __init__(self, search_term=None):  # Make search_term optional
        self.search_term = search_term
        self.results = []
        # Don't initialize driver yet - will be done after search term is provided
        self.driver = None
        self.wait = None

    def prompt_search_term(self):
        """Prompt user for search term if not provided during initialization"""
        if not self.search_term:
            self.search_term = input(
                "Enter search term (e.g., 'sportswear', 'tech companies'): "
            ).strip()

    def _initialize_driver(self):
        """Initialize the browser driver and wait object"""
        if not self.driver:
            self.driver = self._setup_driver()
            self.wait = WebDriverWait(self.driver, 30)

    def _setup_driver(self):
        options = Options()

        # Set a desktop user agent
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Set window size for desktop view
        # options.add_argument('--window-size=1920,1080')
        options.add_argument("--start-maximized")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Enable headless mode if specified in .env
        # if HEADLESS_MODE:
        #    options.add_argument("--headless=new")
        #    options.add_argument("--disable-gpu")
        #    options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Set viewport size after browser is created (if not headless, maximize)
        driver.maximize_window()

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return driver

    def login(self):
        try:
            print("Logging into LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")

            # Wait for and fill username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(EMAIL)

            # Fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(PASSWORD)

            # Click login button
            login_button = self.driver.find_element(
                By.XPATH, "//button[@type='submit']"
            )
            login_button.click()

            # Wait for login to complete
            self.wait.until(EC.url_contains("linkedin.com/feed"))
            print("Successfully logged in!")
            time.sleep(2)

        except TimeoutException:
            print("Login failed or took too long")
            raise

    def extract_email_from_text(self, text):
        """Extract email addresses from text using regex, ignoring image assets and common false positives"""
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, text)
        # Filter out emails that are actually image assets or common false positives
        filtered_emails = [
            e
            for e in emails
            if not re.search(
                r"\.(png|jpg|jpeg|gif|svg|webp|ico|bmp)$", e, re.IGNORECASE
            )
            and not e.startswith("entity-circle-pile-chat")
        ]
        return filtered_emails[0] if filtered_emails else None

    def get_company_details(self, company_url):
        """Visit company page to extract additional details including email and website email"""
        try:
            if not company_url.startswith("https://www.linkedin.com"):
                company_url = "https://www.linkedin.com" + company_url

            print(f"Visiting company page: {company_url}")
            self.driver.get(company_url)
            time.sleep(DELAY)

            # Get company description and contact info
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")

            # 1. Try to find email in the entire page content first
            email = self.extract_email_from_text(page_source)

            # 2. Try to find the company website link
            website_url = None
            website_link = soup.find(
                "a",
                href=True,
                attrs={
                    "data-control-name": "page_details_module_website_external_link"
                },
            )
            if not website_link:
                # Fallback: look for any external link that isn't LinkedIn
                website_link = soup.find(
                    "a", href=True, string=re.compile(r"website", re.I)
                )
            if not website_link:
                # Fallback: look for any external link that isn't LinkedIn
                website_link = soup.find("a", href=True, attrs={"target": "_blank"})
            if website_link:
                href = website_link["href"]
                if href and "linkedin.com" not in href:
                    website_url = href

            # 3. If no email found on LinkedIn, try the company website
            website_email = None
            if not email and website_url:
                try:
                    print(f"Visiting company website: {website_url}")
                    # Use a new Selenium tab to avoid losing LinkedIn session
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get(website_url)
                    time.sleep(DELAY)
                    website_source = self.driver.page_source
                    website_email = self.extract_email_from_text(website_source)
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception as e:
                    print(f"Error scraping website: {e}")
                    website_email = None

            # Prefer LinkedIn email, otherwise use website email
            final_email = email or website_email

            return {"email": final_email, "website": website_url}

        except Exception as e:
            print(f"Error extracting details: {e}")
            return {"email": None, "website": None}

    def search_companies(self):
        try:
            # URL encode the search terms
            encoded_search = urllib.parse.quote(self.search_term)

            print(f"Searching for companies: {self.search_term}")

            for page in range(1, MAX_PAGES + 1):
                print(f"Scraping page {page}...")

                # Construct search URL with fixed parameters
                search_url = (
                    f"https://www.linkedin.com/search/results/companies/"
                    f"?companyHqGeo=%5B%22104738515%22%2C%22101165590%22%5D"
                    f"&keywords={encoded_search}"
                    f"&origin=FACETED_SEARCH"
                    f"&sid=WrT"
                    f"&page={page}"
                )

                self.driver.get(search_url)
                time.sleep(DELAY * 2)  # Give more time for the page to load completely

                # Find all company profile links on the page
                company_links = set()
                link_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "a[data-test-app-aware-link][href*='/company/']"
                )
                for link in link_elements:
                    href = link.get_attribute("href")
                    # Filter out admin/inbox or other non-profile links
                    if href and "/company/" in href and "/admin" not in href:
                        company_links.add(href)

                print(
                    f"Found {len(company_links)} company profile links on page {page}"
                )

                for company_url in company_links:
                    try:
                        print(f"Processing company URL: {company_url}")
                        details = self.get_company_details(company_url)
                        self.results.append(
                            {"LinkedIn URL": company_url, "Email": details["email"]}
                        )
                        time.sleep(DELAY)
                    except Exception as e:
                        print(f"Error processing company: {e}")
                        continue

                # Add delay between pages
                time.sleep(DELAY)

        except Exception as e:
            print(f"Error during search: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.quit()

    def save_results(self, filename=None):
        if self.results:
            # Create filename with search term if not provided
            if filename is None:
                # Sanitize search term for filename (remove special characters)
                safe_search_term = re.sub(r"[^\w\s-]", "", self.search_term).strip()
                safe_search_term = re.sub(r"[-\s]+", "_", safe_search_term)
                filename = f"linkedin_companies_{safe_search_term}.csv"

            df = pd.DataFrame(self.results)
            df.to_csv(filename, index=False)
            print(f"Saved {len(self.results)} companies to {filename}")
        else:
            print("No results to save")

    def scrape(self):
        try:
            if not EMAIL or not PASSWORD:
                raise ValueError(
                    "LinkedIn credentials not found. Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file"
                )

            # Ensure we have a search term
            self.prompt_search_term()
            if not self.search_term:
                raise ValueError("Search term is required")

            # Initialize driver after getting search term
            self._initialize_driver()

            self.login()
            self.search_companies()

        except Exception as e:
            print(f"Scraping failed: {e}")
        finally:
            self.close()

        self.save_results()


if __name__ == "__main__":
    scraper = LinkedInScraper()  # No search term provided - will prompt user
    scraper.scrape()
    print("Scraping completed. Results saved in 'linkedin_companies.csv'.")
