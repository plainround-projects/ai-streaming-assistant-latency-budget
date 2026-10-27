# argparse (command-line programs)

## What it is

`argparse` is Python's standard library module for command-line programs. You declare the commands, sub-commands and options your program accepts; `argparse` reads `sys.argv` (the words typed after the program name), checks them, converts them, and prints help and error messages for you.

## Why this repository uses it

The program's commands (`streaming-assistant`) are how the Makefile and a person run each part of the lesson. `argparse` gives them sub-commands, options, validation and `--help` from the standard library, with no extra dependency.

## Where it appears

| File | What it does with argparse (command-line programs) |
| --- | --- |
| `src/streaming_assistant/interfaces/cli.py` | the parser and `main` |

## How it works underneath

When you run `refund-agent gate --weaken ownership`, the operating system starts Python and hands the program the list of words `["gate", "--weaken", "ownership"]`. `ArgumentParser` builds a description of what is allowed. `add_subparsers(dest="command", required=True)` creates *sub-commands* (like `git commit`): the first word chooses one. `add_argument("--runs", type=int, default=3)` adds an *option* with a name, a converter and a default. `parse_args(argv)` returns an object whose attributes hold the values (`arguments.command`, `arguments.runs`); a bad value prints a usage message and exits with code 2.

The program's `main(argv=None)` function takes the list as an optional argument, so tests call `main(["gate"])` directly without starting a new process, and returns an integer that becomes the *exit code*: 0 for success. At the bottom, `raise SystemExit(main())` turns the return value into the process's exit code. Installing the package creates a console command that calls `main`.

## Walkthrough of this repository's use

The program is `streaming-assistant` (created from `[project.scripts]` in `pyproject.toml`). First, the function that declares what the command line accepts:

From `src/streaming_assistant/interfaces/cli.py`:

```python
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="streaming-assistant", description="A streaming support assistant inside a latency budget."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("serve", "start the HTTP server"),
        ("db", "rebuild the SQLite database from sql/001_schema.sql and sql/002_seed.sql"),
        ("evaluate", "the 200 sample questions: pauses, false pauses, citations"),
        ("stop-test", "close the stream after 3 tokens and look at the upstream call"),
        ("verify-audit", "check the hash chain of the audit log"),
        ("tamper-demo", "edit and delete entries in a copy of the chain and verify"),
    ):
        commands.add_parser(name, help=text)
    trace = commands.add_parser("trace", help="one request's stage times, cold and warm")
    trace.add_argument(
        "--question",
        default="A question about shipping times: standard delivery takes three to five business days after dispatch?",
    )
    load = commands.add_parser("load-test", help="replay the questions at a steady rate against four configurations")
    load.add_argument("--rps", type=float, default=5.0)
    load.add_argument("--duration", type=float, default=40.0)
    replay = commands.add_parser("replay", help="what the customer saw and who approved it, from the audit log")
    replay.add_argument("run_id")
    return parser
```

- `def _parser() -> argparse.ArgumentParser:`: A function that builds the parser. `-> argparse.ArgumentParser` says it returns one.
- `parser = argparse.ArgumentParser(`: Creates the parser; its name and description follow.
- `prog="streaming-assistant", description="A streaming support assistant inside a latency budget."`: `prog` (`streaming-assistant`) is the name shown in usage messages; `description` is the text under `--help`.
- `commands = parser.add_subparsers(dest="command", required=True)`: Makes room for sub-commands. `dest="command"` stores the chosen one in `arguments.command`; `required=True` means one must be chosen.
- `for name, text in (`: Starts a loop over a tuple of (name, help text) pairs, so several similar sub-commands are declared with one `add_parser` call.
- `("serve", "start the HTTP server"),`: One pair: the sub-command `serve` with its help text.
- `("db", "rebuild the SQLite database from sql/001_schema.sql and sql/002_seed.sql"),`: One pair: the sub-command `db` with its help text.
- `("evaluate", "the 200 sample questions: pauses, false pauses, citations"),`: One pair: the sub-command `evaluate` with its help text.
- `("stop-test", "close the stream after 3 tokens and look at the upstream call"),`: One pair: the sub-command `stop-test` with its help text.
- `("verify-audit", "check the hash chain of the audit log"),`: One pair: the sub-command `verify-audit` with its help text.
- `("tamper-demo", "edit and delete entries in a copy of the chain and verify"),`: One pair: the sub-command `tamper-demo` with its help text.
- `commands.add_parser(name, help=text)`: Declares one sub-command per pair.
- `trace = commands.add_parser("trace", help="one request's stage times, cold and warm")`: Declares the sub-command `trace` and keeps its parser in `trace` so options can be added. Help text: one request's stage times, cold and warm
- `trace.add_argument(`: Adds an option to `trace`; the details follow on the next lines.
- `"--question",`: The name of the sub-command (`--question`); the help text follows.
- `default="A question about shipping times: standard delivery takes three to five business days after dispatch?",`: More arguments of the call above: they set the value type, the default, the allowed choices or the help text.
- `load = commands.add_parser("load-test", help="replay the questions at a steady rate against four configurations")`: Declares the sub-command `load-test` and keeps its parser in `load` so options can be added. Help text: replay the questions at a steady rate against four configurations
- `load.add_argument("--rps", type=float, default=5.0)`: Adds the option `--rps` to `load`. `type=float` converts the text to a decimal number. `default=5.0` is the value when the option is left out.
- `load.add_argument("--duration", type=float, default=40.0)`: Adds the option `--duration` to `load`. `type=float` converts the text to a decimal number. `default=40.0` is the value when the option is left out.
- `replay = commands.add_parser("replay", help="what the customer saw and who approved it, from the audit log")`: Declares the sub-command `replay` and keeps its parser in `replay` so options can be added. Help text: what the customer saw and who approved it, from the audit log
- `replay.add_argument("run_id")`: Adds the positional argument `run_id` to `replay`: a value typed after the sub-command, with no dashes.
- `return parser`: Hands the finished parser back.

