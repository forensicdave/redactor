# Redactor

Redactor is a small Python command-line utility for replacing text in files using a configurable set of literal matches and regular expressions.

It is useful for anonymising, sanitising, renaming, or transforming text without manually editing each file.

For example:

```text
dundermifflin.com → corpo.com
Dunder Mifflin → Corpo
```

Redactor supports both exact string replacement and regular-expression-based replacement.

## Requirements

- Python 3.9 or later
- No external Python dependencies

Redactor uses only the Python standard library.

## Usage

```bash
python redactor.py INPUT CONFIG OUTPUT
```

For example:

```bash
python redactor.py input.txt replacements.json output.txt
```

Redactor reads `input.txt`, applies the replacement rules from `replacements.json`, and writes the transformed text to `output.txt`.

## Example

Given the following input file:

```text
Dunder Mifflin owns several brands of paper.

More information is available at dundermifflin.com.

Contact dwight@dundermifflin.com for more information.
```

And the following configuration:

```json
{
  "literal": {
    "dundermifflin.com": "corpo.com",
    "Dunder Mifflin": "Corpo"
  },

  "regex": [
    {
      "match": "\\b([A-Za-z0-9._%+-]+)@dundermifflin\\.com\\b",
      "replace": "\\1@corpo.com",
      "ignore_case": true
    }
  ]
}
```

Running:

```bash
python redactor.py input.txt replacements.json output.txt
```

produces:

```text
Corpo owns several brands of paper.

More information is available at corpo.com.

Contact dwight@corpo.com for more information.
```

