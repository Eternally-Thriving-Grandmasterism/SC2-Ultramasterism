# Test fixtures

The two replays here are copied, unmodified, from the test suite of the
open-source [sc2reader](https://github.com/ggtracker/sc2reader) project
(commit `e10fc9344417d0aa9649e4ed8d6423e38f6af4c9`), where they are used
by `test_replays/test_replays.py`.

| File here | Source path in sc2reader | Game | SHA-256 of the decoded replay |
|---|---|---|---|
| `lotv_1v1_pvp.SC2Replay.b64` | `test_replays/4.10.0.75689/trophy_id_13.SC2Replay` | 1v1 PvP, Kairos Junction LE, 7:48, release 4.10.1 | `7a908f7050b36c8b295773504f222bbb14ed9e87eb01c690cea84a07b5f7e937` |
| `lotv_2v2.SC2Replay.b64` | `test_replays/5.0.15/95405_0.SC2Replay` | 2v2, 9:13, release 5.0.15 | `f2fdfc8325c830df4648c2cbeb0ffda59089c6b717c9507413bb649e6a5fde9f` |

The files are stored base64-encoded (text) and `tests/conftest.py`
decodes them to temporary `.SC2Replay` files when the tests run. To get
the original file back: `base64 -d lotv_1v1_pvp.SC2Replay.b64 > x.SC2Replay`.

## Licence

sc2reader is distributed under the MIT License
(Copyright (c) 2011-2013 Graylin Kim), which allows copying and
redistribution provided the copyright and permission notice are kept.
The notice from sc2reader's `LICENSE.txt` is reproduced below.
The replays are recordings of StarCraft II games (StarCraft II is a
trademark of Blizzard Entertainment) and contain the in-game names of
the players who played them; they are included only as test data.

```
The MIT License, http://www.opensource.org/licenses/mit-license.php

Copyright (c) 2011-2013 Graylin Kim

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