Then the start of `main`, which every sub-command passes through:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand; returns the process exit code."""
    arguments = _parser().parse_args(argv)
    try:
        settings = Settings.from_environ(os.environ)
    except ConfigurationError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2
    configure_logging(settings.log_level)
    try:
```

- `def main(argv: Sequence[str] | None = None) -> int:`: The program's entry. `argv` is the list of arguments; `None` means 'use the real command line'. It returns the exit code.
- `"""Run one subcommand; returns the process exit code."""`: The docstring.
- `arguments = _parser().parse_args(argv)`: Builds the parser and parses the words. On a usage error argparse prints a message and exits with code 2 here.
- `try:`: Starts a block whose errors are handled below.
- `settings = Settings.from_environ(os.environ)`: Reads and validates every environment variable once (see `dotenv.md`).
- `except ConfigurationError as error:`: A bad setting.
- `print(f"configuration error: {error}", file=sys.stderr)`: Prints the message on standard error, where error messages belong.
- `return 2`: Exit code 2: the same code argparse uses for bad usage.
- `configure_logging(settings.log_level)`: Turns logging on at the chosen level (see `logging.md`).
- `try:`: Starts a block whose errors are handled below.

After that, `main` chooses what to run by the sub-command. Each branch calls one helper; this table is read from the file:

| Sub-command | Help text | Helper `main` calls | What the helper's docstring says |
| --- | --- | --- | --- |
| `trace` | one request's stage times, cold and warm | (handled inline in `main`) |  |
| `load-test` | replay the questions at a steady rate against four configurations | (handled inline in `main`) |  |
| `replay` | what the customer saw and who approved it, from the audit log | (handled inline in `main`) |  |
| `serve` | start the HTTP server | (handled inline in `main`) |  |
| `db` | rebuild the SQLite database from sql/001_schema.sql and sql/002_seed.sql | (handled inline in `main`) |  |
| `evaluate` | the 200 sample questions: pauses, false pauses, citations | (handled inline in `main`) |  |
| `stop-test` | close the stream after 3 tokens and look at the upstream call | (handled inline in `main`) |  |
| `verify-audit` | check the hash chain of the audit log | (handled inline in `main`) |  |
| `tamper-demo` | edit and delete entries in a copy of the chain and verify | `_tamper` | Run one subcommand; returns the process exit code. |

And the last two lines of the file:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

- `if __name__ == "__main__":`: True only when the file is run directly, not when it is imported.
- `raise SystemExit(main())`: Runs `main` and ends the process with the number it returned as the exit code.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/streaming-assistant --help
```

Prints the usage line and the list of sub-commands with their help text.

```bash
.venv/bin/streaming-assistant not-a-command; echo $?
```

Prints a usage error and then `2`, argparse's exit code for bad usage.

## Mistakes people make

- Reading `sys.argv` by hand; `argparse` gives validation and `--help` for free.
- Calling `sys.exit` deep inside the code. The functions return codes to `main`, so tests can check them.
- Forgetting `required=True` on sub-parsers, which makes a bare command silently do nothing.
- Returning nothing instead of an exit code; shells and CI rely on a non-zero code to detect failure.
- Parsing numbers by hand. `type=int` and `type=float` report bad input clearly.

## Check yourself

1. What does `add_subparsers` do?
   *Answer:* Creates sub-commands, such as `program gate` and `program serve`.
2. What happens on an invalid option value?
   *Answer:* A usage message is printed and the program exits with code 2.
3. Why does `main` accept an optional list of arguments?
   *Answer:* So tests can call it directly with a list.
4. What is an exit code?
   *Answer:* A number a program returns to the shell: 0 for success, anything else for failure.
5. What does `type=int` do?
   *Answer:* Converts the text to an integer and rejects text that is not one.

## Further reading

- [argparse](https://docs.python.org/3.12/library/argparse.html)
- [argparse tutorial](https://docs.python.org/3.12/howto/argparse.html)
