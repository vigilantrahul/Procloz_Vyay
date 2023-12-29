# import pytesseract
import os
import glob
import easyocr
import re
from dateutil import parser
from datetime import datetime

# import torch
# device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# Finding establishment name
def fetch_establishment_name(result):
    establishment_key = ['OPERATED', 'BY']
    establishment_name = None
    for i in range(len(result)):
        text = result[i][1]
        contains_numbers_or_date = any(char.isdigit() or char == "-" for char in text)
        if not contains_numbers_or_date:
            establishment_name = text
            found_key = True  # Set to True initially
            for j in establishment_key:
                key = j
                if key.lower() in text.lower():
                    found_key = False
                    break
            if found_key:
                # print(f"Establishment Name on the bill is: {establishment_name}")
                return establishment_name


def fetch_bill_date(result):
    bill_date = ""
    date_keyword = "Date"
    for j in range(len(result)):
        text = result[j][1]
        # text = ''.join(char for char in text if not char.isalpha())
        if len(text) >= 8:
            # if date_keyword.lower() in text.lower() and text.count("/")==2 or text.count("-")==2 or text.count(":")==2:
            if date_keyword.lower() in text.lower() or text.count("/") == 2 or text.count("-") == 2:
                text = result[j][1]
                bill_date = re.sub(r'[a-zA-Z\s]', '', text)
                break
            else:
                if len(bill_date) < 5:
                    bill_date = datetime.now().strftime('%Y/%m/%d')

    # print(f"bill date is {bill_date}")
    return bill_date


# finding bill amount
def fetch_bill_amount(result):
    keyword = ["Grand Total", 'Total']
    total_bill_amount = None

    # finding bill_amount
    for detection in range(len(result)):
        text = result[detection][1]
        for k in keyword:
            word = k
            if k.lower() in text.lower():
                next_text = result[detection + 1][1]
                next_text = next_text.replace(',', '', next_text.count(',') - 1)
                next_text = next_text.replace(',', '.')
                total_bill_amount = re.sub(r'[^0-9.]', '', next_text)
                break

    # print(f"Total Bill Amount is: {total_bill_amount}")
    return total_bill_amount


def fetch_bill_number(result):
    # finding bill number
    keyword = ['Aereipt No', "Bill No", 'Invoice', 'Transaction', 'Receipt No']
    bill_number = None
    # finding bill_amount
    for detection in range(len(result)):
        text = result[detection][1]
        for k in keyword:
            word = k
            if k.lower() in text.lower():
                next_text = result[detection + 1][1]
                next_text = next_text.replace(',', '', next_text.count(',') - 1)
                next_text = next_text.replace(',', '.')
                bill_number = next_text
                break

        # print(f"The Bill Number is: {bill_number}")
    return bill_number


def get_ocr_data(file):
    file_content = file.read()
    reader = easyocr.Reader(['en'])
    img_name = file_content
    result = reader.readtext(img_name)
    establishment_name = fetch_establishment_name(result)
    bill_date = fetch_bill_date(result)
    bill_amount = fetch_bill_amount(result)
    bill_number = fetch_bill_number(result)

    return {
        "billNumber": bill_number,
        "billAmount": bill_amount,
        "billDate": bill_date,
        "establishmentName": establishment_name
    }