Note that in this example the literal `dundermifflin.com` rule runs first and already rewrites the email address, so the regex rule only fires on mixed-case domains such as `dwight@dundermifflin.com`. See [Rule order](#rule-order).

## Configuration

The configuration file is JSON and can contain two types of rules:

- `literal` — exact string replacements
- `regex` — regular-expression replacements

A typical configuration looks like this:

```json
{
  "literal": {
    "dundermifflin.com": "corpo.com",
    "Dunder Mifflin": "Corpo"
  },

  "regex": [
    {
      "match": "\\bDunder\\s+Mifflin\\b",
      "replace": "Corpo",
      "ignore_case": true
    }
  ]
}
```

Both sections are optional.

## Literal replacements

Literal replacements perform exact, case-sensitive string matching.

For example:

```json
{
  "literal": {
    "Dunder Mifflin": "Corpo",
    "dundermifflin.com": "corpo.com"
  }
}
```

The text:

```text
Dunder Mifflin operates dundermifflin.com.
```

becomes:

```text
Corpo operates corpo.com.
```

Literal matching is case-sensitive, so:

```text
DUNDER MIFFLIN
```

would not match:

```json
"Dunder Mifflin": "Corpo"
```

Use a regular expression with `ignore_case` if case-insensitive matching is required.

Literal matching is also plain substring matching with no word boundaries, so:

```json
"AirstreamDelux": "Example Product"
```

would also change `AirstreamDeluxVans` into `Example Productvans`. Use a regular expression with `\b` if whole-word matching is required.

## Regular expression replacements

Regex rules are defined as an array:

```json
{
  "regex": [
    {
      "match": "\\bDunder\\s+Mifflin\\b",
      "replace": "Corpo",
      "ignore_case": true
    }
  ]
}
```

The `match` value is a Python regular expression.

The `replace` value uses Python `re.sub()` replacement syntax.

### Case-insensitive matching

```json
{
  "match": "\\bDunder Mifflin\\b",
  "replace": "Corpo",
  "ignore_case": true
}
```

This matches:

```text
Dunder Mifflin
DUNDER MIFFLIN
dunder mifflin
Dunder mifflin
```

and replaces each occurrence with:

```text
Corpo
```

### Matching flexible whitespace

The following rule:

```json
{
  "match": "\\bDunder\\s+Mifflin\\b",
  "replace": "Corpo",
  "ignore_case": true
}
```

matches strings such as:

```text
Dunder Mifflin
Dunder   Mifflin
Dunder        Mifflin
```

### Capture groups

Regex capture groups can be reused in the replacement.

For example:

```json
{
  "match": "\\b([A-Za-z0-9._%+-]+)@dundermifflin\\.com\\b",
  "replace": "\\1@corpo.com",
  "ignore_case": true
}
```

This transforms:

```text
jim@dundermifflin.com
dwight.schrute@dundermifflin.com
```

into:

```text
jim@corpo.com
dwight.schrute@corpo.com
```

`\1` refers to the first capture group in the regular expression.

Because the configuration is JSON, backslashes must be escaped. For example:

```regex
\b
```

must be written as:

```json
"\\b"
```

## Regex options

Each regex rule supports the following optional settings.

### `ignore_case`

Enables case-insensitive matching.

```json
{
  "match": "Dunder Mifflin",
  "replace": "Corpo",
  "ignore_case": true
}
```

Equivalent to Python's:

```python
re.IGNORECASE
```

### `multiline`

Changes the behaviour of `^` and `$` so that they match the beginning and end of individual lines.

```json
{
  "match": "^Company:",
  "replace": "Organisation:",
  "multiline": true
}
```

Equivalent to:

```python
re.MULTILINE
```

### `dotall`

Allows `.` to match newline characters.

```json
{
  "match": "BEGIN.*END",
  "replace": "[REDACTED]",
  "dotall": true
}
```

Equivalent to:

```python
re.DOTALL
```

The options can be combined:

```json
{
  "match": "^Dunder.*Mifflin$",
  "replace": "Corpo",
  "ignore_case": true,
  "multiline": true,
  "dotall": true
}
```

## Rule order

Rule order matters.

Redactor processes replacements in the following order:

1. All literal replacements, in the order they appear in the configuration
2. Regex replacements, from top to bottom

For example:

```json
{
  "literal": {
    "Dunder Mifflin": "Corpo"
  },

  "regex": [
    {
      "match": "Corpo",
      "replace": "Example Corp"
    }
  ]
}
```

The input:

```text
Dunder Mifflin
```

would first become:

```text
Corpo
```

and then:

```text
Example Corp
```

Be careful when one rule may produce text that matches a later rule.

The reverse also applies: an earlier rule can consume text that a later rule was meant to handle. A literal `dundermifflin.com` rule will rewrite every email address ending in `@dundermifflin.com` before any regex rule sees it, so a regex email rule placed after it will report zero matches unless the input contains a case variant that the literal rule missed.

## Replacement statistics

By default, Redactor prints a summary showing how many times each rule matched.

For the input and configuration shown in the [Example](#example) section above, the output is:

```text
Input:  input.txt
Config: replacements.json
Output: output.txt

    2  [LITERAL] "dundermifflin.com" -> "corpo.com"
    1  [LITERAL] "Dunder Mifflin" -> "Corpo"
    0  [REGEX  ] "\b([A-Za-z0-9._%+-]+)@dundermifflin\.com\b" -> "\1@corpo.com"

Total replacements: 3
```

The literal `dundermifflin.com` rule matches twice (the website and the email address), which is why the regex rule reports zero matches.

This can be useful for confirming that the expected replacements occurred, and for spotting rules that never fire because an earlier rule consumed their input.

## Quiet mode

Use `-q` or `--quiet` to suppress replacement statistics:

```bash
python redactor.py input.txt replacements.json output.txt --quiet
```

or:

```bash
python redactor.py -q input.txt replacements.json output.txt
```

## Command-line help

Run:

```bash
python redactor.py --help
```

to display the available options:

```text
usage: redactor [-h] [-q] input config output

Replace literal strings and regex patterns in a text file using a JSON configuration.

positional arguments:
  input        Input text file
  config       JSON replacement configuration
  output       Output text file

options:
  -h, --help   show this help message and exit
  -q, --quiet  Do not print replacement statistics
```

On Python 3.9 the `options:` heading is shown as `optional arguments:` instead.

## Example configuration

A more complete configuration might look like this:

```json
{
  "literal": {
    "Dunder Mifflin": "Corpo",
    "dundermifflin.com": "corpo.com",
    "Paper": "Example Product"
  },

  "regex": [
    {
      "match": "\\bDunder\\s+Mifflin\\b",
      "replace": "Corpo",
      "ignore_case": true
    },
    {
      "match": "\\b([A-Za-z0-9._%+-]+)@dundermifflin\\.com\\b",
      "replace": "\\1@corpo.com",
      "ignore_case": true
    },
    {
      "match": "https?://(?:www\\.)?dundermifflin\\.com",
      "replace": "https://corpo.com",
      "ignore_case": true
    }
  ]
}
```

In this configuration the literal rules handle the common exact-case spellings, and the regex rules act as a safety net for variants the literal rules miss, such as `DUNDER MIFFLIN`, `Dunder  Mifflin` with extra spaces, or `alice@DunderMifflin.com`. Because `dundermifflin.com` is replaced literally first, the second and third regex rules only fire on such case variants.

## Error handling

Redactor exits with an error if:

- the input file does not exist
- the configuration file does not exist
- the configuration contains invalid JSON
- a regex is invalid
- a replacement rule is malformed
- an input or output file cannot be read or written

For example:

```text
redactor: error: Invalid regex in rule #2: missing ), unterminated subpattern
```

Regex patterns are validated before Redactor begins processing the input file.

## Encoding

Redactor reads and writes text using UTF-8.

Input files should therefore be UTF-8 encoded.

## Safety

Redactor writes its results to the output file specified on the command line.

For example:

```bash
python redactor.py original.txt replacements.json redacted.txt
```

This leaves `original.txt` unchanged and writes the transformed content to `redacted.txt`.

Redactor reads the whole input file into memory before writing anything, so using the same path for input and output works and replaces the file in place:

```bash
python redactor.py notes.txt replacements.json notes.txt
```

For important files, keeping the input and output paths separate is still recommended so the original can be compared against the result.

## Project structure

Redactor is a single script with no other files required. A suggested layout for a project that uses it might look like:

```text
redactor/
├── redactor.py
├── replacements.json
├── README.md
└── examples/
    ├── input.txt
    └── output.txt
```

## License

Use, modify, and distribute Redactor as appropriate for your project.

If publishing it publicly, consider adding an explicit license such as MIT, BSD-3-Clause, or Apache-2.0.
