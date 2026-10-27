# JSON Lines (.jsonl)

## What it is

JSON Lines is JSON with one rule added: a file holds one complete JSON value per line, usually an object. It suits data sets, because you can append a record, read a file line by line without loading it all, and diff it line by line.

## Why this repository uses it

The 200 sample questions, each with the page it should cite and whether it should pause, are cases. One per line means a diff shows exactly which question changed.

## Where it appears

| File | What it does with JSON Lines (.jsonl) |
| --- | --- |
| `data/questions.jsonl` | 200 questions: 180 to answer, 20 that must pause |
| `scripts/generate_data.py` | writes it and the help pages from one seed |

## How it works underneath

A `.jsonl` file looks like this: each line is a full JSON object; there is no outer `[ ]` and no commas between lines; blank lines are not records. A reader loops over the lines and calls `json.loads(line)` on each. A writer calls `json.dumps(record)` and writes it followed by a newline. Because each line stands alone, a damaged line spoils only that record, and `git diff` shows exactly which records changed.

## Walkthrough of this repository's use

### `data/questions.jsonl`

Each line: the question, the page and section it should cite (`expected_page`, `expected_anchor`) and `should_pause`. `make evaluate` runs all 200 and compares.

200 lines, one JSON object per line. Keys of the first record: `id`, `question`, `expected_page`, `expected_anchor`, `should_pause`. The first record, pretty-printed:

```json
{
  "id": "q-008",
  "question": "A question about changing an address: the delivery address can change until the?",
  "expected_page": "help-08",
  "expected_anchor": "the-delivery-address-can",
  "should_pause": false
}
```

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
wc -l data/questions.jsonl
```

`200`.

```bash
python3 -c "import json; rows=[json.loads(l) for l in open('data/questions.jsonl')]; print(sum(r['should_pause'] for r in rows))"
```

`20`.

```bash
make evaluate
```

Prints `paused_of_should: 20`, `paused_of_others: 0` and the citation counts.

## Mistakes people make

- Wrapping the lines in `[ ]` or adding commas; that is plain JSON.
- Pretty-printing a record across several lines; each record must be on one line.
- Forgetting the final newline.
- Loading a huge file at once when streaming line by line would do.
- Letting key order vary, which makes needless diffs. The writers here sort keys.

## Check yourself

1. What is in one line of a `.jsonl` file?
   *Answer:* One complete JSON value, usually an object.
2. Is `[ {...}, {...} ]` valid JSON Lines?
   *Answer:* No; that is one JSON array on one or more lines.
3. How do you read a `.jsonl` file in Python?
   *Answer:* Loop over its lines and call `json.loads` on each.
4. Why is the format good for evaluation cases?
   *Answer:* You can add or remove one case as one line, and a diff shows exactly that.
5. Can records contain nested objects?
   *Answer:* Yes. Only the line structure is special.

## Further reading

- [JSON Lines](https://jsonlines.org/)
- [Python json module](https://docs.python.org/3.12/library/json.html)
