from math import floor
import json
import os
import requests
from time import sleep
import uule_grabber

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from serpapi import GoogleSearch

load_dotenv()

def get_jobs_serp(query, location=None, n=20):
    html = serpapi_search(query, location)
    jobs = parse_jobs(html)

    #while len(jobs) + 10 <= n:
    #    html = serpapi_search(query, location, start=len(jobs))
    #    jobs += parse_jobs(html)
    
    return jobs

def get_jobs_manual(query, location=None, n=20):
    html = google_search(query, location)
    jobs = parse_jobs(html)
    recent_query_len = len(jobs)

    while len(jobs) + 10 <= n and recent_query_len > 0:
        sleep(1)
        html = google_search(query, location, start=len(jobs))
        recent_jobs = parse_jobs(html)
        recent_query_len = len(recent_jobs)
        jobs += recent_jobs
    
    if len(jobs) > 0: print(f"{len(jobs)} postings")
    return jobs

def google_search(query, location=None, start=0):
    # Use bs4 to return the html
    url = f"https://www.google.com/search?ie=UTF-8&ibp=htl;jobs"

    params = {
        "q": query,
        "start": start,
        "chips": "date_posted:week",
        "uule": uule_grabber.uule(location),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 14526.89.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36"
    }

    res = requests.get(url, headers=headers, params=params)
    html_page = res.content
    #soup = BeautifulSoup(html_page, "html.parser")

    return html_page

def serpapi_search(query, location, start=0): 
    params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google_jobs",
        "google_domain": "google.com",
        "output": "html",
        "q": query,
        }

    if location:
        params["location"] = location

    if start > 0:
        params["start"] = start

    search = GoogleSearch(params)
    html = search.get_html()
    
    return html

def parse_jobs(html):
    # for now load example_html in bs4
    #with open("src/app/data/example_serp2.html") as f:
    #    html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    job_dict = []

    # find elements with class name "pE8vnd avtvi"
    posting_elements = soup.find_all("div", class_="pE8vnd avtvi")
    if posting_elements:
        #print(f"{len(posting_elements)} postings")
        pass
    else:
        print("No postings")
    for i, posting in enumerate(posting_elements):
        output = dict()

        # find all elements with class name "KLsYvd"
        title_element = posting.find("h2", class_="KLsYvd")
        output["title"] = title_element.text

        # find all elements with class name "sMzDkb"
        company_elements = posting.find_all("div", class_="sMzDkb")
        if len(company_elements) == 2:
            output["company"] = company_elements[0].text
            output["location"] = company_elements[1].text
        elif len(company_elements) == 1:
            output["company"] = company_elements[0].text
            output["location"] = None

        # find all elements with all 3 classes "pMhGee Co68jc j0vryd"
        application_element = posting.select('a.pMhGee.Co68jc.j0vryd')[0]
        output["app_link"] = application_element["href"]
        output["app_text"] = application_element["title"]

        # concatenate all job info into a string
        info_string = ""

        # "Job highlights": get all text from the table in the div with class "JvOW3e"
        table_element = posting.find("div", class_="JvOW3e")
        if table_element:
            table_element = table_element.find("table")
            info_string += table_element.text + "\n"

        # "Job description"
        description_string = ""
        collapsed_description_element = posting.find("span", class_="HBvzbc")
        if collapsed_description_element:
            description_string += collapsed_description_element.text
        expanded_description_element = posting.find("div", class_="WbZuDe")
        if expanded_description_element:
            description_string += expanded_description_element.text
        info_string += description_string

        # Remove all quotes from info_string
        info_string = info_string.replace('"', "").replace("'", "")

        output["info"] = info_string

        job_dict.append(output)

    return job_dict