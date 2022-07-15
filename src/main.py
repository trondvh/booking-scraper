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
    s.post('https://hafjellkvitfjell.r360owner.se/r360/owner/login.php?lang=no', data=login_payload, timeout=15)
    
    return(s)

def fetch_reservations(session):
    reservations_url = "https://hafjellkvitfjell.r360owner.se/r360/owner/reservations.php"
    return(session.get(reservations_url))

def main():
    session = login()

    soup = bs(fetch_reservations(session).text, 'html.parser')
    table = soup.find("table", {"class": "reservations-table r360-table"})
    client = MongoClient(environ["DBSTRING"])

    db = client.booking_scraper
    col = db.bookings

    for row in table.findAll("tr"):
        cells = row.findAll("td")
        booking_entry = cells[1].find(text=True)

        if booking_entry:
            # parse_guests = re.findall(r'\d+', str(cells[3]))
            # guests = list(map(int, parse_guests))
            booking_id = str(booking_entry).strip()
            
            parse_dates = re.findall(
                r'\d\d-\d\d-\d\d', str(cells[2].find(text=True)))

            reservation = {}
            # reservation['adults'] = guests[0]
            # reservation['children'] = guests[1]
            reservation['from_date'] = datetime.strptime(
                parse_dates[0], '%d-%m-%y')
            reservation['to_date'] = datetime.strptime(
                parse_dates[1], '%d-%m-%y')
 
            num_replacements = [(" ", ""), (",", ".")]
            payout = cells[7].find(text=True)

            for pat, repl in num_replacements:
                payout = re.sub(pat, repl, payout)

            reservation['payout'] = float(payout)
            
            print(booking_id)
            print(reservation)

#            result = col.update_one({'_id': booking_id}, {
#                                    "$set": reservation}, upsert=True)

if __name__ == "__main__":
    required_env_vars = {"EMAIL", "PASSWORD", "DBSTRING"}
    diff = required_env_vars.difference(environ)

    if len(diff) > 0:
        sys.exit(f'Missing env variable(s): {diff}')

    main()
