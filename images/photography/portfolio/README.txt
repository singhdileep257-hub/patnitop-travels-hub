Approved portfolio photos only.

Put a photo here ONLY after the photographer has given written permission and
everyone clearly visible in it has agreed to its use. Netlify publishes this
folder as-is, so any file placed here is publicly reachable by its URL even if
it is not shown on the page. Keep unapproved photos out of this repository.

Then list the photo in data/photographer-portfolio.json with "approved": true
and run python3 build.py. The test suite fails if a file is in this folder
without an approved entry.
