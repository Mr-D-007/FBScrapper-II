from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
from utils import (
            Listing, Sheet,
            scroll_page, clean_price_text,
            find_available_file_name,
            get_listing_scrape_count,
            analyze_text_with_chatgpt
        )
import os

# selectors to interact with the website
listings_slt = '[aria-label="Collection of Marketplace items"] a[href*="/marketplace/item/"]'
listing_info_slt = '[class="x9f619 x78zum5 xdt5ytf x1qughib x1rdy4ex xz9dl7a xsag5q8 xh8yej3 xp0eagm x1nrcals"] [class="x1gslohp xkh6y0r"]'

# get input for the scrape count
total_scrape_limit = get_listing_scrape_count()

print('Initiating the browser....')
# initiate the browser
HEADLESS = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
p = sync_playwright().start()
browser = p.chromium.launch(headless=HEADLESS, args=["--start-maximized"])
context = browser.new_context(user_agent=USER_AGENT, no_viewport=True, storage_state=None)
context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
page = context.new_page()

# go to the website
page.goto('https://www.facebook.com/marketplace/nyc/search/?query=textbooks', timeout=60000)

# login
try:
    username = input('Enter your username. - ')
    password = input('Enter your password. - ')
    id_element = page.locator('#login_form > div.x9f619.x1n2onr6.x1ja2u2z.x2lah0s.x13a6bvl.x6s0dn4.xozqiw3.x1q0g3np.x1pi30zi.x1swvt13.xexx8yu.xcud41i.x139jcc6.x4cne27.xifccgj.x1s85apg.x3holdf > div:nth-child(1) > label > input')
    id_element.click()
    page.wait_for_timeout(2000)
    page.keyboard.type(username)
    page.wait_for_timeout(2000)
    page.keyboard.press('Tab')
    page.wait_for_timeout(1000)
    page.keyboard.type(password)
    page.wait_for_timeout(2000)
    page.keyboard.press('Enter')
    page.wait_for_timeout(5000)
except Exception as error:
    print(error)

# Here the program pauses for you to tinker with the parameters in the website
while True:
    user_input = input(f'Going to scrape {total_scrape_limit} listings. Press "y" to continue: ')
    # Click on date listed element to sort data
    date_listed = page.locator('#seo_filters > div:nth-child(2) > div:nth-child(6) > div.x9f619.x78zum5.xl56j7k.xs9asl8.xurb0ha.x1iorvi4.xh8yej3 > div.x1iyjqo2.xu06os2.xk9mzb7.xeuugli > span > span')
    print(date_listed.evaluate('(element) => element.textContent'))
    date_listed.click()
    
    # Wait for 2 seconds (2000 milliseconds)
    page.wait_for_timeout(2000)
    
    # Sort by last 24 Hours
    sort_by = page.locator('#seo_filters > div:nth-child(2) > div.x153efwv.xxqldzo > div > div.x78zum5.xdt5ytf.x1iyjqo2.x1n2onr6 > div:nth-child(2) > div > div.x6s0dn4.x1q0q8m5.x1qhh985.xu3j5b3.xcfux6l.x26u7qi.xm0m39n.x13fuv20.x972fbf.x9f619.x78zum5.x1q0g3np.x1iyjqo2.xs83m0k.x1qughib.xat24cr.x11i5rnm.x1mh8g0r.xdj266r.xeuugli.x18d9i69.x1sxyh0.xurb0ha.xexx8yu.x1n2onr6.x1ja2u2z.x1gg8mnh > div > div.x1qjc9v5.x1q0q8m5.x1qhh985.xu3j5b3.xcfux6l.x26u7qi.xm0m39n.x13fuv20.x972fbf.x9f619.x78zum5.x1r8uery.xdt5ytf.x1iyjqo2.xs83m0k.x1qughib.xat24cr.x11i5rnm.x1mh8g0r.xdj266r.x2lwn1j.xeuugli.x4uap5.xkhd6sd.xz9dl7a.xsag5q8.x1n2onr6.x1ja2u2z > div > div > div > span')
    print(sort_by.evaluate('(element) => element.textContent'))
    sort_by.click()
    
    # Wait for 2 seconds
    page.wait_for_timeout(2000)
    
    if user_input.lower() == 'y':
        break

# Create the Excel sheet if it doesn't exist, or load it if it exists
filename = find_available_file_name()
if not os.path.exists(filename):
    sheet = Sheet(filename, Sheet.option_create)
else:
    sheet = Sheet(filename, Sheet.option_update)


# keep scraping input until we reach the limit provided in the input above
while sheet.listing() < total_scrape_limit:
    listings_elements = page.query_selector_all(listings_slt)
    
    for lst in listings_elements:
        
        # # if you want to check the description with chatGPT
        # while True:
        #     check = input('Do you want to check text with chatGPT to analyse if it is to trade something.\n If yes press "y" else "n".')
        #     if check == 'y':
        #         your_api_key = input('Please Enter your api key here.')
        #         # check if item is for sell/buy through chatGPT
        #         text = lst.evaluate('(element) => element.textContent')
        #         text += ' check if description is to buy or sell something'
        #         response = analyze_text_with_chatgpt(text=text, api_key=your_api_key)
        #         result = response['choices']['message']['content']
        #         print(f'result = {result}')
        #         # check the result text from chatGPT
        #         if 'Yes' in result or 'to buy' in result or 'to sell' in result:
        #             print('Yes, the post is related to trading something.')
        #         # # if you want to skip the current iteration
        #         # else:
        #         #     continue
        #     elif check == 'n':
        #         break
        
        # get the listing link
        unparsed_link = lst.get_attribute('href')
        relative_link = unparsed_link.split('?')[0]    # get rid of query parameters, we don't need it
        base_url = 'https://www.facebook.com/'
        absolute_link = urljoin(base_url, relative_link)   # get the complete link by joining relative link and base url

        # if the listing is already scraped then skip it
        if sheet.contains(absolute_link):
            continue

        # read the 3 text lines of listings below the thumbnail
        text_lines = lst.query_selector_all(listing_info_slt)
        lines = [line.text_content() for line in text_lines]

        # grab the price
        price = lines[0]
        # sometimes there is a discounted price with the original price, ie 15$20$. so get rid of 20$ in this example
        price = clean_price_text(price)
        # grab the title and location
        title = lines[1]
        location = lines[2]

        # create a listing object
        listing = Listing(
                    title=title,
                    price=price,
                    location=location,
                    link=absolute_link
                    )

        # add the listing object
        sheet.add_listing(listing)  # the sheet class will automatically update the Excel sheet
        # store the sheet
        sheet.save()
        
    # show the scraped count
    print(f'Listings scraped: {sheet.listing()}')
    # scroll down the page
    scroll_page(page, 1)

# finally show that the output is saved
print(f'Output saved in: {filename}')
