# jobscli
### Find the most relevant jobs for you, from your command line, with the power of embeddings.
(no SerpAPI dependency because I'm built different)

## First-time usage
- Create a `.env` file with an `OPENAI_API_KEY`.
- Run `python driver.py -r RESUME_PATH` to embed and store your resume.

## Not first-time usage
- Run `python driver.py -c` to use a cached resume.
- Add the `-q` flag to query previously scraped job records OR the `-s` flag to ignore them and only see new ones.
