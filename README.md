# LinkedIn Company Scraper

A Python-based web scraper to extract company information from LinkedIn search results, including company names, LinkedIn URLs, descriptions, email addresses (when available), and website URLs.

## Features

- Search companies by keyword and location
- Extract company LinkedIn URLs
- Attempt to find email addresses from company pages
- Export results to CSV format
- Configurable search parameters
- Both GUI and headless browser modes

## Prerequisites

- Python 3.8+
- Chrome browser installed
- LinkedIn account with valid credentials

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your LinkedIn credentials:
   ```bash
   cp .env.example .env
   ```
   
4. Edit the `.env` file and add your LinkedIn credentials:
   ```
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   HEADLESS_MODE=false
   DELAY_BETWEEN_REQUESTS=3
   MAX_PAGES=5
   ```

## Usage

### Option 1: Command Line Interface (Recommended)

```bash
python run_scraper.py --search "sportswear" --location "amsterdam" --output "sportswear_amsterdam.csv"
```

**Available options:**
- `--search`, `-s`: Search term (required)
- `--location`, `-l`: Location (required) 
- `--output`, `-o`: Output CSV filename (default: linkedin_companies.csv)
- `--pages`, `-p`: Maximum pages to scrape (default: 5)
- `--headless`: Run in headless mode (no browser window)

### Option 2: Direct Script Execution

Edit the `linkedin_scraper.py` file to change the search term and location, then run:

```bash
python linkedin_scraper.py
```

## Output

The scraper generates a CSV file with the following columns:

- **Company Name**: Name of the company
- **LinkedIn URL**: Direct link to the company's LinkedIn page
- **Description**: Company description from LinkedIn
- **Email**: Email address (if found on the company page)
- **Website**: Company website URL (if available)
- **Search Term**: The search term used
- **Location**: The location searched

## Configuration

You can modify the scraping behavior by updating the `.env` file:

- `HEADLESS_MODE`: Set to `true` to run without opening browser windows
- `DELAY_BETWEEN_REQUESTS`: Delay in seconds between page requests (recommended: 2-5)
- `MAX_PAGES`: Maximum number of search result pages to scrape

## Important Notes

### Email Detection
- Emails are extracted using regex patterns from company pages
- LinkedIn rarely displays direct email addresses publicly
- The scraper checks company descriptions and contact sections
- Email extraction success rate may be low due to LinkedIn's privacy policies

### Rate Limiting
- The scraper includes delays between requests to avoid being blocked
- Use reasonable values for `DELAY_BETWEEN_REQUESTS` (2-5 seconds)
- Don't set `MAX_PAGES` too high to avoid detection

### Legal Compliance
- Ensure your use complies with LinkedIn's Terms of Service
- Use the scraper responsibly and respect rate limits
- Consider LinkedIn's robots.txt and API alternatives for commercial use

## Troubleshooting

### Chrome Driver Issues
If you encounter Chrome driver issues:
```bash
pip install --upgrade webdriver-manager
```

### Login Issues
- Verify your LinkedIn credentials in the `.env` file
- Check if your account requires 2FA (currently not supported)
- Ensure your account is not restricted

### No Results Found
- Try different search terms
- Check if the location is spelled correctly
- Reduce the number of pages if getting blocked

### Memory Issues
- Run in headless mode to reduce memory usage
- Reduce the number of pages scraped
- Close other applications while running

## Sample Output

```csv
Company Name,LinkedIn URL,Description,Email,Website,Search Term,Location
Nike Inc.,https://www.linkedin.com/company/nike,Athletic footwear and apparel company,,https://nike.com,sportswear,amsterdam
Adidas Group,https://www.linkedin.com/company/adidas-group,Sports apparel manufacturer,,https://adidas.com,sportswear,amsterdam
```

## License

This project is for educational purposes only. Users are responsible for complying with LinkedIn's Terms of Service and applicable laws.
