import json

from constants import (
    DESIRED_NUM_POSTINGS,
    RESUME_EMBEDDING_DIRECTORY,
    TEMP_DIRECTORY,
)

from models.ponydb import store_jobs, freshen_jobs, retrieve_relevant_jobs_from_db
from pony import orm

from scripts.jobsearch import get_jobs_manual, parse_jobs
from scripts.resume_utils import get_text as extract_resume_text
from scripts.tokenize_and_embed import embed_resume

def _parser():
    import argparse

    parser = argparse.ArgumentParser(description="Better job search")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-r', '--resume')
    group.add_argument('-c', '--cached', action='store_true')

    group2 = parser.add_mutually_exclusive_group(required=False)
    group2.add_argument('-q', '--query', action='store_true') # just to query existing records
    group2.add_argument('-s', '--search', action='store_true') # just to see fresh search results

    return parser

def _get_filename_from_path(path):
    """Gets the filename from a path"""
    return path.split("/")[-1].split(".")[0]

def _write_text_to_file(text, destination_path):
    """Writes text to a filepath"""
    import datetime
    with open(destination_path, 'w') as f:
        f.write(text)

    return destination_path

def _write_embedding_to_file(embedding, destination_path):
    """Saves an embedding as json dump to a filepath"""
    import json
    with open(destination_path, 'w') as f:
        json.dump(embedding, f)

    return destination_path

def _load_most_recent_json_file(directory):
    """Loads the most recent file in a directory as json"""
    import os
    import json
    import datetime

    # get all files in directory
    files = [f'{directory}/' + f for f in os.listdir(directory)]
    # get the most recent file
    most_recent_file = max(files, key=os.path.getctime)
    # print the filename of the most recent file
    # print(f"{most_recent_file}")
    # load the most recent file
    with open(f"{most_recent_file}", 'r') as f:
        most_recent_json = json.load(f)

    return most_recent_json

def _remove_file(path):
    """Removes a file"""
    import os
    os.remove(path)

def _validate_args():
    parser = _parser()
    args = parser.parse_args()
    return args

def _check_filenames_for_match(filename, directory):
    """Checks all files in directory, returning true if there is a file with name filename. Extensions do not have to match"""
    import os
    import re

    filenames = os.listdir(directory)
    for f in filenames:
        if re.match(filename, f):
            return True

    return False

def _embed_resume_from_path(path):
    filename = _get_filename_from_path(path)

    if not _check_filenames_for_match(filename, RESUME_EMBEDDING_DIRECTORY):
        resume_path = args.resume
        tmp_filepath = f"{TEMP_DIRECTORY}/{_get_filename_from_path(resume_path)}.txt"
        extracted_text = extract_resume_text(filename=resume_path)
        _write_text_to_file(extracted_text, tmp_filepath)  

        embedded_resume = embed_resume(filepath=tmp_filepath)
        _remove_file(tmp_filepath)
        _write_embedding_to_file(embedded_resume, destination_path=f"{RESUME_EMBEDDING_DIRECTORY}/{_get_filename_from_path(resume_path)}.json")
    else:
        print(f"cached embedding found for filename: {filename}")

def _retrieve_jobs_from_query(query, location=None):
    jobs = get_jobs_manual(query=query, location=location, n=DESIRED_NUM_POSTINGS)
    return jobs

def _print_result(jobs_iterable):
    for job in jobs_iterable:
        print(f"{job.relevance_score}: {job.title} at {job.company} in {job.location if job.location else 'N/A'}")

if __name__ == '__main__':
    args = _validate_args()
    freshen_jobs()
    
    jobsearch_query = input("Find these jobs for me: ")
    location_input = input("Location (wip): ")

    if args.search:
        found_jobs = _retrieve_jobs_from_query(query=jobsearch_query, location=location_input)
        newly_stored_jobs = store_jobs(job_list=found_jobs)
        all_relevant_jobs = newly_stored_jobs
    elif args.query:
        relevant_jobs_in_db = retrieve_relevant_jobs_from_db(query=jobsearch_query)
        all_relevant_jobs = relevant_jobs_in_db
    else:
        relevant_jobs_in_db = retrieve_relevant_jobs_from_db(query=jobsearch_query)
        found_jobs = _retrieve_jobs_from_query(query=jobsearch_query, location=location_input)
        newly_stored_jobs = store_jobs(job_list=found_jobs)
        all_relevant_jobs = newly_stored_jobs + relevant_jobs_in_db

    _print_result(jobs_iterable=all_relevant_jobs)