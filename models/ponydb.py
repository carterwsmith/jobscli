from pony.orm import *
from datetime import datetime, timedelta
import json

if __name__ == '__main__':
    from commands.embed import embed_job_from_dict
    from commands.score import score_job_from_dict, _load_most_recent_json_file, score_job_from_embedding
else:
    from models.commands.embed import embed_job_from_dict
    from models.commands.score import score_job_from_dict, _load_most_recent_json_file, score_job_from_embedding

def init_db():
    db = Database()
    db.bind(provider='sqlite', filename='database.sqlite', create_db=True)

    return db

database = init_db()

class Job(database.Entity):
    updated_at = Required(datetime,
                          default=datetime.utcnow())
    title = Required(str)
    company = Required(str)
    location = Optional(str, nullable=True)
    app_link = Required(str)
    app_text = Optional(str)
    info = Optional(str)

    embedding_json = Optional(str)
    relevance_score = Optional(float)

database.generate_mapping(create_tables=True)

def _does_job_exist(job):
    """Returns true if a job already exists in the database"""
    with db_session:
        return Job.get(title=job['title'], company=job['company']) is not None 

def store_jobs(job_list):
    """Stores a list of jobs in the database"""
    resume_embedding = _load_most_recent_json_file('cache/embeddings')
    stored_list = []
    with db_session:
        for job in job_list:
            # create a job to store in the db unless it already exists
            if not _does_job_exist(job):
                embedding = embed_job_from_dict(job)
                embedding_str = json.dumps(embedding)
                score = score_job_from_embedding(job_embedding=embedding, resume_embedding=resume_embedding)

                new_stored_job = Job(title=job['title'], company=job["company"], location=job["location"], app_link=job["app_link"], app_text=job["app_text"], info=job["info"], embedding_json=embedding_str, relevance_score=score)
                stored_list.append(new_stored_job)
    return stored_list

def _count_all_jobs():
    """Returns the number of jobs in the database"""
    with db_session:
        return Job.select().count()

def _backfill_job_embeddings():
    """Backfills the embeddings for all jobs in the database if the embedding does not exist"""
    with db_session:
        for job in select(j for j in Job if j.embedding_json == ''):
            job.embedding_json = json.dumps(embed_job_from_dict(job.to_dict()))
            print("Backfilled")

def _get_n_grams(in_string, n=2):
    """
    Return all consecutive phrases of words of length n in a string (that do not contain a stopword)
    """
    from nltk.corpus import stopwords
    stopwords_nltk = set(stopwords.words('english'))

    words = in_string.split()

    if len(words) == 1:
        return [words[0]]

    n_grams = []
    for i in range(len(words) - n + 1):
        if not any(word in stopwords_nltk for word in words[i:i+n]):
            n_grams.append(' '.join(words[i:i+n]))

    return n_grams

def _backfill_job_relevance_scores():
    """Backfills the relevance scores for all jobs in the database if the score does not exist"""
    resume_embedding = _load_most_recent_json_file('cache/embeddings')
    with db_session:
        for job in select(j for j in Job if j.relevance_score == 0.0 or j.relevance_score is None):
            job.relevance_score = score_job_from_dict(job.to_dict(), resume_embedding)
            print("Backfilled")

def _delete_jobs_with_word_in_title(word):
    """Deletes all jobs with a given word in the title"""
    with db_session:
        for job in select(j for j in Job if word.lower() in j.title.lower()):
            job.delete()
            print("Deleted")

def retrieve_relevant_jobs_from_db(query):
    """Retrieves jobs where any n gram in the query is present in the title or info (case insensitive) sorted by relevance score"""
    n_grams = _get_n_grams(query)
    jobs = []
    with db_session:
        for n_gram in n_grams:
            jobs += select(j for j in Job if n_gram.lower() in j.title.lower() or n_gram.lower() in j.info.lower())
    # filter jobs to have relevance score geq to 77
    jobs = [j for j in jobs if j.relevance_score >= 77]
    return sorted(jobs, key=lambda j: j.relevance_score, reverse=True)

def freshen_jobs():
    """Removes all jobs that have an updated_at date greater than 7 days ago"""
    if _count_all_jobs() > 0:
        with db_session:
            valid_jobs = Job.select(lambda j: j.updated_at < datetime.utcnow() - timedelta(days=7))
            if len(valid_jobs) > 0:
                valid_jobs.delete(bulk=True)