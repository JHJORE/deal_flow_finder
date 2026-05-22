# Tests

## Layout mirrors source

`backend/tests/unit/` mirrors `backend/src/deal_flow/` **folder-for-folder**. A test for `src/deal_flow/X/Y/Z.py` lives at `tests/unit/X/Y/test_Z.py`.

This means you can predict a file's tests from its path, and vice versa. If you add a new module, add the matching test folder.

## Test categories

| Folder | What goes here | I/O allowed? |
|---|---|---|
| `unit/` | Tests for one module in isolation. Use **fakes** for ports (in-memory `DealRepository`, etc.), never real adapters. | No |
| `integration/` | Tests that wire real adapters together (real DB, real HTTP cassette). Verify the seams between layers. | Yes, scoped |
| `e2e/` | Full-stack tests via FastAPI `TestClient` (or `httpx.AsyncClient`). Hit real routes, real composition root, fake out only the outermost externals. | Yes |

## Naming
- Test files: `test_<module>.py`
- Test functions: `test_<behavior>` (describe behavior, not implementation)

## Don't
- Don't mock what you don't own — wrap third-party deps behind a port and fake the port instead.
- Don't reach across layers in unit tests — if you need to touch infrastructure, you're writing an integration test.
- Don't share state between tests. Fixtures are per-test.
