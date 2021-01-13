# pyinputlanguage
Python utility that wraps a couple Carbon functions (`TISCreateInputSourceList` and `TISSelectInputSource`) to programmatically switch input languages on macOS.

Requires the PyObjC package.

## Usage

```python
from pyinputlanguage import macSwitchInputLanguage
macSwitchInputLanguage("com.apple.inputmethod.Kotoeri.Japanese")
```
