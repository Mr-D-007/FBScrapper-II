from playwright.sync_api import sync_playwright
from pathlib import Path
import os
from utils import (
            Sheet,
            get_input_file_name,
            sanitize_filename,
            download_image, Listing
        )

img_slt = '[class="x6s0dn4 xal61yo x78zum5 xdt5ytf x1iyjqo2 x5yr21d xl56j7k x6ikm8r x10wlt62 x1n2onr6 x87ps6o xh8yej3 x1hyxz0u"] img'
desc_slt = '[class="xz9dl7a x4uap5 xsag5q8 xkhd6sd x126k92a"]'
rows_slt = '[class="x1cy8zhl x78zum5 x1qughib xz9dl7a x4uap5 xsag5q8 xkhd6sd"]'
keys_slt = '[class="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x6prxxf xvq8zen x1s688f xzsf02u"]'
values_slt = '[class="x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x6prxxf xvq8zen xo1l8bm xzsf02u"]'

images_folder = 'images'
current_path = Path(os.getcwd())

# load the sheet
filename = get_input_file_name()
sheet = Sheet(filename, Sheet.option_update)

# create image folder if it doesn't exist
Path(images_folder).mkdir(exist_ok=True)

# initiate the browser
print('Starting the browser....')
HEADLESS = False
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
p = sync_playwright().start()
browser = p.chromium.launch(headless=HEADLESS, args=["--start-maximized"])
context = browser.new_context(user_agent=USER_AGENT, no_viewport=True)
context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
page = context.new_page()

listings = sheet.listings()
# loop through the rows inside the Excel sheet
for listing in listings.iter_rows(min_row=2, values_only=True):
    new_listing = []
    title = listing[0]
    price = listing[1]
    location = listing[2]
    link = listing[3]
    new_listing.append(title)
    new_listing.append(price)
    new_listing.append(location)
    new_listing.append(link)
    # go to the link
    page.goto(link)
    print(f'Scraping:  {link}  {title}')
    page.wait_for_timeout(1000)

    # if there is description then grab it
    desc_elem = page.query_selector(desc_slt)
    if desc_elem is not None:
        # if there is 'See more' button then click it
        if 'See more' in desc_elem.text_content():
            page.get_by_text('See more').click()
            page.wait_for_timeout(200)

        desc_text = desc_elem.text_content()
        new_listing.append(desc_text)

    # by saying rows I mean the rows that contain the attributes, ie. condition, genre, age group
    rows = page.query_selector_all(rows_slt)

    # grab the attributes
    attributes = {}
    for r in rows:
        try:
            key = r.query_selector(keys_slt).text_content()
            value = r.query_selector(values_slt).text_content()
            attributes[key] = value
        except AttributeError:
            print('Attribute error...')

    # save then in the listing object
    if 'Condition' in attributes:
        new_listing.append(attributes['Condition'])
    else:
        new_listing.append('')
    if 'Book Genre' in attributes:
        new_listing.append(attributes['Book Genre'])
    else:
        new_listing.append('')
    if 'Age Group' in attributes:
        new_listing.append(attributes['Age Group'])
    else:
        new_listing.append('')


    # get the image link
    image_link = page.query_selector(img_slt).get_attribute('src')
    # get the image file name
    sanitized_title = sanitize_filename(title)
    image_name = f'{sanitized_title}.jpg'
    # get the image path
    image_path = current_path / images_folder / image_name

    # this logic makes sure if there is already an image saved with the same name
    # then do not overwrite the previous image but instead add a number to the filename to make it unique
    count = 1
    while os.path.exists(image_path):
        image_name = f'{count} {sanitized_title}.jpg'
        image_path = current_path / images_folder / image_name
        count += 1

    download_image(image_path, image_link)
    print(f'Image saved in {image_path}')

    # update the listing object
    new_listing.append(str(image_path))
    new_listing.append(image_link)
    new_listing.append('y')
    sheet.update_listing(new_listing)
    sheet.save()

print('File updated successfully')