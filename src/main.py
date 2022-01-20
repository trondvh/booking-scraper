import re
import sys
import requests
from os import environ
from bs4 import BeautifulSoup as bs
from pymongo import MongoClient
from datetime import datetime

def login():
    login_payload = {
        'email': environ["EMAIL"],
        'pass': environ["PASSWORD"],
        'action': 'login',
        'login_form_api': '/r360/owner/login.php'
    }

    s = requests.session()
    s.post('https://hafjellkvitfjell.restech.se/r360/owner/login.php?site=hafjellkvitfjell&lang=NO', data=login_payload, timeout=15)
    
    return(s)

def fetch_reservations(session):
    reservations_url = "https://hafjellkvitfjell.restech.se/r360/owner/reservations.php"
    return(session.get(reservations_url))

def main():
    session = login()

    soup = bs(fetch_reservations(session).text, 'html.parser')
    table = soup.find("table", {"class": "reservationsTable"})
    
    client = MongoClient(environ["DBSTRING"])

    db = client.booking_scraper
    col = db.bookings

    for row in table.findAll("tr"):
        cells = row.findAll("td")
        if len(cells) == 10:
            parse_guests = re.findall(r'\d+', str(cells[3]))
            parse_dates = re.findall(
                r'\d\d\d\d-\d\d-\d\d', str(cells[2].find(text=True)))

            guests = list(map(int, parse_guests))

            reservation = {}
            booking_id = cells[1].find(text=True)
            reservation['adults'] = guests[0]
            reservation['children'] = guests[1]
            reservation['from_date'] = datetime.strptime(
                parse_dates[0], '%Y-%m-%d')
            reservation['to_date'] = datetime.strptime(parse_dates[1], '%Y-%m-%d')
            reservation['payout'] = float(
                re.sub(r'[^0-9.]', '', cells[8].find(text=True)))

            result = col.update_one({'_id': booking_id}, {
                                    "$set": reservation}, upsert=True)

            print(cells[1].find(text=True), cells[2].find(
                text=True), cells[3], cells[8].find(text=True))

if __name__ == "__main__":
    required_env_vars = {"EMAIL", "PASSWORD", "DBSTRING"}
    diff = required_env_vars.difference(environ)

    if len(diff) > 0:
        sys.exit(f'Missing env variable(s): {diff}')

    main()
