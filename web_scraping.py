import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

base_page_link = "https://fidibo.com"

foreign_story_page_link = 'https://fidibo.com/ebooks/story-foreign'

def find_category_links(foreign_story_page_link):
    response = requests.get(
    foreign_story_page_link,
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0"
    }
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    categories_a_tags = soup.find_all("a", class_="base-category-content-box-children-item")
    links=[]
    for tag in categories_a_tags:
        links.append(tag["href"])
    return links


def book_webpage_crawl(link):
    full_link = base_page_link + link
    # Static varibales
    Data = {
        "book_id": int(link.split("/")[2].split("-")[0]),
        "title": "",
        "author": "",
        "translator": "",
        "publisher": "",
        "original_price": "",
        "price": "",
        "discount_percent": "",
        "category": "",
        "format": "",
        "pages": 0,
        "language": "",
        "english_title": "",
        "publish_date": "",
        "print_price": None,
        "rating": "",
        "rating_count": ""

    }
    persian_to_english = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


    # book name from header
    response = requests.get(
    full_link,
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0"
    }
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    header_with_name = soup.select_one("h1", class_="book-main-box-detail-title").get_text(strip=True)
    Data["title"] = header_with_name.split("اثر")[0][5:-1]

    # match = re.search(r"کتاب (.*?) اثر", header_with_name)
    # print(match)
    # book_name = match.group(1)
    # print(book_name)


    # sub header
    sub_header_elements = soup.select("div.book-main-box-detail-author-content")

    Data["author"] = sub_header_elements[0].select_one("a").get_text(strip=True)
    Data["translator"] = sub_header_elements[1].select_one("a").get_text(strip=True)
    Data["publisher"] = sub_header_elements[2].select_one("a").get_text(strip=True)

    # Specifications table
    Specifications_table_rows = soup.find_all("tr", class_="book-vl-rows-item")

    for row in Specifications_table_rows:
        tds = row.find_all("td")
        first_td = tds[0].get_text(strip=True)
        second_td = tds[1].get_text(strip=True)
        match first_td:
            case "فرمت محتوا":
                Data['format']= second_td

            case "تعداد صفحات":
                Data['pages'] = int(second_td.split(" ")[0].translate(persian_to_english))

            case "زبان":
                Data['language'] = second_td
            
            case "عنوان انگلیسی":
                Data['english_title'] = second_td

            case "تاریخ انتشار":
                Data['publish_date'] = second_td.translate(persian_to_english)

            case "قیمت چاپی":
                Data['print_price'] = second_td.split(" ")[0].replace(",", "").translate(persian_to_english)

    # price
    discount = soup.select_one("span.book-buy-box-header-discount-percent-text")
    if discount:
        Data["discount_percent"] = int(discount.get_text(strip=True)[1:])
    
    original_price = soup.select_one("div.book-buy-box-header-discount-price")
    if original_price:
        Data["original_price"] = original_price.get_text(strip=True).replace(",", "").translate(persian_to_english)
    
    price = soup.select_one("div.book-buy-box-header-price-number")
    if price:
        Data["price"] = price.get_text(strip=True).replace(",", "").translate(persian_to_english)

    price_is_free = soup.select_one("div.book-buy-box-header-price-free")
    if price_is_free:
        Data["price"] = 0


    # rating
    Data["rating"] = float(soup.select_one("div.book-rate-content-rate-score").get_text(strip=True))
    
    Data["rating_count"] = int(soup.select_one("div.book-rate-content-responses").get_text(strip=True).split(" ")[2])

    # category
    Data["category"] = soup.select_one("a.material.breadcrumb-name.last").get_text(strip=True)
    

    return Data


def category_crawl(link):
    full_link = base_page_link + link
    response = requests.get(
    full_link,
    headers={
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:156.0) Gecko/20100101 Firefox/156.0"
    }
    )
    soup = BeautifulSoup(response.text, 'html.parser')
    categories_a_tags = soup.find_all("a", class_="content-card-container-item")
    books_links=[]
    for tag in categories_a_tags:
        books_links.append(tag["href"])
    return books_links


category_links = find_category_links(foreign_story_page_link)


all_books = []

for category_link in category_links:

    book_links = category_crawl(category_link)

    for book_link in book_links:
        try:
            book_data = book_webpage_crawl(book_link)
            all_books.append(book_data)
        except Exception as e:
            print(f"Error for {book_link}: {e}")
        time.sleep(5)


df = pd.DataFrame(all_books)

df.to_excel("books.xlsx", index=False)