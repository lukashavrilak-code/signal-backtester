# Signal Backtester: project rules

Portfolio project: a retrospective backtest of PRR/ROR signal detection on FDA FAERS data,
published as a static website. The working plan is `docs/PLAN.md` (local only, git-ignored).

## Language: English only

- Everything written into this project is in English: code (names, comments, docstrings), SQL,
  YAML/CSV/JSON content, tests, documentation, commit messages, branch names, pull requests
  and issues, CLI output, log and error messages, website text, LLM prompts and AI drafts.
- Never add Slovak or any other non-English text to a file. If you find some, translate it.
- One exception: verbatim quotes from non-English official sources (the `quote` field in
  `config/studies/*.yaml`) stay in the original language.
- The author chats in Slovak. Reply in Slovak in the chat, and never copy chat text into files.

## Working rules

- Readable code over clever abstractions. One responsibility per module, about 200 lines at most.
  The author must be able to explain every module in a job interview.
- `study` means one historical drug–event pair (there are six). `case` means a FAERS case (CASEID).
  Never use one word for the other.
- Statistics are computed in SQL (`sql/`) and Python only. JavaScript renders, sorts and filters;
  it never derives a metric, a threshold or a date.
- Pre-registration: the definitions in `config/` are frozen and tagged before any result is
  computed on real FAERS data. Before that tag exists, do not run a query that counts a study's
  drug and event together. After it, log every change of a definition in `docs/METHODOLOGY.md`.
- Regulatory dates live only in `config/studies/*.yaml`, each with a source and a `verified_on`
  date set by the author. Do not change a verified date without asking the author.
- Secrets stay in `.env` (git-ignored) and in GitHub Actions secrets.
- When explaining an IT concept to the author, be direct and factual, without analogies from
  medicine or biology.

## Commands

uv is installed through pip on this machine, so it runs as `python -m uv`.

- `python -m uv sync` installs the locked environment
- `python -m uv run pytest` runs the tests
- `python -m uv run ruff check .` and `python -m uv run ruff format .` lint and format
- `python -m uv run backtester --help` lists the pipeline commands
