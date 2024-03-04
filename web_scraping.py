import requests
from bs4 import BeautifulSoup


url = 'https://www.sigure.tw/learn-japanese/vocabulary/n5/02-noun-family.php'


response = requests.get(url)


if response.status_code == 200:
    
    soup = BeautifulSoup(response.text, 'html.parser')


    paragraphs = soup.find_all('p')


    for paragraph in paragraphs:
        print(paragraph.text)


    keyword = "尊稱"
    for paragraph in paragraphs:
        if keyword in paragraph.text:
            print(f"Found '{keyword}' in: {paragraph.text}")
else:
    print("Failed to retrieve the web page.")